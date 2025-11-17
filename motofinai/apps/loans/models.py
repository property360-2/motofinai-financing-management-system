from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from motofinai.apps.inventory.models import Motor


class FinancingTerm(models.Model):
    term_years = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Loan duration in years.",
    )
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Annual interest rate percentage (e.g. 12.5).",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["term_years", "interest_rate"]
        unique_together = ("term_years", "interest_rate")

    def __str__(self) -> str:
        return f"{self.term_years}-yr @ {self.interest_rate}%"

    @property
    def total_months(self) -> int:
        return self.term_years * 12

    @property
    def monthly_interest_rate(self) -> Decimal:
        """Return rate as decimal fraction per month."""
        return (self.interest_rate / Decimal("100")) / Decimal("12")


def add_months(start: date, months: int) -> date:
    """Advance ``start`` by ``months`` calendar months preserving the day where possible."""

    year = start.year + (start.month - 1 + months) // 12
    month = (start.month - 1 + months) % 12 + 1
    day = min(start.day, monthrange(year, month)[1])
    return date(year, month, day)


@dataclass
class PaymentBreakdown:
    principal: Decimal
    interest: Decimal
    total: Decimal


class LoanApplicationQuerySet(models.QuerySet):
    def pending(self):
        return self.filter(status=LoanApplication.Status.PENDING)

    def approved(self):
        return self.filter(status=LoanApplication.Status.APPROVED)

    def active(self):
        return self.filter(status=LoanApplication.Status.ACTIVE)


