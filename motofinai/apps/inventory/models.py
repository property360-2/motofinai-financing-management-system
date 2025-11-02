from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class MotorQuerySet(models.QuerySet):
    def available(self):
        return self.filter(status=Motor.Status.AVAILABLE)


class Motor(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        RESERVED = "reserved", "Reserved"
        SOLD = "sold", "Sold"
        REPOSSESSED = "repossessed", "Repossessed"

    type = models.CharField(max_length=100, help_text="Motorcycle category (e.g. Scooter, Underbone).")
    brand = models.CharField(max_length=100)
    model_name = models.CharField("model", max_length=120)
    year = models.PositiveIntegerField(validators=[MinValueValidator(1900)])
    chassis_number = models.CharField(max_length=100, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True)
    purchase_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )
    image = models.ImageField(
        upload_to="inventory/motors/",
        blank=True,
        null=True,
        help_text="Motorcycle photo stored via configured media storage.",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = MotorQuerySet.as_manager()

    class Meta:
        ordering = ["brand", "model_name", "year"]
        unique_together = ("brand", "model_name", "year", "chassis_number")

    def __str__(self) -> str:
        return self.display_name

    @property
    def display_name(self) -> str:
        return f"{self.year} {self.brand} {self.model_name}".strip()

    @property
    def is_available(self) -> bool:
        return self.status == self.Status.AVAILABLE
