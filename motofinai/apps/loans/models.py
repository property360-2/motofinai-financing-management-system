from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


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