class LoanApplication(models.Model):
    """Represents a submitted request for financing a motorcycle purchase."""

    class EmploymentStatus(models.TextChoices):
        EMPLOYED = "employed", "Employed"
        SELF_EMPLOYED = "self_employed", "Self-employed"
        UNEMPLOYED = "unemployed", "Unemployed"
        STUDENT = "student", "Student"
        RETIRED = "retired", "Retired"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"

    applicant_first_name = models.CharField(max_length=100)
    applicant_last_name = models.CharField(max_length=100)
    applicant_email = models.EmailField()
    applicant_phone = models.CharField(max_length=32)
    date_of_birth = models.DateField(blank=True, null=True)
    employment_status = models.CharField(
        max_length=20,
        choices=EmploymentStatus.choices,
        default=EmploymentStatus.EMPLOYED,
    )
    employer_name = models.CharField(max_length=150, blank=True)
    monthly_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    motor = models.ForeignKey(
        Motor,
        on_delete=models.PROTECT,
        related_name="loan_applications",
    )
    financing_term = models.ForeignKey(
        FinancingTerm,
        on_delete=models.PROTECT,
        related_name="loan_applications",
    )
    loan_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Total amount being financed before down payment.",
    )
    down_payment = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        default=Decimal("0.00"),
        help_text="Amount paid upfront to reduce the financed principal.",
    )
    principal_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Loan amount after deducting down payment.",
    )
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Captured interest rate percentage from the financing term.",
    )
    monthly_payment = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    has_valid_id = models.BooleanField(default=False)
    has_proof_of_income = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="submitted_loan_applications",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    activated_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LoanApplicationQuerySet.as_manager()

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self) -> str:
        return f"Loan application for {self.motor} by {self.applicant_full_name}"

    @property
    def applicant_full_name(self) -> str:
        return f"{self.applicant_first_name} {self.applicant_last_name}".strip()

    def clean(self) -> None:
        if self.down_payment > self.loan_amount:
            raise ValidationError("Down payment cannot exceed total loan amount.")

    def calculate_monthly_payment(self) -> Decimal:
        """Return the simple-interest monthly payment defined in the project plan."""

        principal = self.principal_amount
        if principal <= Decimal("0"):
            return Decimal("0.00")

        term_years = Decimal(self.financing_term.term_years)
        total_months = self.financing_term.total_months
        annual_rate = (self.interest_rate or Decimal("0.00")) / Decimal("100")

        total_interest = (principal * annual_rate * term_years).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        total_amount = principal + total_interest
        payment = total_amount / Decimal(total_months)
        return payment.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def update_monthly_payment(self, save: bool = True) -> Decimal:
        payment = self.calculate_monthly_payment()
        self.monthly_payment = payment
        if save:
            self.save(update_fields=["monthly_payment", "updated_at"])
        return payment

    def approve(self) -> None:
        if self.status != self.Status.PENDING:
            raise ValidationError("Only pending applications can be approved.")
        self.update_monthly_payment()
        self.status = self.Status.APPROVED
        self.approved_at = timezone.now()
        self.save(update_fields=["status", "approved_at", "updated_at"])
        self.generate_payment_schedule()
        self.evaluate_risk()

    def activate(self) -> None:
        if self.status != self.Status.APPROVED:
            raise ValidationError("Only approved applications can be activated.")
        # Decrease stock when activating loan (motor is being financed/sold)
        if self.motor and self.motor.stock:
            try:
                self.motor.stock.decrease_available(amount=1)
            except ValueError as e:
                raise ValidationError(f"Stock management error: {str(e)}")
        self.status = self.Status.ACTIVE
        self.activated_at = timezone.now()
        self.save(update_fields=["status", "activated_at", "updated_at"])

    def complete(self) -> None:
        if self.status != self.Status.ACTIVE:
            raise ValidationError("Only active applications can be completed.")
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at", "updated_at"])

    def refresh_overdue_schedules(self, *, reference_date: date | None = None) -> int:
        return self.payment_schedules.mark_overdue(reference_date)

    def update_completion_from_payments(self) -> None:
        if self.status != self.Status.ACTIVE:
            return
        if not self.payment_schedules.exclude(status=PaymentSchedule.Status.PAID).exists():
            self.complete()

    def refresh_payment_progress(self, *, reference_date: date | None = None) -> None:
        self.refresh_overdue_schedules(reference_date=reference_date)
        self.update_completion_from_payments()
        self.evaluate_risk()
        RepossessionCase = apps.get_model("repossession", "RepossessionCase")
        RepossessionCase.objects.sync_for_loan(self)

    def evaluate_risk(
        self,
        *,
        base_score: int | None = None,
        credit_score: int | None = None,
        notes: str | None = None,
    ) -> "RiskAssessment":
        RiskAssessment = apps.get_model("risk", "RiskAssessment")
        return RiskAssessment.objects.evaluate_for_loan(
            self,
            base_score=base_score,
            credit_score=credit_score,
            notes=notes,
        )

    def generate_payment_schedule(self, *, start_date: date | None = None) -> None:
        """Generate or refresh the payment schedule based on current loan values."""

        PaymentSchedule.objects.filter(loan_application=self).delete()
        if self.principal_amount <= Decimal("0"):
            return

        start_date = start_date or timezone.now().date()
        periods = self.financing_term.total_months
        principal_total = self.principal_amount
        annual_rate = (self.interest_rate or Decimal("0.00")) / Decimal("100")
        total_interest = (
            principal_total
            * annual_rate
            * Decimal(self.financing_term.term_years)
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        monthly_payment = self.monthly_payment
        if monthly_payment <= Decimal("0.00"):
            monthly_payment = self.calculate_monthly_payment()
        principal_share = principal_total / Decimal(periods)
        principal_paid = Decimal("0.00")
        interest_paid = Decimal("0.00")

        schedules: list[PaymentSchedule] = []

        for index in range(periods):
            if index == periods - 1:
                remaining_principal = principal_total - principal_paid
                remaining_interest = total_interest - interest_paid
                principal_amount = max(remaining_principal, Decimal("0.00")).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP,
                )
                interest_amount = max(remaining_interest, Decimal("0.00")).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP,
                )
                payment_total = (principal_amount + interest_amount).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP,
                )
            else:
                principal_amount = principal_share.quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP,
                )
                if principal_amount > monthly_payment:
                    principal_amount = monthly_payment
                interest_amount = (monthly_payment - principal_amount).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP,
                )
                if interest_amount < Decimal("0.00"):
                    interest_amount = Decimal("0.00")
                    principal_amount = monthly_payment
                payment_total = monthly_payment
                principal_paid += principal_amount
                interest_paid += interest_amount

            schedules.append(
                PaymentSchedule(
                    loan_application=self,
                    sequence=index + 1,
                    due_date=add_months(start_date, index + 1),
                    principal_amount=principal_amount,
                    interest_amount=interest_amount,
                    total_amount=payment_total.quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    ),
                )
            )

        PaymentSchedule.objects.bulk_create(schedules)

    def payment_breakdown(self) -> Iterable[PaymentBreakdown]:
        for schedule in self.payment_schedules.order_by("sequence"):
            yield PaymentBreakdown(
                principal=schedule.principal_amount,
                interest=schedule.interest_amount,
                total=schedule.total_amount,
            )


