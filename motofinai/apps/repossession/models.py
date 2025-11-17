from __future__ import annotations

from decimal import Decimal

from django.apps import apps
from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class RepossessionCaseQuerySet(models.QuerySet):
    def open(self) -> "RepossessionCaseQuerySet":
        closed_statuses = [
            RepossessionCase.Status.RECOVERED,
            RepossessionCase.Status.CLOSED,
        ]
        return self.exclude(status__in=closed_statuses)


class RepossessionCaseManager(models.Manager["RepossessionCase"]):
    def get_queryset(self) -> RepossessionCaseQuerySet:
        return RepossessionCaseQuerySet(self.model, using=self._db)

    def open(self) -> RepossessionCaseQuerySet:
        return self.get_queryset().open()

    def sync_for_loan(
        self,
        loan_application,
    ) -> "RepossessionCase | None":
        """Ensure repossession tracking reflects the loan's overdue state."""

        PaymentSchedule = apps.get_model("loans", "PaymentSchedule")
        overdue_qs = loan_application.payment_schedules.filter(
            status=PaymentSchedule.Status.OVERDUE
        )
        overdue_count = overdue_qs.count()
        total_overdue_amount = overdue_qs.aggregate(
            total=Sum("total_amount")
        )["total"] or Decimal("0.00")
        total_overdue_amount = total_overdue_amount.quantize(Decimal("0.01"))

        if overdue_count == 0:
            try:
                case = loan_application.repossession_case
            except RepossessionCase.DoesNotExist:
                return None
            if case.status not in (
                RepossessionCase.Status.RECOVERED,
                RepossessionCase.Status.CLOSED,
            ):
                case.mark_recovered()
            return case

        case, created = self.get_or_create(
            loan_application=loan_application,
            defaults={"status": RepossessionCase.Status.WARNING},
        )
        case.update_from_metrics(
            overdue_installments=overdue_count,
            total_overdue_amount=total_overdue_amount,
            created=created,
        )
        return case


class RepossessionCase(models.Model):
    """Track overdue loans moving through repossession workflows."""

    class Status(models.TextChoices):
        WARNING = "warning", "Warning"
        ACTIVE = "active", "Active case"
        REMINDER = "reminder", "Reminder sent"
        RECOVERED = "recovered", "Recovered"
        CLOSED = "closed", "Closed"

    loan_application = models.OneToOneField(
        "loans.LoanApplication",
        on_delete=models.CASCADE,
        related_name="repossession_case",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WARNING,
    )
    overdue_installments = models.PositiveIntegerField(default=0)
    total_overdue_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    last_reminder_sent_at = models.DateTimeField(blank=True, null=True)
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(blank=True, null=True)

    objects = RepossessionCaseManager()

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"Repossession case for loan {self.loan_application_id}"

    @property
    def is_open(self) -> bool:
        return self.status not in {self.Status.RECOVERED, self.Status.CLOSED}

    def log_event(
        self,
        description: str,
        *,
        event_type: "RepossessionEvent.EventType" | str,
        user=None,
    ) -> None:
        self.events.create(
            event_type=event_type,
            description=description,
            created_by=user,
        )

    def log_status_change(self, previous_status: str, *, user=None) -> None:
        try:
            previous_display = self.Status(previous_status).label
        except ValueError:
            previous_display = previous_status
        current_display = self.get_status_display()
        self.log_event(
            f"Status changed from {previous_display} to {current_display}.",
            event_type=RepossessionEvent.EventType.STATUS,
            user=user,
        )

    def update_from_metrics(
        self,
        *,
        overdue_installments: int,
        total_overdue_amount: Decimal,
        created: bool = False,
    ) -> None:
        previous_status = self.status
        updates: list[str] = []
        if self.overdue_installments != overdue_installments:
            self.overdue_installments = overdue_installments
            updates.append("overdue_installments")
        amount = total_overdue_amount.quantize(Decimal("0.01"))
        if self.total_overdue_amount != amount:
            self.total_overdue_amount = amount
            updates.append("total_overdue_amount")
        if (
            overdue_installments >= 2
            and self.status == self.Status.WARNING
        ):
            self.status = self.Status.ACTIVE
            updates.append("status")
        if updates:
            self.save(update_fields=[*updates, "updated_at"])
        if created:
            self.log_event(
                f"Case opened with {overdue_installments} overdue installment"
                f"{'s' if overdue_installments != 1 else ''} totaling ₱{self.total_overdue_amount}.",
                event_type=RepossessionEvent.EventType.SYSTEM,
            )
        elif updates:
            self.log_event(
                f"Metrics updated to {overdue_installments} overdue installment"
                f"{'s' if overdue_installments != 1 else ''} totaling ₱{self.total_overdue_amount}.",
                event_type=RepossessionEvent.EventType.SYSTEM,
            )
        if self.status != previous_status:
            self.log_status_change(previous_status)

    def record_reminder(self, message: str, *, user=None) -> None:
        previous_status = self.status
        self.status = self.Status.REMINDER
        self.last_reminder_sent_at = timezone.now()
        self.save(update_fields=["status", "last_reminder_sent_at", "updated_at"])
        if previous_status != self.status:
            self.log_status_change(previous_status, user=user)
        self.log_event(
            message or "Reminder sent to customer regarding overdue account.",
            event_type=RepossessionEvent.EventType.REMINDER,
            user=user,
        )

    def mark_recovered(self, *, user=None) -> None:
        if self.status == self.Status.CLOSED:
            return
        previous_status = self.status
        self.status = self.Status.RECOVERED
        self.overdue_installments = 0
        self.total_overdue_amount = Decimal("0.00")
        timestamp = timezone.now()
        self.closed_at = timestamp
        self.save(
            update_fields=[
                "status",
                "overdue_installments",
                "total_overdue_amount",
                "closed_at",
                "updated_at",
            ]
        )
        # Restore stock when loan is recovered
        motor = self.loan_application.motor
        if motor and motor.stock:
            try:
                motor.stock.increase_available(amount=1)
            except ValueError:
                # Log but don't fail if stock restoration has issues
                self.log_event(
                    "Warning: Could not restore stock after recovery.",
                    event_type=RepossessionEvent.EventType.SYSTEM,
                    user=user,
                )
        if previous_status != self.status:
            self.log_status_change(previous_status, user=user)
        self.log_event(
            "Loan brought current. Case marked as recovered.",
            event_type=RepossessionEvent.EventType.SYSTEM,
            user=user,
        )

    def close_case(self, notes: str, *, user=None) -> None:
        if self.status == self.Status.CLOSED:
            return
        previous_status = self.status
        self.status = self.Status.CLOSED
        self.resolution_notes = notes
        self.closed_at = timezone.now()
        self.save(
            update_fields=[
                "status",
                "resolution_notes",
                "closed_at",
                "updated_at",
            ]
        )
        if previous_status != self.status:
            self.log_status_change(previous_status, user=user)
        self.log_event(
            notes or "Repossession case closed.",
            event_type=RepossessionEvent.EventType.STATUS,
            user=user,
        )


class RepossessionEvent(models.Model):
    """Timeline entries describing repossession actions."""

    class EventType(models.TextChoices):
        SYSTEM = "system", "System"
        REMINDER = "reminder", "Reminder"
        STATUS = "status", "Status change"
        NOTE = "note", "Note"

    case = models.ForeignKey(
        RepossessionCase,
        on_delete=models.CASCADE,
        related_name="events",
    )
    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
    )
    description = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="repossession_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.get_event_type_display()} for case {self.case_id}"
