# Motofinai Developer Guide

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 14+ (or SQLite for development)
- Node.js 18+ (for Tailwind CSS compilation)
- Git

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd motofinai-financing-management-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

8. **Open browser**
   ```
   http://localhost:8000
   ```

## Project Structure

```
motofinai/
├── apps/
│   ├── core/              # Shared utilities
│   │   ├── exceptions.py  # Custom exceptions
│   │   ├── validators.py  # Validation framework
│   │   ├── responses.py   # API responses
│   │   ├── middleware.py  # Exception handling
│   │   └── concurrency.py # Concurrency control
│   ├── users/             # User management
│   ├── loans/             # Loan management
│   ├── payments/          # Payment processing
│   ├── inventory/         # Inventory management
│   ├── audit/             # Audit logging
│   └── [other apps]/
├── templates/             # Django templates
├── static/                # CSS, JS, images
├── settings.py            # Django settings
├── urls.py                # URL routing
└── manage.py              # Django CLI
```

## Development Workflow

### 1. Creating a New Feature

**Step 1: Create models**
```python
# motofinai/apps/loans/models.py
from django.db import models
from motofinai.apps.core.concurrency import VersionedModel

class LoanApplication(VersionedModel):
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=[...])
```

**Step 2: Add validation**
```python
# motofinai/apps/core/validators.py
class LoanValidator:
    @staticmethod
    def validate_loan_amount(amount, min_amount=None, max_amount=None):
        result = ValidationResult()
        if amount <= 0:
            result.add_error("amount", "Amount must be positive")
        return result
```

**Step 3: Create forms**
```python
# motofinai/apps/loans/forms.py
from django import forms

class LoanApplicationForm(forms.ModelForm):
    class Meta:
        model = LoanApplication
        fields = ['amount', 'term_months', 'interest_rate']
```

**Step 4: Create views**
```python
# motofinai/apps/loans/views.py
from django.views import View
from motofinai.apps.core.responses import APIResponse
from motofinai.apps.core.exceptions import LoanValidationException

class LoanCreateView(View):
    def post(self, request):
        form = LoanApplicationForm(request.POST)
        if not form.is_valid():
            return FormResponseHelper.validation_response(form)

        try:
            loan = form.save()
            return APIResponse.created(data=loan.to_dict())
        except Exception as e:
            raise LoanValidationException(str(e))
```

**Step 5: Create templates**
```django
<!-- motofinai/templates/pages/loans/form.html -->
{% extends "layouts/base.html" %}

{% block content %}
<form method="post" class="space-y-8">
    {% csrf_token %}
    {% for field in form %}
        <!-- Render field with error handling -->
    {% endfor %}
    <button type="submit" class="bg-teal-600 text-white px-6 py-2 rounded">
        Submit
    </button>
</form>
{% endblock %}
```

**Step 6: Add URLs**
```python
# motofinai/apps/loans/urls.py
from django.urls import path
from .views import LoanCreateView

app_name = 'loans'
urlpatterns = [
    path('create/', LoanCreateView.as_view(), name='create'),
]
```

**Step 7: Register in admin**
```python
# motofinai/apps/loans/admin.py
from django.contrib import admin
from .models import LoanApplication

@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ['id', 'applicant', 'amount', 'status']
    list_filter = ['status', 'created_at']
    search_fields = ['applicant__username']
```

### 2. Using Exception Handling

```python
from motofinai.apps.core.exceptions import (
    LoanNotFound,
    LoanValidationException,
    ErrorDetail
)

# Simple exception
try:
    loan = Loan.objects.get(id=loan_id)
except Loan.DoesNotExist:
    raise LoanNotFound(f"Loan {loan_id} not found")

# With details
raise LoanValidationException(
    "Loan validation failed",
    details=[
        ErrorDetail(
            message="Amount exceeds maximum",
            code="amount_exceeded",
            field="amount",
            context={"max": 500000, "requested": 600000}
        )
    ]
)
```

### 3. Using Validation

```python
from motofinai.apps.core.validators import LoanValidator

# Validate loan amount
result = LoanValidator.validate_loan_amount(
    amount=50000,
    min_amount=10000,
    max_amount=500000
)

if not result:
    for field, message, context in result.errors:
        print(f"Error in {field}: {message}")

# Check validation result
if result.is_valid:
    # Process loan
    pass
```

### 4. Using Concurrency Control

```python
from motofinai.apps.core.concurrency import (
    TransactionConsistency,
    ConsistencyChecker
)

# Safe update with version checking
try:
    updated_loan = TransactionConsistency.safe_update_with_version(
        Loan,
        loan_id=123,
        current_version=5,
        update_fields={"status": "approved"}
    )
except ConcurrencyException:
    # Handle concurrent modification
    pass

# Check consistency
issues = ConsistencyChecker.check_loan_consistency(loan_id=123)
if issues["errors"]:
    # Handle errors
    pass
```

### 5. Using Audit Logging

