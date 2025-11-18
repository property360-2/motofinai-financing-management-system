from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Stock(models.Model):
    """Represents a batch or variant of motorcycles in inventory."""
    brand = models.CharField(max_length=100)
    model_name = models.CharField("model", max_length=120)
    year = models.PositiveIntegerField(validators=[MinValueValidator(1900)])
    color = models.CharField(max_length=50, blank=True)
    quantity_available = models.PositiveIntegerField(default=0)
    quantity_sold = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["brand", "model_name", "year", "color"]
        unique_together = ("brand", "model_name", "year", "color")

    def __str__(self) -> str:
        color_str = f" ({self.color})" if self.color else ""
        return f"{self.year} {self.brand} {self.model_name}{color_str}"

    @property
    def total_quantity(self) -> int:
        """Returns total quantity (available + sold)."""
        return self.quantity_available + self.quantity_sold

    def decrease_available(self, amount: int = 1) -> None:
        """Decrease available quantity and increase sold quantity."""
        if self.quantity_available < amount:
            raise ValueError(f"Insufficient stock. Available: {self.quantity_available}, Requested: {amount}")
        self.quantity_available -= amount
        self.quantity_sold += amount
        self.save()

    def increase_available(self, amount: int = 1) -> None:
        """Increase available quantity (e.g., when repossessing)."""
        if self.quantity_sold < amount:
            raise ValueError(f"Cannot return more than sold. Sold: {self.quantity_sold}, Requested: {amount}")
        self.quantity_sold -= amount
        self.quantity_available += amount
        self.save()


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
    stock = models.ForeignKey(
        Stock,
        on_delete=models.PROTECT,
        related_name="motors",
        null=True,
        blank=True,
        help_text="Stock batch this motor belongs to.",
    )
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
    quantity = models.PositiveIntegerField(default=1, help_text="Number of units in inventory.")
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
