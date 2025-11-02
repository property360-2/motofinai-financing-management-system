"""Risk scoring data models."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict

from django.db import models


@dataclass(frozen=True)
class RiskComputation:
    """Container for the computed risk factors and resulting score."""

    base_score: int
    credit_score: int
    missed_payments: int
    employment_penalty: int
    income_factor: Decimal
    credit_factor: Decimal
    debt_to_income_ratio: Decimal
    score: int
    risk_level: str


class RiskAssessmentQuerySet(models.QuerySet):
    def by_level(self) -> Dict[str, int]:
        """Return a mapping of risk level -> count for quick dashboards."""

        levels = {level: 0 for level, _ in RiskAssessment.RiskLevel.choices}
        for row in self.values("risk_level").annotate(total=models.Count("pk")):
            levels[row["risk_level"]] = row["total"]
        return levels


class RiskAssessmentManager(models.Manager["RiskAssessment"]):
    """Provide helpers for creating or refreshing loan risk evaluations."""

    DEFAULT_BASE_SCORE = 30
    DEFAULT_CREDIT_SCORE = 650

    def get_queryset(self) -> RiskAssessmentQuerySet:
        return RiskAssessmentQuerySet(self.model, using=self._db)

    def evaluate_for_loan(
        self,
        loan_application,
        *,
        base_score: int | None = None,
        credit_score: int | None = None,
        notes: str | None = None,
    ) -> "RiskAssessment":
        """Create or refresh a risk assessment for ``loan_application``."""

        try:
            existing = loan_application.risk_assessment
        except self.model.DoesNotExist:  # type: ignore[attr-defined]
            existing = None
        base = base_score if base_score is not None else getattr(existing, "base_score", self.DEFAULT_BASE_SCORE)
        credit = credit_score if credit_score is not None else getattr(
            existing, "credit_score", self.DEFAULT_CREDIT_SCORE
        )
        notes_value = notes if notes is not None else getattr(existing, "notes", "")
        computation = RiskAssessment.compute(loan_application, base_score=base, credit_score=credit)
        defaults = {
            "score": computation.score,
            "risk_level": computation.risk_level,
            "base_score": computation.base_score,
            "credit_score": computation.credit_score,
            "missed_payments": computation.missed_payments,
            "employment_penalty": computation.employment_penalty,
            "income_factor": computation.income_factor,
            "credit_factor": computation.credit_factor,
            "debt_to_income_ratio": computation.debt_to_income_ratio,
            "notes": notes_value,
        }
        assessment, _ = self.update_or_create(
            loan_application=loan_application,
            defaults=defaults,
        )
        return assessment


class RiskAssessment(models.Model):
    """Represents a calculated risk profile for a loan application."""

    class RiskLevel(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    EMPLOYMENT_PENALTIES = {
        "employed": 0,
        "self_employed": 8,
        "unemployed": 25,
        "student": 10,
        "retired": 6,
    }

    LOW_THRESHOLD = 40
    HIGH_THRESHOLD = 70

    loan_application = models.OneToOneField(
        "loans.LoanApplication",
        on_delete=models.CASCADE,
        related_name="risk_assessment",
    )
    score = models.PositiveIntegerField()
    risk_level = models.CharField(max_length=10, choices=RiskLevel.choices)
    base_score = models.PositiveIntegerField(default=RiskAssessmentManager.DEFAULT_BASE_SCORE)
    credit_score = models.PositiveIntegerField(default=RiskAssessmentManager.DEFAULT_CREDIT_SCORE)
    missed_payments = models.PositiveIntegerField(default=0)
    employment_penalty = models.IntegerField(default=0)
    income_factor = models.DecimalField(max_digits=6, decimal_places=2)
    credit_factor = models.DecimalField(max_digits=6, decimal_places=2)
    debt_to_income_ratio = models.DecimalField(max_digits=6, decimal_places=2)
    notes = models.TextField(blank=True)
    calculated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = RiskAssessmentManager()

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"Risk assessment for application {self.loan_application_id}"

    @classmethod
    def compute(
        cls,
        loan_application,
        *,
        base_score: int,
        credit_score: int,
    ) -> RiskComputation:
        from motofinai.apps.loans.models import PaymentSchedule

        missed_payments = loan_application.payment_schedules.filter(
            status=PaymentSchedule.Status.OVERDUE
        ).count()

        monthly_income = getattr(loan_application, "monthly_income", Decimal("0.00"))
        principal = getattr(loan_application, "principal_amount", Decimal("0.00"))
        monthly_payment = getattr(loan_application, "monthly_payment", Decimal("0.00"))

        if monthly_income <= Decimal("0.00"):
            income_factor = Decimal("30.00")
            dti_ratio = Decimal("100.00")
        else:
            ratio = principal / monthly_income
            income_factor = min(
                (ratio * Decimal("10")),
                Decimal("30.00"),
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            dti_ratio = min(
                (monthly_payment / monthly_income * Decimal("100")),
                Decimal("999.99"),
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        credit_factor = min(
            Decimal(credit_score) / Decimal("20"),
            Decimal("25.00"),
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        employment_penalty = cls.EMPLOYMENT_PENALTIES.get(
            getattr(loan_application, "employment_status", ""),
            0,
        )

        raw_score = (
            Decimal(base_score)
            + Decimal(missed_payments * 15)
            + income_factor
            - credit_factor
            + Decimal(employment_penalty)
        )
        rounded = int(max(0, raw_score.quantize(Decimal("1"), rounding=ROUND_HALF_UP)))
        risk_level = cls.level_for_score(rounded)

        return RiskComputation(
            base_score=base_score,
            credit_score=credit_score,
            missed_payments=missed_payments,
            employment_penalty=employment_penalty,
            income_factor=income_factor,
            credit_factor=credit_factor,
            debt_to_income_ratio=dti_ratio,
            score=rounded,
            risk_level=risk_level,
        )

    @classmethod
    def level_for_score(cls, score: int) -> str:
        if score < cls.LOW_THRESHOLD:
            return cls.RiskLevel.LOW
        if score < cls.HIGH_THRESHOLD:
            return cls.RiskLevel.MEDIUM
        return cls.RiskLevel.HIGH

    def as_dict(self) -> Dict[str, int | Decimal | str]:
        return {
            "score": self.score,
            "risk_level": self.risk_level,
            "missed_payments": self.missed_payments,
            "employment_penalty": self.employment_penalty,
            "income_factor": self.income_factor,
            "credit_factor": self.credit_factor,
            "debt_to_income_ratio": self.debt_to_income_ratio,
        }

    def refresh(self, *, base_score: int | None = None, credit_score: int | None = None) -> "RiskAssessment":
        """Recalculate this assessment from the linked loan application."""

        return RiskAssessment.objects.evaluate_for_loan(
            self.loan_application,
            base_score=base_score or self.base_score,
            credit_score=credit_score or self.credit_score,
            notes=self.notes,
        )
