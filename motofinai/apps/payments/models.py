from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone

from motofinai.apps.loans.models import LoanApplication, PaymentSchedule


class PaymentMethod(models.TextChoices):
    """Available payment methods for installment collection."""

    CASH = "cash", "Cash"
    CHECK = "check", "Check"
    BANK_TRANSFER = "bank_transfer", "Bank Transfer"
    CREDIT_CARD = "credit_card", "Credit Card"
    MOBILE_MONEY = "mobile_money", "Mobile Money"
    OTHER = "other", "Other"


class Payment(models.Model):
    """Represents a recorded payment against a scheduled installment."""

    loan_application = models.ForeignKey(
        LoanApplication,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    schedule = models.OneToOneField(
        PaymentSchedule,
        on_delete=models.CASCADE,
        related_name="payment",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Amount collected for this installment.",
    )
    payment_date = models.DateField(
        default=timezone.localdate,
        help_text="Date the customer settled the installment.",
    )
    reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional receipt or reference identifier.",
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional context about the payment (mode, remarks, etc.).",
    )
    # Payment method tracking
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
        help_text="How the payment was received.",
    )
    # For check payments
    check_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Check number if payment method is check.",
    )
    check_date = models.DateField(
        blank=True,
        null=True,
        help_text="Date on the check if payment method is check.",
    )
    # For bank transfer payments
    bank_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="Bank name if payment method is bank transfer.",
    )
    bank_reference = models.CharField(
        max_length=150,
        blank=True,
        help_text="Bank transaction reference if payment method is bank transfer.",
    )
    # Reconciliation tracking
    reconciled = models.BooleanField(
        default=False,
        help_text="Whether this payment has been reconciled with bank statements.",
    )
    reconciled_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When this payment was reconciled.",
    )
    reconciled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reconciled_payments",
        help_text="Who reconciled this payment.",
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="recorded_payments",
    )
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-payment_date", "-recorded_at"]

    def __str__(self) -> str:
        return f"Payment for schedule {self.schedule_id}"

    def clean(self) -> None:
        super().clean()
        if self.schedule_id and self.loan_application_id:
            if self.schedule.loan_application_id != self.loan_application_id:
                raise ValidationError(
                    "Selected schedule is not part of the provided loan application."
                )
        if self.schedule_id and self.schedule.status == PaymentSchedule.Status.PAID and not self.pk:
            raise ValidationError("This installment has already been settled.")
        if self.amount <= Decimal("0.00"):
            raise ValidationError({"amount": "Payment amount must be greater than zero."})
        if self.schedule_id:
            expected = self.schedule.total_amount
            if self.amount != expected:
                raise ValidationError(
                    {"amount": "Payment amount must match the scheduled installment."}
                )

    def save(self, *args, **kwargs):
        if self.schedule_id and not self.loan_application_id:
            self.loan_application = self.schedule.loan_application
        self.full_clean()
        with transaction.atomic():
            super().save(*args, **kwargs)
            payment_date: date = self.payment_date
            self.schedule.mark_paid(payment_date)
            loan = self.schedule.loan_application
            loan.refresh_payment_progress(reference_date=payment_date)
