"""
Custom exceptions for the Motofinai application.
Provides domain-specific exceptions with consistent error handling patterns.
"""

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class ErrorDetail:
    """Structured error detail with context information."""
    message: str
    code: str
    field: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        data = {
            "message": self.message,
            "code": self.code,
        }
        if self.field:
            data["field"] = self.field
        if self.context:
            data["context"] = self.context
        return data


class MotofinaiException(Exception):
    """Base exception for all application exceptions."""

    status_code = 500
    error_code = "internal_error"
    message = "An unexpected error occurred"
    details: List[ErrorDetail] = []

    def __init__(
        self,
        message: str = None,
        code: str = None,
        status_code: int = None,
        details: List[ErrorDetail] = None,
    ):
        self.message = message or self.message
        self.error_code = code or self.error_code
        self.status_code = status_code or self.status_code
        self.details = details or []
        super().__init__(self.message)

    def to_response_dict(self) -> Dict[str, Any]:
        """Convert exception to API response dictionary."""
        return {
            "success": False,
            "error": {
                "code": self.error_code,
                "message": self.message,
                "status_code": self.status_code,
                "details": [d.to_dict() for d in self.details],
            },
        }


class ValidationException(MotofinaiException):
    """Raised when validation fails."""

    status_code = 400
    error_code = "validation_error"
    message = "Validation failed"

    def __init__(
        self,
        message: str = "Validation failed",
        details: List[ErrorDetail] = None,
    ):
        super().__init__(message=message, code="validation_error", details=details or [])


class LoanException(MotofinaiException):
    """Base exception for loan operations."""

    error_code = "loan_error"
    message = "Loan operation failed"


class LoanValidationException(LoanException, ValidationException):
    """Raised when loan validation fails."""

    status_code = 400
    error_code = "loan_validation_error"
    message = "Loan validation failed"


class LoanStateException(LoanException):
    """Raised when attempting invalid loan status transition."""

    status_code = 400
    error_code = "loan_state_error"
    message = "Invalid loan state transition"


class LoanNotFound(LoanException):
    """Raised when loan is not found."""

    status_code = 404
    error_code = "loan_not_found"
    message = "Loan not found"


class LoanAlreadyProcessed(LoanException):
    """Raised when attempting to process already processed loan."""

    status_code = 400
    error_code = "loan_already_processed"
    message = "Loan has already been processed"


class PaymentException(MotofinaiException):
    """Base exception for payment operations."""

    error_code = "payment_error"
    message = "Payment operation failed"


class PaymentValidationException(PaymentException, ValidationException):
    """Raised when payment validation fails."""

    status_code = 400
    error_code = "payment_validation_error"
    message = "Payment validation failed"


class PaymentNotFound(PaymentException):
    """Raised when payment is not found."""

    status_code = 404
    error_code = "payment_not_found"
    message = "Payment not found"


class PaymentReversalException(PaymentException):
    """Raised when payment reversal is not allowed."""

    status_code = 400
    error_code = "payment_reversal_error"
    message = "Payment cannot be reversed"


class InsufficientFundsException(PaymentException):
    """Raised when there are insufficient funds."""

    status_code = 400
    error_code = "insufficient_funds"
    message = "Insufficient funds for this operation"


class InventoryException(MotofinaiException):
    """Base exception for inventory operations."""

    error_code = "inventory_error"
    message = "Inventory operation failed"


class InventoryValidationException(InventoryException, ValidationException):
    """Raised when inventory validation fails."""

    status_code = 400
    error_code = "inventory_validation_error"
    message = "Inventory validation failed"


class MotorNotFound(InventoryException):
    """Raised when motor is not found."""

    status_code = 404
    error_code = "motor_not_found"
    message = "Motor not found"


class InsufficientInventory(InventoryException):
    """Raised when insufficient inventory available."""

    status_code = 400
    error_code = "insufficient_inventory"
    message = "Insufficient inventory available"


class DuplicateVINException(InventoryException):
    """Raised when duplicate VIN is detected."""

    status_code = 400
    error_code = "duplicate_vin"
    message = "Motor with this VIN already exists"


class UserException(MotofinaiException):
    """Base exception for user operations."""

    error_code = "user_error"
    message = "User operation failed"


class UserValidationException(UserException, ValidationException):
    """Raised when user validation fails."""

    status_code = 400
    error_code = "user_validation_error"
    message = "User validation failed"


class UserNotFound(UserException):
    """Raised when user is not found."""

    status_code = 404
    error_code = "user_not_found"
    message = "User not found"


class DuplicateEmailException(UserException):
    """Raised when duplicate email is detected."""

    status_code = 400
    error_code = "duplicate_email"
    message = "User with this email already exists"


class DuplicatePhoneException(UserException):
    """Raised when duplicate phone is detected."""

    status_code = 400
    error_code = "duplicate_phone"
    message = "User with this phone already exists"


class AuthenticationException(MotofinaiException):
    """Raised when authentication fails."""

    status_code = 401
    error_code = "authentication_error"
    message = "Authentication failed"


class AuthorizationException(MotofinaiException):
    """Raised when user lacks required permissions."""

    status_code = 403
    error_code = "authorization_error"
    message = "You do not have permission to perform this action"


class RateLimitException(MotofinaiException):
    """Raised when rate limit is exceeded."""

    status_code = 429
    error_code = "rate_limit_exceeded"
    message = "Rate limit exceeded. Please try again later"


class ConcurrencyException(MotofinaiException):
    """Raised when concurrent modification is detected."""

    status_code = 409
    error_code = "concurrency_error"
    message = "Resource was modified by another user. Please refresh and try again"


class RiskAssessmentException(MotofinaiException):
    """Raised when risk assessment fails."""

    status_code = 400
    error_code = "risk_assessment_error"
    message = "Risk assessment failed"


class LimitExceededException(MotofinaiException):
    """Raised when operation exceeds configured limits."""

    status_code = 400
    error_code = "limit_exceeded"
    message = "Operation exceeds configured limits"


class POSException(MotofinaiException):
    """Base exception for POS operations."""

    error_code = "pos_error"
    message = "POS operation failed"


class InvalidTransactionException(POSException):
    """Raised when transaction is invalid."""

    status_code = 400
    error_code = "invalid_transaction"
    message = "Invalid transaction"


class TerminalNotAvailable(POSException):
    """Raised when POS terminal is not available."""

    status_code = 503
    error_code = "terminal_unavailable"
    message = "POS terminal is not available"


class ReportException(MotofinaiException):
    """Base exception for report operations."""

    error_code = "report_error"
    message = "Report generation failed"


class InvalidReportParameters(ReportException):
    """Raised when report parameters are invalid."""

    status_code = 400
    error_code = "invalid_report_parameters"
    message = "Invalid report parameters"


class ExternalServiceException(MotofinaiException):
    """Raised when external service fails."""

    status_code = 503
    error_code = "external_service_error"
    message = "External service is unavailable"


class DatabaseException(MotofinaiException):
    """Raised when database operation fails."""

    status_code = 500
    error_code = "database_error"
    message = "Database operation failed"


class ConfigurationException(MotofinaiException):
    """Raised when configuration is invalid."""

    status_code = 500
    error_code = "configuration_error"
    message = "Application configuration error"
