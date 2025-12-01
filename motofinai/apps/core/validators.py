"""
Enterprise validation framework for business rule enforcement.
Provides validators for loans, payments, inventory, and system-level validations.
"""

from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone


class ValidationError(Exception):
    """Custom validation error with context."""
    def __init__(self, message: str, code: str = "validation_error", context: Dict = None):
        self.message = message
        self.code = code
        self.context = context or {}
        super().__init__(self.message)


class ValidationResult:
    """Result of validation with errors and warnings."""
    def __init__(self):
        self.errors: List[Tuple[str, str, Dict]] = []  # (field, message, context)
        self.warnings: List[Tuple[str, str]] = []  # (field, message)
        self.is_valid = True

    def add_error(self, field: str, message: str, context: Dict = None):
        """Add validation error."""
        self.errors.append((field, message, context or {}))
        self.is_valid = False

    def add_warning(self, field: str, message: str):
        """Add validation warning."""
        self.warnings.append((field, message))

    def __bool__(self) -> bool:
        return self.is_valid


class LoanValidator:
    """Validators for loan applications and terms."""

    @staticmethod
    def validate_loan_amount(amount: Decimal, min_amount: Decimal = None, max_amount: Decimal = None) -> ValidationResult:
        """Validate loan amount against business rules."""
        result = ValidationResult()

        if amount is None or amount <= 0:
            result.add_error("amount", "Loan amount must be greater than zero", {"amount": amount})

        if min_amount and amount < min_amount:
            result.add_error("amount", f"Loan amount cannot be less than {min_amount}", {"min": min_amount, "actual": amount})

        if max_amount and amount > max_amount:
            result.add_error("amount", f"Loan amount cannot exceed {max_amount}", {"max": max_amount, "actual": amount})

        return result

    @staticmethod
    def validate_interest_rate(rate: Decimal) -> ValidationResult:
        """Validate interest rate."""
        result = ValidationResult()

        if rate is None or rate < 0:
            result.add_error("rate", "Interest rate must be non-negative", {"rate": rate})

        if rate > 100:
            result.add_warning("rate", "Interest rate exceeds 100% - please review")

        return result

    @staticmethod
    def validate_loan_term(months: int) -> ValidationResult:
        """Validate loan term in months."""
        result = ValidationResult()

        if months is None or months <= 0:
            result.add_error("term", "Loan term must be greater than zero months", {"months": months})

        if months > 360:  # 30 years
            result.add_warning("term", "Loan term exceeds 30 years - please review")

        if months < 1:
            result.add_error("term", "Loan term must be at least 1 month", {"months": months})

        return result

    @staticmethod
    def validate_approval_status_change(current_status: str, new_status: str) -> ValidationResult:
        """Validate loan status transition."""
        result = ValidationResult()

        # Define valid transitions
        valid_transitions = {
            "pending": ["approved", "rejected"],
            "approved": ["active", "rejected"],
            "active": ["completed", "defaulted"],
            "completed": [],
            "rejected": [],
            "defaulted": ["recovered"],
            "recovered": [],
        }

        if current_status not in valid_transitions:
            result.add_error("status", f"Unknown current status: {current_status}", {"status": current_status})
            return result

        if new_status not in valid_transitions.get(current_status, []):
            result.add_error("status", f"Cannot transition from {current_status} to {new_status}",
                           {"current": current_status, "new": new_status})

        return result


class PaymentValidator:
    """Validators for payment operations."""

    @staticmethod
    def validate_payment_amount(amount: Decimal, scheduled_amount: Decimal = None) -> ValidationResult:
        """Validate payment amount."""
        result = ValidationResult()

        if amount is None or amount <= 0:
            result.add_error("amount", "Payment amount must be greater than zero", {"amount": amount})

        if scheduled_amount:
            if amount > scheduled_amount * Decimal('1.1'):  # Allow 10% overpayment
                result.add_warning("amount",
                    f"Payment amount exceeds scheduled amount by more than 10%",
                    )

            if amount < scheduled_amount * Decimal('0.9'):  # Less than 90% of scheduled
                result.add_warning("amount",
                    f"Payment amount is less than 90% of scheduled amount")

        return result

    @staticmethod
    def validate_payment_date(payment_date: datetime, due_date: datetime = None) -> ValidationResult:
        """Validate payment date."""
        result = ValidationResult()

        if payment_date is None:
            result.add_error("date", "Payment date is required", {})

        if payment_date > timezone.now():
            result.add_error("date", "Payment date cannot be in the future", {"date": payment_date})

        if due_date and payment_date > due_date + timedelta(days=30):
            result.add_warning("date", f"Payment is more than 30 days late")

        return result

    @staticmethod
    def validate_payment_reversal(original_payment_date: datetime, reversal_days: int = 30) -> ValidationResult:
        """Validate if payment can be reversed."""
        result = ValidationResult()

        days_since_payment = (timezone.now() - original_payment_date).days

        if days_since_payment > reversal_days:
            result.add_error("reversal",
                f"Cannot reverse payment made {days_since_payment} days ago (limit: {reversal_days} days)",
                {"days_since": days_since_payment, "limit": reversal_days})

        return result


