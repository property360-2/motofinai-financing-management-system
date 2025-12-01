"""Models for comprehensive reporting system."""

from django.conf import settings
from django.db import models
from django.utils import timezone


class ReportSchedule(models.Model):
    """Track scheduled report generation and delivery."""

    class Frequency(models.TextChoices):
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"
        QUARTERLY = "quarterly", "Quarterly"
        ANNUAL = "annual", "Annual"
        ONCE = "once", "One-time"

    class ReportType(models.TextChoices):
        APPLICANTS = "applicants", "All Applicants"
        APPROVED_LOANS = "approved_loans", "Approved Loans"
        RELEASED_MOTORS = "released_motors", "Released Motors"
        ONGOING_LOANS = "ongoing_loans", "Ongoing Loans"
        MOTORCYCLE_STATUS = "motorcycle_status", "Motorcycle Status"
        PAYMENT_RECONCILIATION = "payment_reconciliation", "Payment Reconciliation"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        PAUSED = "paused", "Paused"

    report_type = models.CharField(
        max_length=50,
        choices=ReportType.choices,
        help_text="Type of report to generate.",
    )
    frequency = models.CharField(
        max_length=20,
        choices=Frequency.choices,
        default=Frequency.MONTHLY,
        help_text="How often to generate this report.",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        help_text="Whether this scheduled report is active.",
    )
    recipient_emails = models.TextField(
        help_text="Comma-separated list of email addresses to receive reports.",
    )
    include_charts = models.BooleanField(
        default=True,
        help_text="Include charts and visualizations in the report.",
    )
    last_generated = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this report was last generated.",
    )
    next_generation = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this report should be generated next.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="scheduled_reports_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.get_report_type_display()} - {self.get_frequency_display()}"

    def mark_generated(self) -> None:
        """Mark this report as just generated and update next generation time."""
        self.last_generated = timezone.now()
        # TODO: Calculate next_generation based on frequency
        self.save()


class ExportLog(models.Model):
    """Track report exports for audit trail."""

    class ExportFormat(models.TextChoices):
        PDF = "pdf", "PDF"
        CSV = "csv", "CSV"
        EXCEL = "excel", "Excel"
        JSON = "json", "JSON"

    class ExportStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    report_type = models.CharField(
        max_length=50,
        choices=ReportSchedule.ReportType.choices,
        help_text="Type of report exported.",
    )
    export_format = models.CharField(
        max_length=20,
        choices=ExportFormat.choices,
        help_text="Format the report was exported to.",
    )
    status = models.CharField(
        max_length=20,
        choices=ExportStatus.choices,
        default=ExportStatus.PENDING,
        help_text="Current status of the export.",
    )
    file_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to the exported file.",
    )
    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Size of exported file in bytes.",
    )
    row_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of data rows in the export.",
    )
    filters_applied = models.JSONField(
        default=dict,
        blank=True,
        help_text="Filters that were applied when exporting.",
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if export failed.",
    )
    exported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="report_exports",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the export was completed.",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.get_report_type_display()} ({self.get_export_format_display()}) - {self.get_status_display()}"

    def mark_completed(self, file_path: str = "", file_size: int = 0, row_count: int = 0) -> None:
        """Mark export as completed with file details."""
        self.status = self.ExportStatus.COMPLETED
        self.file_path = file_path
        self.file_size = file_size
        self.row_count = row_count
        self.completed_at = timezone.now()
        self.save()

    def mark_failed(self, error_message: str) -> None:
        """Mark export as failed with error message."""
        self.status = self.ExportStatus.FAILED
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save()
