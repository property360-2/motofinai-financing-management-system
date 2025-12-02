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

    def decrease_available(self, amount: int = 1) -> None:
        """Decrease available stock and mark as sold."""
        if self.quantity_available < amount:
            raise ValueError(f"Insufficient available stock. Available: {self.quantity_available}, Requested: {amount}")
        self.quantity_available -= amount
        self.quantity_sold += amount
        self.save()

    def increase_available(self, amount: int = 1) -> None:
        """Increase available stock (typically from returning sold items)."""
        if self.quantity_sold < amount:
            raise ValueError(f"Cannot return more than sold. Sold: {self.quantity_sold}, Requested: {amount}")
        self.quantity_sold -= amount
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
        unique_together = ("brand", "model_name", "year")

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



class MotorReceiving(models.Model):
    """Track incoming motorcycles in the inventory receiving process."""
    
    class Status(models.TextChoices):
        PENDING = "pending", "Pending Receipt"
        RECEIVED = "received", "Received"
        INSPECTED = "inspected", "Inspected"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
    
    brand = models.CharField(max_length=100)
    model_name = models.CharField("model", max_length=120)
    year = models.PositiveIntegerField(validators=[MinValueValidator(1900)])
    vin_number = models.CharField(max_length=100, unique=True, help_text="Vehicle Identification Number (VIN/Chassis Number)")
    engine_number = models.CharField(max_length=100, blank=True, help_text="Engine/Motor number for identification")
    color = models.CharField(max_length=50, blank=True)
    motorcycle_type = models.CharField(max_length=20, choices=Motor.Type.choices, default=Motor.Type.SCOOTER)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))], help_text="Cost price from supplier")
    quantity = models.PositiveIntegerField(default=1)
    supplier_name = models.CharField(max_length=200, blank=True)
    purchase_order_number = models.CharField(max_length=100, blank=True)
    invoice_number = models.CharField(max_length=100, blank=True)
    inspection_status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, help_text="Inspection status of the motor")
    inspection_notes = models.TextField(blank=True)
    inspected_by = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="inspected_motors", help_text="User who performed the inspection")
    inspected_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    received_by = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="received_motors")
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="accepted_motors")
    rejection_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["vin_number"]), models.Index(fields=["status"]), models.Index(fields=["inspection_status"])]
    
    def __str__(self) -> str:
        return f"{self.year} {self.brand} {self.model_name} (VIN: {self.vin_number})"
    
    def mark_inspected(self, inspected_by, notes: str = "", passed: bool = True) -> None:
        from django.utils import timezone
        self.inspected_by = inspected_by
        self.inspected_at = timezone.now()
        self.inspection_notes = notes
        self.inspection_status = self.Status.INSPECTED if passed else self.Status.REJECTED
        self.status = self.Status.INSPECTED if passed else self.Status.REJECTED
        self.save()
    
    def mark_accepted(self, accepted_by, motor=None) -> None:
        from django.utils import timezone
        self.status = self.Status.ACCEPTED
        self.accepted_by = accepted_by
        self.accepted_at = timezone.now()
        self.save()



class ReceivingInspection(models.Model):
    """Quality inspection checklist for received motorcycles."""
    
    class Result(models.TextChoices):
        PASS = "pass", "Pass"
        FAIL = "fail", "Fail"
        NEEDS_REPAIR = "needs_repair", "Needs Repair"
    
    motor_receiving = models.ForeignKey(MotorReceiving, on_delete=models.CASCADE, related_name="inspections")
    engine_condition = models.CharField(max_length=20, choices=Result.choices, default=Result.PASS, help_text="Engine condition assessment")
    frame_condition = models.CharField(max_length=20, choices=Result.choices, default=Result.PASS, help_text="Frame integrity assessment")
    electrical_system = models.CharField(max_length=20, choices=Result.choices, default=Result.PASS, help_text="Electrical components assessment")
    tires_condition = models.CharField(max_length=20, choices=Result.choices, default=Result.PASS, help_text="Tire condition assessment")
    brakes_condition = models.CharField(max_length=20, choices=Result.choices, default=Result.PASS, help_text="Brake system assessment")
    paint_condition = models.CharField(max_length=20, choices=Result.choices, default=Result.PASS, help_text="Paint and body condition")
    overall_result = models.CharField(max_length=20, choices=Result.choices, default=Result.PASS)
    issues_found = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    inspector = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="conducted_inspections")
    inspected_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-inspected_at"]
    
    def __str__(self) -> str:
        return f"Inspection for {self.motor_receiving} - {self.overall_result}"
    
    @property
    def passed(self) -> bool:
        return self.overall_result == self.Result.PASS


class ReceivingDocument(models.Model):
    """Store documents related to motor receiving (invoices, certificates, etc)."""
    
    class DocumentType(models.TextChoices):
        INVOICE = "invoice", "Invoice"
        PURCHASE_ORDER = "purchase_order", "Purchase Order"
        DELIVERY_NOTE = "delivery_note", "Delivery Note"
        INSPECTION_REPORT = "inspection_report", "Inspection Report"
        CERTIFICATE = "certificate", "Certificate/Title"
        OTHER = "other", "Other"
    
    motor_receiving = models.ForeignKey(MotorReceiving, on_delete=models.CASCADE, related_name="documents")
    document_type = models.CharField(max_length=30, choices=DocumentType.choices)
    document_name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to="receiving_documents/%Y/%m/%d/", blank=True, null=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)
    document_date = models.DateField(blank=True, null=True)
    reference_number = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="uploaded_receiving_documents")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-uploaded_at"]
        unique_together = ("motor_receiving", "document_type", "reference_number")
    
    def __str__(self) -> str:
        return f"{self.document_name} - {self.get_document_type_display()}"