class InventoryValidator:
    """Validators for inventory operations."""

    @staticmethod
    def validate_vin_number(vin: str) -> ValidationResult:
        """Validate VIN number format."""
        result = ValidationResult()

        if not vin or len(vin) < 5:
            result.add_error("vin", "VIN number must be at least 5 characters", {"vin": vin})

        if len(vin) > 100:
            result.add_error("vin", "VIN number cannot exceed 100 characters", {"vin": vin})

        # Check for special characters
        if not all(c.isalnum() or c in ['-', '_', '.'] for c in vin):
            result.add_error("vin", "VIN number contains invalid characters", {"vin": vin})

        return result

    @staticmethod
    def validate_motor_quantity(quantity: int, available: int = None) -> ValidationResult:
        """Validate motor quantity."""
        result = ValidationResult()

        if quantity is None or quantity < 1:
            result.add_error("quantity", "Quantity must be at least 1", {"quantity": quantity})

        if available is not None and quantity > available:
            result.add_error("quantity",
                f"Insufficient quantity. Available: {available}, Requested: {quantity}",
                {"available": available, "requested": quantity})

        return result

    @staticmethod
    def validate_purchase_price(price: Decimal) -> ValidationResult:
        """Validate purchase price."""
        result = ValidationResult()

        if price is None or price <= 0:
            result.add_error("price", "Purchase price must be greater than zero", {"price": price})

        if price > Decimal('999999.99'):
            result.add_warning("price", "Purchase price seems unusually high - please review", {})

        return result


class UserValidator:
    """Validators for user-related operations."""

    @staticmethod
    def validate_email(email: str) -> ValidationResult:
        """Validate email format."""
        result = ValidationResult()

        if not email or '@' not in email:
            result.add_error("email", "Invalid email format", {"email": email})

        if len(email) > 254:
            result.add_error("email", "Email address is too long", {"email": email})

        return result

    @staticmethod
    def validate_phone(phone: str) -> ValidationResult:
        """Validate phone number."""
        result = ValidationResult()

        if not phone:
            result.add_error("phone", "Phone number is required", {})
            return result

        # Remove common formatting characters
        clean_phone = ''.join(c for c in phone if c.isdigit())

        if len(clean_phone) < 7:
            result.add_error("phone", "Phone number must have at least 7 digits", {"phone": phone})

        if len(clean_phone) > 15:
            result.add_error("phone", "Phone number is too long", {"phone": phone})

        return result

    @staticmethod
    def validate_password(password: str) -> ValidationResult:
        """Validate password strength."""
        result = ValidationResult()

        if len(password) < 8:
            result.add_error("password", "Password must be at least 8 characters", {})

        if not any(c.isupper() for c in password):
            result.add_error("password", "Password must contain at least one uppercase letter", {})

        if not any(c.isdigit() for c in password):
            result.add_error("password", "Password must contain at least one digit", {})

        if not any(c in '!@#$%^&*' for c in password):
            result.add_warning("password", "Password should contain special characters for better security")

        return result


class RiskValidator:
    """Validators for risk assessment."""

    @staticmethod
    def validate_risk_score(score: Decimal) -> ValidationResult:
        """Validate risk score (0-100)."""
        result = ValidationResult()

        if score is None or score < 0 or score > 100:
            result.add_error("score", "Risk score must be between 0 and 100", {"score": score})

        return result

    @staticmethod
    def validate_credit_score(score: int) -> ValidationResult:
        """Validate credit score (typically 300-850)."""
        result = ValidationResult()

        if score is None or score < 0:
            result.add_error("score", "Credit score must be non-negative", {"score": score})

        if score < 300:
            result.add_warning("score", "Credit score below 300 indicates poor credit history")

        if score > 850:
            result.add_warning("score", "Credit score exceeds typical maximum of 850")

        return result


class ValidatorRegistry:
    """Registry for all validators with centralized access."""

    def __init__(self):
        self.validators: Dict[str, Callable] = {
            # Loan validators
            "loan.amount": LoanValidator.validate_loan_amount,
            "loan.interest_rate": LoanValidator.validate_interest_rate,
            "loan.term": LoanValidator.validate_loan_term,
            "loan.status_change": LoanValidator.validate_approval_status_change,

            # Payment validators
            "payment.amount": PaymentValidator.validate_payment_amount,
            "payment.date": PaymentValidator.validate_payment_date,
            "payment.reversal": PaymentValidator.validate_payment_reversal,

            # Inventory validators
            "inventory.vin": InventoryValidator.validate_vin_number,
            "inventory.quantity": InventoryValidator.validate_motor_quantity,
            "inventory.price": InventoryValidator.validate_purchase_price,

            # User validators
            "user.email": UserValidator.validate_email,
            "user.phone": UserValidator.validate_phone,
            "user.password": UserValidator.validate_password,

            # Risk validators
            "risk.score": RiskValidator.validate_risk_score,
            "risk.credit_score": RiskValidator.validate_credit_score,
        }

    def validate(self, validator_key: str, *args, **kwargs) -> ValidationResult:
        """Execute validator by key."""
        if validator_key not in self.validators:
            raise ValueError(f"Unknown validator: {validator_key}")

        return self.validators[validator_key](*args, **kwargs)

    def register(self, key: str, validator: Callable):
        """Register custom validator."""
        self.validators[key] = validator

    def get_validator(self, key: str) -> Optional[Callable]:
        """Get validator by key."""
        return self.validators.get(key)


# Global validator registry instance
validator_registry = ValidatorRegistry()
