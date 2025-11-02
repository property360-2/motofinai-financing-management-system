from django.conf import settings
from django.db import models


class AuditLogEntry(models.Model):
    """Persisted audit record for notable system and authentication events."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_entries",
    )
    action = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    metadata = models.JSONField(blank=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        actor_display = self.actor.get_username() if self.actor else "system"
        return f"{self.action} ({actor_display})"

    @classmethod
    def record(cls, *, action: str, actor=None, ip_address: str | None = None, user_agent: str = "", metadata=None):
        payload = metadata or {}
        return cls.objects.create(
            actor=actor,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent[:512],
            metadata=payload,
        )
