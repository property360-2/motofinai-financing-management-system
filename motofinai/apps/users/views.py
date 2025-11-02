from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy

from motofinai.apps.audit.models import AuditLogEntry

from .forms import LoginForm


class UserLoginView(LoginView):
    template_name = "pages/login.html"
    form_class = LoginForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("page_title", "Sign in")
        return context

    def get_success_url(self):
        return self.get_redirect_url() or reverse_lazy("home")


class UserLogoutView(LoginRequiredMixin, LogoutView):
    next_page = reverse_lazy("home")
    http_method_names = ["get", "post", "options", "head"]

    def get(self, request, *args, **kwargs):
        """Ensure GET requests trigger logout for header links."""

        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        actor = request.user if request.user.is_authenticated else None
        session_key = request.session.session_key
        ip_address = self._extract_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        response = super().post(request, *args, **kwargs)
        AuditLogEntry.record(
            actor=actor,
            action="auth.logout",
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"path": request.path, "session_key": session_key},
        )
        return response

    @staticmethod
    def _extract_ip(request):
        if not request:
            return None
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
