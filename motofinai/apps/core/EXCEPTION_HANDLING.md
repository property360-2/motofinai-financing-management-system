# Exception Handling System Documentation

The Motofinai application includes a comprehensive exception handling system designed to provide consistent error handling across all layers of the application.

## Overview

The exception handling system consists of:

1. **Custom Exceptions** (`exceptions.py`) - Domain-specific exception classes
2. **Global Middleware** (`middleware.py`) - Automatic exception catching and formatting
3. **Response Utilities** (`responses.py`) - Consistent API response formatting
4. **Validation Framework** (`validators.py`) - Business rule validation

## Custom Exceptions

### Exception Hierarchy

```
MotofinaiException (base exception)
├── ValidationException
│   ├── LoanValidationException
│   ├── PaymentValidationException
│   ├── InventoryValidationException
│   └── UserValidationException
├── LoanException
│   ├── LoanValidationException
│   ├── LoanStateException
│   ├── LoanNotFound
│   └── LoanAlreadyProcessed
├── PaymentException
│   ├── PaymentValidationException
│   ├── PaymentNotFound
│   ├── PaymentReversalException
│   └── InsufficientFundsException
├── InventoryException
│   ├── InventoryValidationException
│   ├── MotorNotFound
│   ├── InsufficientInventory
│   └── DuplicateVINException
├── UserException
│   ├── UserValidationException
│   ├── UserNotFound
│   ├── DuplicateEmailException
│   └── DuplicatePhoneException
├── AuthenticationException
├── AuthorizationException
├── RateLimitException
├── ConcurrencyException
├── RiskAssessmentException
├── LimitExceededException
├── POSException
├── ReportException
├── ExternalServiceException
├── DatabaseException
└── ConfigurationException
```

## Usage Examples

### Basic Exception Usage

```python
from motofinai.apps.core.exceptions import LoanNotFound, LoanValidationException

# Raise an exception
if not loan:
    raise LoanNotFound("Loan with ID 123 not found")

# With validation details
from motofinai.apps.core.exceptions import ErrorDetail, LoanValidationException

details = [
    ErrorDetail(
        message="Loan amount exceeds maximum allowed",
        code="amount_exceeded",
        field="amount",
        context={"max": 500000, "requested": 600000}
    )
]
raise LoanValidationException("Loan validation failed", details=details)
```

### In Views

```python
from django.views import View
from motofinai.apps.core.exceptions import PaymentNotFound, InsufficientFundsException
from motofinai.apps.core.responses import APIResponse
from motofinai.apps.payments.models import Payment

class PaymentDetailView(View):
    def get(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id)
            return APIResponse.success(data=payment.to_dict())
        except Payment.DoesNotExist:
            raise PaymentNotFound(f"Payment {payment_id} not found")
```

### In Forms

```python
from django import forms
from motofinai.apps.core.validators import LoanValidator
from motofinai.apps.core.exceptions import LoanValidationException

class LoanApplicationForm(forms.Form):
    amount = forms.DecimalField()
    interest_rate = forms.DecimalField()
    term_months = forms.IntegerField()

    def clean(self):
        cleaned_data = super().clean()

        # Validate loan amount
        amount_result = LoanValidator.validate_loan_amount(
            cleaned_data.get('amount'),
            min_amount=10000,
            max_amount=500000
        )
        if not amount_result:
            raise forms.ValidationError(
                "Loan validation failed: " + ", ".join(
                    [f"{e[0]}: {e[1]}" for e in amount_result.errors]
                )
            )

        return cleaned_data
```

### In Service Classes

```python
from motofinai.apps.core.exceptions import (
    LoanStateException,
    PaymentValidationException
)
from motofinai.apps.loans.models import LoanApplication

class LoanService:
    @staticmethod
    def approve_loan(loan_id):
        loan = LoanApplication.objects.get(id=loan_id)

        # Check status transition
        from motofinai.apps.core.validators import LoanValidator

        result = LoanValidator.validate_approval_status_change(
            loan.status,
            "approved"
        )

        if not result:
            raise LoanStateException(
                f"Cannot transition from {loan.status} to approved"
            )

        loan.status = "approved"
        loan.save()
        return loan
```

## Error Response Format

### API Responses

All API errors follow this consistent format:

```json
{
    "success": false,
    "error": {
        "code": "error_code",
        "message": "Human readable error message",
        "status_code": 400,
        "details": [
            {
                "message": "Specific error detail",
                "code": "detail_code",
                "field": "field_name",
                "context": {
                    "min": 100,
                    "max": 1000,
                    "actual": 50
                }
            }
        ]
    }
}
```

