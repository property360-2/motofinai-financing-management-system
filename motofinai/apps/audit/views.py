from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import DetailView, ListView

from .models import AuditLogEntry


class AuditLogListView(LoginRequiredMixin, ListView):
    """List all audit log entries with filtering."""

    model = AuditLogEntry
    template_name = "pages/audit/audit_log_list.html"
    context_object_name = "logs"
    paginate_by = 50
    required_roles = ("admin", "finance")

    def get_queryset(self):
        queryset = super().get_queryset().select_related("actor")

        # Search by action or username
        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(action__icontains=query) |
                Q(actor__username__icontains=query) |
                Q(actor__email__icontains=query)
            )

        # Filter by action
        action = self.request.GET.get("action")
        if action:
            queryset = queryset.filter(action__icontains=action)

        # Filter by user
        user_id = self.request.GET.get("user")
        if user_id:
            queryset = queryset.filter(actor_id=user_id)

        return queryset

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        # Get users for filtering
        from django.contrib.auth import get_user_model
        User = get_user_model()

        context.update({
            "users": User.objects.filter(is_active=True).order_by("username"),
            "search_query": self.request.GET.get("q", ""),
        })
        return context


class AuditLogDetailView(LoginRequiredMixin, DetailView):
    """View details of a specific audit log entry."""

    model = AuditLogEntry
    template_name = "pages/audit/audit_log_detail.html"
    context_object_name = "log"
    required_roles = ("admin", "finance")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Audit Logs", "url": reverse("audit:list")},
            {"label": "Logs", "url": reverse("audit:list")},
            {"label": f"{self.object.action}"},
        ]
        return context