class PaymentScheduleQuerySet(models.QuerySet):
    def due(self):
        return self.filter(status=self.model.Status.DUE)

    def paid(self):
        return self.filter(status=self.model.Status.PAID)

    def overdue(self):
        return self.filter(status=self.model.Status.OVERDUE)

    def mark_overdue(self, reference_date: date | None = None) -> int:
        reference = reference_date or timezone.now().date()
        return self.filter(
            status=self.model.Status.DUE,
            due_date__lt=reference,
        ).update(status=self.model.Status.OVERDUE)


class PaymentSchedule(models.Model):
    class Status(models.TextChoices):
        DUE = "due", "Due"
        OVERDUE = "overdue", "Overdue"
        PAID = "paid", "Paid"

    loan_application = models.ForeignKey(
        LoanApplication,
        on_delete=models.CASCADE,
        related_name="payment_schedules",
    )
    sequence = models.PositiveIntegerField()
    due_date = models.DateField()
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DUE,
    )
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = PaymentScheduleQuerySet.as_manager()

    class Meta:
        ordering = ["sequence"]
        unique_together = ("loan_application", "sequence")

    def mark_paid(self, when: date | datetime | None = None) -> None:
        timestamp: datetime
        if when is None:
            timestamp = timezone.now()
        elif isinstance(when, datetime):
            timestamp = when
        else:
            naive = datetime.combine(when, time.min)
            try:
                timestamp = timezone.make_aware(naive)
            except ValueError:
                timestamp = naive
        self.status = self.Status.PAID
        self.paid_at = timestamp
        self.save(update_fields=["status", "paid_at"])
        self.loan_application.update_completion_from_payments()

    def refresh_status(self, reference_date: date | None = None) -> None:
        if self.status == self.Status.PAID:
            return
        reference = reference_date or timezone.now().date()
        if self.due_date < reference and self.status != self.Status.OVERDUE:
            self.status = self.Status.OVERDUE
            self.save(update_fields=["status"])

    def __str__(self) -> str:
        return f"Payment {self.sequence} for application {self.loan_application_id}"


def loan_document_upload_to(instance: "LoanDocument", filename: str) -> str:
    base = Path("loan_documents")
    return str(base / str(instance.loan_application_id) / filename)


class LoanDocument(models.Model):
    class DocumentType(models.TextChoices):
        VALID_ID = "valid_id", "Valid ID"
        PROOF_OF_INCOME = "proof_of_income", "Proof of income"
        OTHER = "other", "Other supporting document"

    loan_application = models.ForeignKey(
        LoanApplication,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    document_type = models.CharField(
        max_length=50,
        choices=DocumentType.choices,
    )
    title = models.CharField(
        max_length=150,
        blank=True,
        help_text="Optional label to help staff identify the file.",
    )
    file = models.FileField(
        upload_to=loan_document_upload_to,
        validators=[FileExtensionValidator(["pdf", "png", "jpg", "jpeg"])],
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_loan_documents",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return f"{self.get_document_type_display()} for application {self.loan_application_id}"

    @property
    def filename(self) -> str:
        return Path(self.file.name).name

    def clean(self) -> None:
        super().clean()
        allowed_mimetypes = {
            "application/pdf",
            "image/jpeg",
            "image/png",
        }
        field_file = getattr(self, "file", None)
        if not field_file or not getattr(field_file, "name", ""):
            return
        try:
            uploaded_file = field_file.file
        except ValueError:
            return
        content_type = getattr(uploaded_file, "content_type", None)
        if content_type and content_type not in allowed_mimetypes:
            raise ValidationError(
                {
                    "file": "Only PDF, JPEG, or PNG files are supported.",
                }
            )
        if uploaded_file is not None and getattr(uploaded_file, "size", 0) <= 0:
            raise ValidationError({"file": "Uploaded document appears to be empty."})