```python
from motofinai.apps.audit.models import AuditLogEntry

# Log a business event
AuditLogEntry.log_business_event(
    action=AuditLogEntry.ActionType.LOAN_APPROVED,
    actor=request.user,
    description=f"Approved loan for {applicant.name}",
    object_model="LoanApplication",
    object_id=loan.id,
    details={
        "amount": str(loan.amount),
        "term": loan.term_months,
    }
)

# Log with object changes
AuditLogEntry.log_object_change(
    action=AuditLogEntry.ActionType.UPDATE,
    obj=loan,
    actor=request.user,
    old_values={"status": "pending"},
    new_values={"status": "approved"},
)
```

## Running Tests

### Unit Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test motofinai.apps.loans

# Run specific test class
python manage.py test motofinai.apps.loans.tests.LoanTestCase

# Run with verbosity
python manage.py test --verbosity=2

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Management Commands

```bash
# Check consistency
python manage.py check_consistency

# Quick check only
python manage.py check_consistency

# Check specific loan
python manage.py check_consistency --loan 123

# Full system check
python manage.py check_consistency --all

# Verbose output
python manage.py check_consistency --all --verbose
```

## Database Management

### Migrations

```bash
# Create migrations
python manage.py makemigrations

# Show migration status
python manage.py showmigrations

# Apply migrations
python manage.py migrate

# Migrate specific app
python manage.py migrate loans

# Rollback migration
python manage.py migrate loans 0001

# Create empty migration
python manage.py makemigrations --empty loans --name task_description
```

### Database Queries

```bash
# Django shell
python manage.py shell

# Execute SQL
python manage.py shell
>>> from django.db import connection
>>> with connection.cursor() as cursor:
>>>     cursor.execute("SELECT * FROM loans_loan LIMIT 1")
>>>     result = cursor.fetchone()
```

## Static Files

### Development

Tailwind CSS is configured with hot-reload:

```bash
# Watch for CSS changes
npm run dev

# Build once
npm run build
```

### Collection

```bash
# Collect static files
python manage.py collectstatic --noinput

# Clear collected files
rm -rf staticfiles/
```

## Common Tasks

### Add New App

```bash
python manage.py startapp myapp motofinai/apps/myapp
```

Then add to `INSTALLED_APPS` in `settings.py`

### Create Fixture

```bash
# Export data
python manage.py dumpdata myapp.Model > fixture.json

# Load fixture
python manage.py loaddata fixture.json
```

### Database Backup

```bash
# PostgreSQL backup
pg_dump database_name > backup.sql

# PostgreSQL restore
psql database_name < backup.sql

# SQLite backup
cp db.sqlite3 db.sqlite3.backup
```

## Environment Variables

Key settings in `.env`:

```
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/motofinai
DB_ENGINE=django.db.backends.postgresql

# Django
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@example.com

# AWS S3 (optional)
USE_S3=false
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
```

## Troubleshooting

### Import Errors

```
ModuleNotFoundError: No module named 'motofinai'
```

Make sure you're in the project root directory and have installed dependencies:
```bash
pip install -r requirements.txt
```

### Database Errors

```
django.db.utils.OperationalError: FATAL: database "motofinai" does not exist
```

Create the database:
```bash
createdb motofinai  # PostgreSQL
```

Or run with SQLite (automatically created):
```bash
DJANGO_DEBUG=true python manage.py runserver
```

### Migration Errors

```
django.db.migrations.exceptions.InconsistentMigrationHistory
```

Reset migrations (development only):
```bash
python manage.py migrate --fake-initial
```

### Static Files Not Loading

Clear cache and collect static files:
```bash
rm -rf staticfiles/
python manage.py collectstatic --noinput
```

## Code Style

### PEP 8 Compliance

```bash
# Check code style
flake8 motofinai/

# Auto-format code
black motofinai/
```

### Import Organization

```python
# 1. Standard library
import os
import sys

# 2. Third-party
from django.db import models
from rest_framework import serializers

# 3. Local
from motofinai.apps.core.exceptions import LoanNotFound
from motofinai.apps.loans.models import Loan
```

## Performance Tips

1. **Use select_related() and prefetch_related()**
   ```python
   loans = Loan.objects.select_related('applicant').prefetch_related('payments')
   ```

2. **Index frequently queried fields**
   ```python
   class Loan(models.Model):
       status = models.CharField(max_length=20, db_index=True)
   ```

3. **Use bulk operations**
   ```python
   Loan.objects.bulk_create(loans)
   Loan.objects.bulk_update(loans, fields=['status'])
   ```

4. **Cache expensive queries**
   ```python
   from django.views.decorators.cache import cache_page

   @cache_page(60 * 5)  # Cache for 5 minutes
   def expensive_view(request):
       pass
   ```

## Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## Getting Help

1. Check the [Enterprise Transformation Documentation](ENTERPRISE_TRANSFORMATION.md)
2. Review the [Exception Handling Guide](motofinai/apps/core/EXCEPTION_HANDLING.md)
3. Read the [Concurrency Control Guide](motofinai/apps/core/CONCURRENCY.md)
4. Check Django logs: `python manage.py runserver` output
5. Use Django shell for debugging: `python manage.py shell`

---

Happy coding! 🚀
