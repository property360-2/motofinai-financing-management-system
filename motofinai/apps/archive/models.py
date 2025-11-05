from django.conf import settings
from django.db import models


class Archive(models.Model):
    """Centralized archive for all modules with JSON snapshots."""

    class Status(models.TextChoices):
        ARCHIVED = "archived", "Archived"
        RESTORED = "restored", "Restored"

    module = models.CharField(
        max_length=100,
        help_text="Module name (e.g., 'motors', 'loan_applications', 'payments')",
    )
    record_id = models.IntegerField(help_text="ID of the archived record")
    archived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="archived_records",
    )
    reason = models.TextField(blank=True, help_text="Optional reason for archiving")
    data_snapshot = models.JSONField(help_text="Snapshot of the record at archive time")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ARCHIVED,
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="Date archived")
    restored_at = models.DateTimeField(null=True, blank=True, help_text="Date restored if applicable")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["module", "record_id"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.module} #{self.record_id} - {self.status}"

    @classmethod
    def archive_record(cls, *, module: str, record_id: int, data_snapshot: dict, archived_by, reason: str = ""):
        """Archive a record with its data snapshot."""
        return cls.objects.create(
            module=module,
            record_id=record_id,
            data_snapshot=data_snapshot,
            archived_by=archived_by,
            reason=reason,
            status=cls.Status.ARCHIVED,
        )

    def restore(self):
        """Mark the archive as restored."""
        from django.utils import timezone
        self.status = self.Status.RESTORED
        self.restored_at = timezone.now()
        self.save(update_fields=["status", "restored_at"])
