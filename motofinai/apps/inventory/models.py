from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Stock(models.Model):
    """Represents a batch or variant of motorcycles in inventory with status tracking."""
    brand = models.CharField(max_length=100)
    model_name = models.CharField("model", max_length=120)
    year = models.PositiveIntegerField(validators=[MinValueValidator(1900)])
    color = models.CharField(max_length=50, blank=True)
    quantity_available = models.PositiveIntegerField(default=0)
    quantity_reserved = models.PositiveIntegerField(default=0)
    quantity_sold = models.PositiveIntegerField(default=0)
    quantity_repossessed = models.PositiveIntegerField(default=0)
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
        """Returns total quantity across all statuses."""
        return self.quantity_available + self.quantity_reserved + self.quantity_sold + self.quantity_repossessed

    def mark_as_reserved(self, amount: int = 1) -> None:
        """Mark units as reserved."""
        if self.quantity_available < amount:
            raise ValueError(f"Insufficient available stock. Available: {self.quantity_available}, Requested: {amount}")
        self.quantity_available -= amount
        self.quantity_reserved += amount
        self.save()

    def mark_as_sold(self, amount: int = 1) -> None:
        """Mark units as sold (from available or reserved)."""
        if self.quantity_available >= amount:
            self.quantity_available -= amount
            self.quantity_sold += amount
        elif self.quantity_reserved >= amount:
            self.quantity_reserved -= amount
            self.quantity_sold += amount
        else:
            raise ValueError(f"Insufficient stock for sale. Available: {self.quantity_available}, Reserved: {self.quantity_reserved}, Requested: {amount}")
        self.save()

    def mark_as_repossessed(self, amount: int = 1) -> None:
        """Mark sold units as repossessed."""
        if self.quantity_sold < amount:
            raise ValueError(f"Cannot repossess more than sold. Sold: {self.quantity_sold}, Requested: {amount}")
        self.quantity_sold -= amount
        self.quantity_repossessed += amount
        self.save()

    def return_to_available(self, amount: int = 1) -> None:
        """Return repossessed units back to available."""
        if self.quantity_repossessed < amount:
            raise ValueError(f"Cannot return more than repossessed. Repossessed: {self.quantity_repossessed}, Requested: {amount}")
        self.quantity_repossessed -= amount
        self.quantity_available += amount
        self.save()

    def cancel_reservation(self, amount: int = 1) -> None:
        """Cancel reserved units and return to available."""
        if self.quantity_reserved < amount:
            raise ValueError(f"Cannot cancel more than reserved. Reserved: {self.quantity_reserved}, Requested: {amount}")
        self.quantity_reserved -= amount
        self.quantity_available += amount
        self.save()


class MotorQuerySet(models.QuerySet):
    """Custom QuerySet for Motor model."""
    pass


class Motor(models.Model):
    class Type(models.TextChoices):
        SCOOTER = "scooter", "Scooter"
        UNDERBONE = "underbone", "Underbone"
        STANDARD = "standard", "Standard"
        CRUISER = "cruiser", "Cruiser"
        SPORT = "sport", "Sport"
        TOURING = "touring", "Touring"
        ADVENTURE = "adventure", "Adventure"
        MOPED = "moped", "Moped"
        CAPPING = "capping", "Capping"
        TRICYCLE = "tricycle", "Tricycle"

    class ApprovalStatus(models.TextChoices):
        PENDING = "pending", "Pending Approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.SCOOTER,
        help_text="Motorcycle category",
    )
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
    quantity = models.PositiveIntegerField(default=1, help_text="Number of units in inventory.")
    notes = models.TextField(blank=True)
    # Approval workflow fields
    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
        help_text="Motorcycle approval status for financing",
    )
    approved_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_motors",
        help_text="Finance officer who approved this motorcycle",
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this motorcycle was approved",
    )
    approval_notes = models.TextField(
        blank=True,
        help_text="Notes from the approving finance officer",
    )
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
    def type_display(self) -> str:
        """Get human-readable type label."""
        return self.get_type_display()

    @property
    def status(self) -> str:
        """Derive motor status from associated loan applications."""
        if not hasattr(self, '_status_cache'):
            # Check for repossession first
            try:
                from motofinai.apps.repossession.models import RepossessionCase
                if RepossessionCase.objects.filter(loan_application__motor=self).exists():
                    self._status_cache = 'repossessed'
                    return self._status_cache
            except (ImportError, Exception):
                pass

            # Check loan application statuses
            from motofinai.apps.loans.models import LoanApplication

            # Check for active/completed (sold)
            if self.loan_applications.filter(status__in=['active', 'completed']).exists():
                self._status_cache = 'sold'
            # Check for pending/approved (reserved)
            elif self.loan_applications.filter(status__in=['pending', 'approved']).exists():
                self._status_cache = 'reserved'
            # No loan applications (available)
            else:
                self._status_cache = 'available'

        return self._status_cache

    def get_available_count(self) -> int:
        """Count motors without loan applications."""
        from motofinai.apps.loans.models import LoanApplication
        return 1 if not self.loan_applications.exists() else 0

    def get_reserved_count(self) -> int:
        """Count motors with pending or approved loan applications."""
        return self.loan_applications.filter(status__in=['pending', 'approved']).count()

    def get_sold_count(self) -> int:
        """Count motors with active or completed loan applications."""
        return self.loan_applications.filter(status__in=['active', 'completed']).count()

    def get_repossessed_count(self) -> int:
        """Count motors with repossession cases."""
        try:
            from motofinai.apps.repossession.models import RepossessionCase
            return RepossessionCase.objects.filter(loan_application__motor=self).count()
        except (ImportError, Exception):
            return 0

    def get_reserved_applications(self):
        """Get pending or approved loan applications."""
        return self.loan_applications.filter(status__in=['pending', 'approved']).select_related('financing_term')

    def get_sold_applications(self):
        """Get active or completed loan applications."""
        return self.loan_applications.filter(status__in=['active', 'completed']).select_related('financing_term')

    def get_repossessed_applications(self):
        """Get repossession cases for this motor."""
        try:
            from motofinai.apps.repossession.models import RepossessionCase
            return RepossessionCase.objects.filter(loan_application__motor=self).select_related('loan_application')
        except (ImportError, Exception):
            return []

    def approve(self, approved_by, notes: str = "") -> None:
        """Approve the motorcycle for financing."""
        from django.utils import timezone
        if self.approval_status != self.ApprovalStatus.PENDING:
            raise ValueError(f"Only pending motors can be approved. Current status: {self.approval_status}")
        self.approval_status = self.ApprovalStatus.APPROVED
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.approval_notes = notes
        self.save()

    def reject(self, approved_by, notes: str = "") -> None:
        """Reject the motorcycle for financing."""
        from django.utils import timezone
        if self.approval_status != self.ApprovalStatus.PENDING:
            raise ValueError(f"Only pending motors can be rejected. Current status: {self.approval_status}")
        self.approval_status = self.ApprovalStatus.REJECTED
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.approval_notes = notes
        self.save()