### Success Responses

```json
{
    "success": true,
    "message": "Operation completed successfully",
    "data": {
        "id": 123,
        "name": "John Doe"
    }
}
```

## Middleware Behavior

The `ExceptionHandlingMiddleware` automatically:

1. **Catches all exceptions** during request processing
2. **Formats responses** based on the request type:
   - API requests (Accept: application/json or /api/ paths) → JSON
   - Web requests → HTML error pages
3. **Logs exceptions** with full context (user, endpoint, error details)
4. **Returns appropriate HTTP status codes**
5. **In development mode**: Includes detailed error information
6. **In production mode**: Returns generic error messages

## Response Utilities

The `APIResponse` helper class provides convenient methods for creating responses:

```python
from motofinai.apps.core.responses import APIResponse
from django.http import JsonResponse

# Success responses
APIResponse.success(data=user_dict)  # 200
APIResponse.created(data=loan_dict)  # 201
APIResponse.paginated(
    data=loans,
    pagination={"page": 1, "total": 100}
)

# Error responses
APIResponse.not_found("User")  # 404
APIResponse.forbidden()  # 403
APIResponse.unauthorized()  # 401
APIResponse.validation_error(errors=error_list)  # 400
APIResponse.conflict("Resource already exists")  # 409
APIResponse.rate_limited()  # 429
```

## FormResponseHelper

For handling form validation errors:

```python
from motofinai.apps.core.responses import FormResponseHelper
from django.views import View

class MyFormView(View):
    def post(self, request):
        form = MyForm(request.POST)
        if not form.is_valid():
            # For API requests
            return FormResponseHelper.validation_response(
                form,
                custom_message="Form submission failed"
            )

        # Process form...
        return APIResponse.created(data=result)
```

## Best Practices

1. **Use Specific Exceptions**: Use domain-specific exceptions rather than generic Exception
   ```python
   # Good
   raise PaymentNotFound("Payment 123 not found")

   # Avoid
   raise Exception("Payment not found")
   ```

2. **Provide Context**: Include relevant context in exception details
   ```python
   raise LoanValidationException(
       "Loan amount invalid",
       details=[
           ErrorDetail(
               message=f"Amount {amount} exceeds maximum {max_amount}",
               code="amount_exceeded",
               field="amount",
               context={"requested": amount, "maximum": max_amount}
           )
       ]
   )
   ```

3. **Appropriate Status Codes**: Use the correct HTTP status code
   - 400: Validation errors, bad input
   - 401: Authentication required
   - 403: Access denied
   - 404: Resource not found
   - 409: Conflict (concurrent modification)
   - 429: Rate limit exceeded
   - 500: Server error

4. **Consistent Response Format**: Always use APIResponse helpers in views
   ```python
   # Good
   return APIResponse.success(data=data)

   # Avoid
   return JsonResponse({"data": data})
   ```

5. **Validate Early**: Use validators before database operations
   ```python
   # Validate first
   result = LoanValidator.validate_loan_amount(amount, min_amount, max_amount)
   if not result:
       raise LoanValidationException("Invalid amount", details=...)

   # Then save
   loan.save()
   ```

## Error Templates

Error pages are rendered from templates in `motofinai/templates/errors/`:

- `400.html` - Bad Request
- `403.html` - Forbidden
- `404.html` - Not Found
- `429.html` - Too Many Requests
- `500.html` - Server Error

Templates use the Tailwind CSS color scheme and can be customized as needed.

## Development Mode

In development (DEBUG=True), error responses include:

- Full exception messages
- Error details and context
- Stack traces (in JSON responses)
- Development-specific error pages

In production (DEBUG=False), error responses include:

- Generic error messages
- Status codes only
- No sensitive information
- Professional error pages

## Logging

All exceptions are logged with context including:

- Request method and path
- Authenticated user (or "anonymous")
- Exception type and message
- Full stack trace (for unexpected errors)
- Severity level (WARNING for 4xx, ERROR for 5xx)

Example log entry:
```
Exception in GET /api/loans/123 by user@example.com: LoanNotFound: Loan with ID 123 not found
```

## Integration with Business Logic

The validation framework works alongside the exception handling system:

1. **Validators** check business rules and return ValidationResult
2. **Views/Services** raise exceptions if validation fails
3. **Middleware** catches exceptions and formats responses
4. **User** receives formatted error message with details

Example flow:
```
User submits form
    ↓
Form/View validates using Validator
    ↓
ValidationResult has errors
    ↓
Raise ValidationException with details
    ↓
Middleware catches exception
    ↓
Format response (JSON or HTML)
    ↓
Return to user
```
