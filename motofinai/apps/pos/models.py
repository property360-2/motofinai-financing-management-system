"""Point-of-Sale models for payment collection and session management."""

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from motofinai.apps.payments.models import Payment


class POSSessionQuerySet(models.QuerySet):
    """QuerySet for POS sessions."""

    def active(self):
        """Return only open sessions."""
        return self.filter(status=POSSession.Status.OPEN)

    def closed(self):
        """Return only closed sessions."""
        return self.filter(status=POSSession.Status.CLOSED)


class POSSession(models.Model):
    """Represents a cashier's POS session for daily payment collection."""

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"

    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="opened_pos_sessions",
        help_text="Cashier who opened this session.",
    )
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="closed_pos_sessions",
        help_text="Cashier who closed this session.",
    )
    closed_at = models.DateTimeField(blank=True, null=True)
    opening_cash = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Cash float at session start.",
    )
    closing_cash = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Cash float at session end.",
    )
    notes = models.TextField(
        blank=True,
        help_text="Session notes or discrepancies.",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.OPEN,
    )

    objects = POSSessionQuerySet.as_manager()

    class Meta:
        ordering = ["-opened_at"]

    def __str__(self) -> str:
        return f"POS Session {self.id} - {self.opened_by.get_full_name()} ({self.opened_at.date()})"

    def close_session(self, closing_cash: Decimal, closed_by=None):
        """Close this POS session."""
        if self.status == self.Status.CLOSED:
            raise ValidationError("This session is already closed.")
        self.closing_cash = closing_cash
        self.closed_by = closed_by
        self.closed_at = timezone.now()
        self.status = self.Status.CLOSED
        self.save()

    @property
    def transaction_count(self) -> int:
        """Get count of transactions in this session."""
        return self.transactions.count()

    @property
    def total_collected(self) -> Decimal:
        """Get total amount collected in this session."""
        return sum(
            (t.payment.amount for t in self.transactions.all()),
            Decimal("0.00"),
        )

    @property
    def cash_variance(self) -> Decimal | None:
        """Get variance between expected and actual cash."""
        if not self.closing_cash:
            return None
        expected = self.opening_cash + self.total_collected
        return self.closing_cash - expected


class POSTransaction(models.Model):
    """Represents a transaction recorded in a POS session."""

    class TransactionType(models.TextChoices):
        PAYMENT = "payment", "Payment"
        REFUND = "refund", "Refund"
        ADJUSTMENT = "adjustment", "Adjustment"

    session = models.ForeignKey(
        POSSession,
        on_delete=models.PROTECT,
        related_name="transactions",
        help_text="POS session this transaction belongs to.",
    )
    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name="pos_transaction",
        help_text="Payment being recorded.",
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        default=TransactionType.PAYMENT,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.get_transaction_type_display()} - ₱{self.payment.amount} ({self.payment.loan_application.applicant_full_name})"


class ReceiptLog(models.Model):
    """Log for receipt generation and printing."""

    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name="receipt_log",
        help_text="Payment this receipt is for.",
    )
    receipt_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Sequential receipt number.",
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    printed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the receipt was printed.",
    )
    printed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="printed_receipts",
        help_text="Who printed this receipt.",
    )
    print_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this receipt was printed.",
    )

    class Meta:
        ordering = ["-generated_at"]

    def __str__(self) -> str:
        return f"Receipt #{self.receipt_number}"

    def mark_printed(self, printed_by=None):
        """Record that receipt was printed."""
        self.printed_at = timezone.now()
        self.printed_by = printed_by
        self.print_count += 1
        self.save()


def get_next_receipt_number() -> str:
    """Generate the next sequential receipt number."""
    last_receipt = ReceiptLog.objects.order_by("-id").first()
    if not last_receipt:
        return "RCP-000001"
    last_number = int(last_receipt.receipt_number.split("-")[-1])
    next_number = last_number + 1
    return f"RCP-{next_number:06d}"
