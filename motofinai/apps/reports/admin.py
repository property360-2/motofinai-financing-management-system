from django.contrib import admin

from .models import ExportLog, ReportSchedule


@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    """Admin for scheduled reports."""

    list_display = [
        "id",
        "report_type",
        "frequency",
        "status",
        "last_generated",
        "next_generation",
    ]
    list_filter = ["report_type", "frequency", "status", "created_at"]
    search_fields = ["report_type", "recipient_emails"]
    readonly_fields = ["last_generated", "created_at", "updated_at"]
    fieldsets = (
        ("Report Configuration", {
            "fields": ("report_type", "frequency", "status"),
        }),
        ("Distribution", {
            "fields": ("recipient_emails", "include_charts"),
        }),
        ("Scheduling", {
            "fields": ("last_generated", "next_generation"),
        }),
        ("Metadata", {
            "fields": ("created_by", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(ExportLog)
class ExportLogAdmin(admin.ModelAdmin):
    """Admin for report exports."""

    list_display = [
        "id",
        "report_type",
        "export_format",
        "status",
        "row_count",
        "created_at",
    ]
    list_filter = ["report_type", "export_format", "status", "created_at"]
    search_fields = ["report_type", "file_path"]
    readonly_fields = ["created_at", "completed_at", "file_size", "error_message"]
    fieldsets = (
        ("Export Details", {
            "fields": ("report_type", "export_format", "status"),
        }),
        ("File Information", {
            "fields": ("file_path", "file_size", "row_count"),
        }),
        ("Filters Applied", {
            "fields": ("filters_applied",),
        }),
        ("Metadata", {
            "fields": ("exported_by", "created_at", "completed_at"),
        }),
        ("Error Information", {
            "fields": ("error_message",),
            "classes": ("collapse",),
        }),
    )
