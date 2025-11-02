from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


class RoleRequiredMiddleware:
    """Apply role-based access control for views declaring required roles."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        required_roles = getattr(view_func, "required_roles", None)
        view_class = getattr(view_func, "view_class", None)
        if not required_roles and view_class is not None:
            required_roles = getattr(view_class, "required_roles", None)
        if not required_roles:
            return None
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if request.user.is_superuser:
            return None
        if request.user.role not in required_roles:
            raise PermissionDenied("You do not have permission to access this resource.")
        return None
