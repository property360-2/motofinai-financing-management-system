from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView

from .models import Archive
from .services import restore_record, ArchiveRestoreError


class ArchiveListView(LoginRequiredMixin, ListView):
    """List all archived records across all modules."""

    model = Archive
    template_name = "pages/archive/archive_list.html"
    context_object_name = "archives"
    paginate_by = 50
    required_roles = ("admin", "finance")

    def get_queryset(self):
        queryset = super().get_queryset().select_related("archived_by")

        # Filter by module if provided
        module = self.request.GET.get("module")
        if module:
            queryset = queryset.filter(module=module)

        # Filter by status if provided
        status = self.request.GET.get("status")
        if status in dict(Archive.Status.choices):
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        # Get module statistics
        module_stats = Archive.objects.values("module").annotate(
            count=Count("id")
        ).order_by("-count")

        context.update({
            "module_stats": module_stats,
            "status_choices": Archive.Status.choices,
            "user_can_restore": self.request.user.is_admin,
        })
        return context


class ArchiveDetailView(LoginRequiredMixin, DetailView):
    """View details of an archived record."""

    model = Archive
    template_name = "pages/archive/archive_detail.html"
    context_object_name = "archive"
    required_roles = ("admin", "finance")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["user_can_restore"] = self.request.user.is_admin
        context["breadcrumbs"] = [
            {"label": "Archive", "url": reverse("archive:list")},
            {"label": "Archives", "url": reverse("archive:list")},
            {"label": f"{self.object.module.title()} #{self.object.record_id}"},
        ]
        return context


class ArchiveRestoreView(LoginRequiredMixin, View):
    """Restore an archived record (Admin only)."""

    required_roles = ("admin",)

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        archive = get_object_or_404(Archive, pk=pk)

        if archive.status == Archive.Status.RESTORED:
            messages.warning(request, "This record has already been restored.")
            return redirect("archive:detail", pk=pk)

        try:
            # Attempt to restore the record from the data snapshot
            restored_instance = restore_record(
                module=archive.module,
                data_snapshot=archive.data_snapshot,
                original_record_id=archive.record_id,
            )

            # Mark the archive as restored
            archive.restore()

            messages.success(
                request,
                f"Successfully restored {archive.module} record #{archive.record_id}. "
                f"The record has been recreated in the {archive.module} module."
            )

        except ArchiveRestoreError as e:
            messages.error(
                request,
                f"Failed to restore record: {str(e)}"
            )

        return redirect("archive:detail", pk=pk)
