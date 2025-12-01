from django.conf import settings
from django.db import models
from django.utils import timezone


class AuditLogEntry(models.Model):
    """Enterprise-grade audit record for system, authentication, and business events."""

    class ActionType(models.TextChoices):
        # Authentication events
        LOGIN = "login", "User Login"
        LOGOUT = "logout", "User Logout"
        LOGIN_FAILED = "login_failed", "Failed Login Attempt"
        PASSWORD_CHANGED = "password_changed", "Password Changed"
        ACCOUNT_LOCKED = "account_locked", "Account Locked"

        # CRUD operations
        CREATE = "create", "Record Created"
        UPDATE = "update", "Record Updated"
        DELETE = "delete", "Record Deleted"
        VIEW = "view", "Record Viewed"
        EXPORT = "export", "Data Exported"
        IMPORT = "import", "Data Imported"

        # Loan operations
        LOAN_CREATED = "loan_created", "Loan Application Created"
        LOAN_APPROVED = "loan_approved", "Loan Approved"
        LOAN_REJECTED = "loan_rejected", "Loan Rejected"
        LOAN_DISBURSED = "loan_disbursed", "Loan Disbursed"
        LOAN_COMPLETED = "loan_completed", "Loan Completed"

        # Payment operations
        PAYMENT_RECORDED = "payment_recorded", "Payment Recorded"
        PAYMENT_REVERSED = "payment_reversed", "Payment Reversed"

        # Inventory operations
        MOTOR_RECEIVED = "motor_received", "Motor Received"
        MOTOR_INSPECTED = "motor_inspected", "Motor Inspected"
        MOTOR_APPROVED = "motor_approved", "Motor Approved"

        # User management
        USER_CREATED = "user_created", "User Created"
        USER_MODIFIED = "user_modified", "User Modified"
        USER_DEACTIVATED = "user_deactivated", "User Deactivated"
        USER_ROLE_CHANGED = "user_role_changed", "User Role Changed"

        # System events
        SYSTEM_CONFIG_CHANGED = "system_config_changed", "System Configuration Changed"
        BACKUP_CREATED = "backup_created", "Backup Created"
        SECURITY_ALERT = "security_alert", "Security Alert"

    class Severity(models.TextChoices):
        INFO = "info", "Informational"
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"
        CRITICAL = "critical", "Critical"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_entries",
        help_text="User who performed the action"
    )
    action = models.CharField(
        max_length=50,
        choices=ActionType.choices,
        default=ActionType.VIEW,
        db_index=True,
        help_text="Type of action performed"
    )
    severity = models.CharField(
        max_length=10,
        choices=Severity.choices,
        default=Severity.INFO,
        help_text="Severity level of the audit event"
    )
    description = models.TextField(
        blank=True,
        help_text="Human-readable description of what happened"
    )

    # Request information
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    user_agent = models.CharField(max_length=512, blank=True)

    # Object information
    object_model = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="Model name of the object affected"
    )
    object_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="Primary key of the object affected"
    )

    # Additional data
    metadata = models.JSONField(
        blank=True,
        default=dict,
        help_text="Additional structured data about the event"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["actor", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
            models.Index(fields=["object_model", "object_id"]),
        ]
        verbose_name = "Audit Log Entry"
        verbose_name_plural = "Audit Log Entries"

    def __str__(self) -> str:
        actor_display = self.actor.get_username() if self.actor else "system"
        return f"{self.get_action_display()} - {actor_display}"

    @property
    def actor_display(self) -> str:
        """Display name for the actor."""
        if self.actor:
            return self.actor.get_full_name() or self.actor.get_username()
        return "System"

    @classmethod
    def record(
        cls,
        *,
        action: str,
        actor=None,
        description: str = "",
        severity: str = "info",
        ip_address: str | None = None,
        user_agent: str = "",
        object_model: str = "",
        object_id = None,
        metadata=None,
    ):
        """Create and save an audit log entry."""
        payload = metadata or {}
        return cls.objects.create(
            actor=actor,
            action=action,
            description=description,
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent[:512],
            object_model=object_model,
            object_id=str(object_id) if object_id else "",
            metadata=payload,
        )

    @classmethod
    def log_object_change(
        cls,
        action: str,
        obj,
        actor=None,
        description: str = "",
        old_values: dict | None = None,
        new_values: dict | None = None,
        ip_address: str | None = None,
        user_agent: str = "",
    ):
        """Log a change to a specific object with before/after values."""
        metadata = {
            "old_values": old_values or {},
            "new_values": new_values or {},
        }
        return cls.record(
            action=action,
            actor=actor,
            description=description,
            object_model=obj.__class__.__name__,
            object_id=obj.pk,
            metadata=metadata,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @classmethod
    def log_authentication(
        cls,
        action: str,
        actor=None,
        successful: bool = True,
        ip_address: str | None = None,
        user_agent: str = "",
        reason: str = "",
    ):
        """Log authentication events."""
        severity = "info" if successful else "warning"
        description = f"Authentication: {reason}" if reason else ""
        return cls.record(
            action=action,
            actor=actor,
            description=description,
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @classmethod
    def log_business_event(
        cls,
        action: str,
        actor=None,
        description: str = "",
        object_model: str = "",
        object_id = None,
        details: dict | None = None,
        ip_address: str | None = None,
        user_agent: str = "",
    ):
        """Log business-level events like loan approvals, payments, etc."""
        return cls.record(
            action=action,
            actor=actor,
            description=description,
            severity="info",
            object_model=object_model,
            object_id=object_id,
            metadata=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @classmethod
    def get_recent_activity(cls, user=None, days: int = 30):
        """Get recent audit activity."""
        from django.utils import timezone
        from datetime import timedelta

        cutoff_date = timezone.now() - timedelta(days=days)
        queryset = cls.objects.filter(created_at__gte=cutoff_date)

        if user:
            queryset = queryset.filter(actor=user)

        return queryset.order_by("-created_at")

    @classmethod
    def get_object_history(cls, object_model: str, object_id):
        """Get audit history for a specific object."""
        return cls.objects.filter(
            object_model=object_model,
            object_id=str(object_id),
        ).order_by("-created_at")
