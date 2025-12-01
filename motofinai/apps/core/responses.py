"""
Standardized API response formatting utilities.
Provides consistent response structures for success and error cases.
"""

from typing import Dict, Any, List, Optional, Generic, TypeVar
from dataclasses import dataclass, asdict
from django.http import JsonResponse
from .exceptions import MotofinaiException, ErrorDetail

T = TypeVar("T")


@dataclass
class SuccessResponse(Generic[T]):
    """Standard success response structure."""

    success: bool = True
    data: Optional[T] = None
    message: str = "Operation completed successfully"
    meta: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "success": self.success,
            "message": self.message,
        }
        if self.data is not None:
            result["data"] = self.data
        if self.meta:
            result["meta"] = self.meta
        return result


@dataclass
class PaginatedResponse(Generic[T]):
    """Paginated response structure."""

    success: bool = True
    data: List[T] = None
    pagination: Dict[str, Any] = None
    message: str = "Data retrieved successfully"

    def __post_init__(self):
        if self.data is None:
            self.data = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "pagination": self.pagination or {},
        }


@dataclass
class ErrorResponse:
    """Standard error response structure."""

    success: bool = False
    error: Dict[str, Any] = None
    message: str = "An error occurred"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "message": self.message,
            "error": self.error or {},
        }


class APIResponse:
    """Helper class for creating API responses."""

    @staticmethod
    def success(
        data: Any = None,
        message: str = "Operation completed successfully",
        status_code: int = 200,
        meta: Optional[Dict[str, Any]] = None,
    ) -> JsonResponse:
        """Create a success response."""
        response = SuccessResponse(data=data, message=message, meta=meta)
        return JsonResponse(response.to_dict(), status=status_code)

    @staticmethod
    def created(
        data: Any = None,
        message: str = "Resource created successfully",
    ) -> JsonResponse:
        """Create a 201 Created response."""
        return APIResponse.success(data=data, message=message, status_code=201)

    @staticmethod
    def paginated(
        data: List[Any],
        pagination: Dict[str, Any],
        message: str = "Data retrieved successfully",
        status_code: int = 200,
    ) -> JsonResponse:
        """Create a paginated response."""
        response = PaginatedResponse(data=data, pagination=pagination, message=message)
        return JsonResponse(response.to_dict(), status=status_code)

    @staticmethod
    def error(
        message: str,
        code: str = "error",
        status_code: int = 400,
        error_details: Optional[Dict[str, Any]] = None,
    ) -> JsonResponse:
        """Create an error response."""
        error = {
            "code": code,
            "message": message,
            "status_code": status_code,
        }
        if error_details:
            error["details"] = error_details

        response = ErrorResponse(message=message, error=error)
        return JsonResponse(response.to_dict(), status=status_code)

    @staticmethod
    def exception(exc: MotofinaiException) -> JsonResponse:
        """Create response from MotofinaiException."""
        return JsonResponse(exc.to_response_dict(), status=exc.status_code)

    @staticmethod
    def validation_error(
        errors: List[ErrorDetail] = None,
        message: str = "Validation failed",
    ) -> JsonResponse:
        """Create a validation error response."""
        error_list = []
        if errors:
            for error in errors:
                error_list.append(error.to_dict())

        error_data = {
            "code": "validation_error",
            "message": message,
            "status_code": 400,
            "details": error_list,
        }

        response = ErrorResponse(message=message, error=error_data)
        return JsonResponse(response.to_dict(), status=400)

    @staticmethod
    def not_found(resource: str) -> JsonResponse:
        """Create a 404 Not Found response."""
        message = f"{resource} not found"
        return APIResponse.error(
            message=message,
            code="not_found",
            status_code=404,
        )

    @staticmethod
    def unauthorized() -> JsonResponse:
        """Create a 401 Unauthorized response."""
        return APIResponse.error(
            message="Authentication required",
            code="unauthorized",
            status_code=401,
        )

    @staticmethod
    def forbidden() -> JsonResponse:
        """Create a 403 Forbidden response."""
        return APIResponse.error(
            message="You do not have permission to perform this action",
            code="forbidden",
            status_code=403,
        )

    @staticmethod
    def conflict(message: str) -> JsonResponse:
        """Create a 409 Conflict response."""
        return APIResponse.error(
            message=message,
            code="conflict",
            status_code=409,
        )

    @staticmethod
    def rate_limited() -> JsonResponse:
        """Create a 429 Rate Limited response."""
        return APIResponse.error(
            message="Rate limit exceeded. Please try again later",
            code="rate_limit_exceeded",
            status_code=429,
        )


class FormResponseHelper:
    """Helper for handling form responses in views."""

    @staticmethod
    def form_errors(form) -> Dict[str, List[str]]:
        """Extract form errors into a dictionary."""
        errors = {}
        for field, error_list in form.errors.items():
            errors[field] = list(error_list)
        return errors

    @staticmethod
    def form_error_details(form) -> List[ErrorDetail]:
        """Convert form errors to ErrorDetail objects."""
        details = []
        for field, error_list in form.errors.items():
            for error in error_list:
                details.append(
                    ErrorDetail(
                        message=str(error),
                        code="form_validation_error",
                        field=field,
                    )
                )
        return details

    @staticmethod
    def validation_response(form, custom_message: str = None) -> JsonResponse:
        """Create validation error response from form errors."""
        message = custom_message or "Form validation failed"
        errors = FormResponseHelper.form_error_details(form)
        return APIResponse.validation_error(errors=errors, message=message)


class AsyncResponseHelper:
    """Helper for async operation responses."""

    @staticmethod
    def async_job_response(job_id: str, status: str = "queued") -> Dict[str, Any]:
        """Create response for async job."""
        return {
            "job_id": job_id,
            "status": status,
            "message": f"Job {job_id} is {status}",
        }

    @staticmethod
    def async_job_status(job_id: str, status: str, progress: int = None) -> Dict[str, Any]:
        """Create status response for async job."""
        response = {
            "job_id": job_id,
            "status": status,
            "progress": progress or 0,
        }
        return response


class BulkResponseHelper:
    """Helper for bulk operation responses."""

    @staticmethod
    def bulk_operation_response(
        successful: int,
        failed: int,
        errors: List[Dict[str, Any]] = None,
        message: str = "Bulk operation completed",
    ) -> Dict[str, Any]:
        """Create response for bulk operations."""
        return {
            "success": failed == 0,
            "message": message,
            "summary": {
                "total": successful + failed,
                "successful": successful,
                "failed": failed,
                "success_rate": f"{(successful / (successful + failed) * 100):.1f}%" if (successful + failed) > 0 else "0%",
            },
            "errors": errors or [],
        }
