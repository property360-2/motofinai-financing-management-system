"""
Global middleware for exception handling and error response formatting.
Converts application exceptions to consistent JSON/HTML responses.
"""

import logging
import json
import traceback
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.template.response import TemplateResponse
from .exceptions import (
    MotofinaiException,
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    ConcurrencyException,
    DatabaseException,
    ExternalServiceException,
)

logger = logging.getLogger(__name__)


class ExceptionHandlingMiddleware:
    """
    Middleware to catch and format exceptions consistently.
    Converts exceptions to appropriate HTTP responses (JSON or HTML).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except Exception as exc:
            response = self.handle_exception(request, exc)

        return response

    def handle_exception(self, request, exc):
        """Handle exception and return appropriate response."""

        # Log the exception
        self.log_exception(request, exc)

        # Handle specific exception types
        if isinstance(exc, MotofinaiException):
            return self.handle_motofinai_exception(request, exc)
        elif isinstance(exc, DjangoValidationError):
            return self.handle_django_validation_error(request, exc)
        elif isinstance(exc, IntegrityError):
            return self.handle_integrity_error(request, exc)
        elif isinstance(exc, PermissionError):
            return self.handle_permission_error(request, exc)
        else:
            return self.handle_unexpected_error(request, exc)

    def handle_motofinai_exception(self, request, exc: MotofinaiException):
        """Handle MotofinaiException and format response."""
        if self.is_api_request(request):
            return JsonResponse(
                exc.to_response_dict(),
                status=exc.status_code,
            )
        else:
            return self.render_error_page(
                request,
                exc.status_code,
                exc.error_code,
                exc.message,
                exc.details,
            )

    def handle_django_validation_error(self, request, exc: DjangoValidationError):
        """Handle Django ValidationError."""
        status_code = 400
        error_code = "validation_error"
        message = str(exc)

        if self.is_api_request(request):
            return JsonResponse(
                {
                    "success": False,
                    "error": {
                        "code": error_code,
                        "message": message,
                        "status_code": status_code,
                    },
                },
                status=status_code,
            )
        else:
            return self.render_error_page(request, status_code, error_code, message)

    def handle_integrity_error(self, request, exc: IntegrityError):
        """Handle database integrity errors (e.g., unique constraint violations)."""
        status_code = 400
        error_code = "database_integrity_error"
        message = "A record with these details already exists"

        # Log the detailed error
        logger.warning(f"Integrity error: {str(exc)}")

        if self.is_api_request(request):
            return JsonResponse(
                {
                    "success": False,
                    "error": {
                        "code": error_code,
                        "message": message,
                        "status_code": status_code,
                    },
                },
                status=status_code,
            )
        else:
            return self.render_error_page(request, status_code, error_code, message)

    def handle_permission_error(self, request, exc: PermissionError):
        """Handle permission errors."""
        status_code = 403
        error_code = "permission_denied"
        message = "You do not have permission to perform this action"

        if self.is_api_request(request):
            return JsonResponse(
                {
                    "success": False,
                    "error": {
                        "code": error_code,
                        "message": message,
                        "status_code": status_code,
                    },
                },
                status=status_code,
            )
        else:
            return self.render_error_page(request, status_code, error_code, message)

    def handle_unexpected_error(self, request, exc: Exception):
        """Handle unexpected exceptions."""
        status_code = 500
        error_code = "internal_error"
        message = "An unexpected error occurred"

        # Log the full exception details
        logger.exception(f"Unexpected error: {str(exc)}", exc_info=exc)

        # In development, include the error details
        if self.is_development():
            message = f"{message}: {str(exc)}"

        if self.is_api_request(request):
            response_data = {
                "success": False,
                "error": {
                    "code": error_code,
                    "message": message,
                    "status_code": status_code,
                },
            }
            if self.is_development():
                response_data["error"]["details"] = traceback.format_exc()
            return JsonResponse(response_data, status=status_code)
        else:
            return self.render_error_page(request, status_code, error_code, message)

    def render_error_page(
        self,
        request,
        status_code: int,
        error_code: str,
        message: str,
        details=None,
    ):
        """Render an error page template."""
        context = {
            "status_code": status_code,
            "error_code": error_code,
            "message": message,
            "details": details or [],
            "is_development": self.is_development(),
        }

        # Try to render error template
        try:
            return TemplateResponse(
                request,
                f"errors/{status_code}.html",
                context,
                status=status_code,
            )
        except Exception:
            # Fallback to basic error response
            return HttpResponse(
                f"<h1>Error {status_code}: {error_code}</h1><p>{message}</p>",
                content_type="text/html",
                status=status_code,
            )

    def is_api_request(self, request) -> bool:
        """Check if request expects JSON response."""
        # Check Accept header
        accept = request.headers.get("Accept", "")
        if "application/json" in accept:
            return True

        # Check if path looks like API endpoint
        if request.path.startswith("/api/"):
            return True

        # Check content type
        if "json" in accept:
            return True

        return False

    def is_development(self) -> bool:
        """Check if running in development environment."""
        import os
        return os.environ.get("DJANGO_ENV") == "development" or (
            __import__("django").conf.settings.DEBUG
        )

    def log_exception(self, request, exc: Exception):
        """Log exception with request context."""
        user = getattr(request, "user", None)
        username = user.username if user and user.is_authenticated else "anonymous"

        log_message = (
            f"Exception in {request.method} {request.path} "
            f"by {username}: {type(exc).__name__}: {str(exc)}"
        )

        if isinstance(exc, MotofinaiException):
            if exc.status_code >= 500:
                logger.error(log_message)
            else:
                logger.warning(log_message)
        else:
            logger.exception(log_message, exc_info=exc)
