from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.utils.decorators import sync_and_async_middleware


@sync_and_async_middleware
class RoleRequiredMiddleware:
    """Apply role-based access control for views declaring required roles."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Call process_view to check roles before the view executes
        response = self.process_view(request)
        if response is not None:
            return response
        return self.get_response(request)

    def process_view(self, request):
        """Check role-based access control for the current request."""
        # Get the view function from the resolver
        resolver_match = request.resolver_match
        if not resolver_match:
            return None

        view_func = resolver_match.func

        # Try to get required_roles from the view function
        required_roles = getattr(view_func, "required_roles", None)

        # If not found, try to get it from the view class (for class-based views)
        view_class = getattr(view_func, "view_class", None)
        if not required_roles and view_class is not None:
            required_roles = getattr(view_class, "required_roles", None)

        # If no required_roles defined, allow access
        if not required_roles:
            return None

        # Require authentication
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())

        # Superusers always have access
        if request.user.is_superuser:
            return None

        # Check if user's role is in required roles
        if request.user.role not in required_roles:
            raise PermissionDenied("You do not have permission to access this resource.")

        return None
