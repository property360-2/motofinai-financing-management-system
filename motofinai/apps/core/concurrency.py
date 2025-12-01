"""
Concurrency control and optimistic locking for handling simultaneous modifications.
Implements version-based concurrency control to prevent lost updates.
"""

from typing import Optional, Type
from decimal import Decimal
from datetime import datetime
from django.db import models, transaction
from django.core.exceptions import ObjectDoesNotExist
from .exceptions import ConcurrencyException


class VersionedModel(models.Model):
    """
    Abstract model that adds optimistic locking through versioning.
    Prevents lost updates when multiple users modify the same record simultaneously.
    """

    version = models.PositiveIntegerField(
        default=1,
        help_text="Version number for optimistic locking",
        db_index=True,
    )
    last_modified_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp of last modification",
        db_index=True,
    )

    class Meta:
        abstract = True

    def increment_version(self):
        """Increment version number for next update."""
        self.version += 1

    @classmethod
    def check_version(cls, instance_id, expected_version: int):
        """
        Check if the object version matches expected version.
        Raises ConcurrencyException if version mismatch.
        """
        try:
            obj = cls.objects.get(id=instance_id)
            if obj.version != expected_version:
                raise ConcurrencyException(
                    f"Object has been modified by another user. "
                    f"Expected version {expected_version}, found {obj.version}",
                    code="version_mismatch",
                    details=[
                        {
                            "current_version": obj.version,
                            "expected_version": expected_version,
                            "last_modified": obj.last_modified_at.isoformat(),
                        }
                    ],
                )
        except ObjectDoesNotExist:
            raise ConcurrencyException(
                f"Object no longer exists",
                code="object_deleted",
            )

    @staticmethod
    def get_for_update(model_class: Type["VersionedModel"], instance_id, expected_version: int = None):
        """
        Get an object for update with version checking.
        Uses database-level locking to prevent concurrent modifications.
        """
        obj = model_class.objects.select_for_update().get(id=instance_id)

        if expected_version is not None and obj.version != expected_version:
            raise ConcurrencyException(
                f"Object has been modified by another user",
                code="version_mismatch",
            )

        return obj


class ConsistencyChecker:
    """
    Utility for verifying data consistency and integrity across the system.
    Detects orphaned records, broken relationships, and invalid states.
    """

    @staticmethod
    def check_loan_consistency(loan_id: int) -> dict:
        """
        Check consistency of a loan and its related records.
        Returns dict with errors and warnings.
        """
        from motofinai.apps.loans.models import LoanApplication
        from motofinai.apps.payments.models import Payment, PaymentSchedule
        from motofinai.apps.inventory.models import Motor

        issues = {"errors": [], "warnings": []}

        try:
            loan = LoanApplication.objects.select_related("applicant", "motor").get(id=loan_id)
        except LoanApplication.DoesNotExist:
            issues["errors"].append(f"Loan {loan_id} not found")
            return issues

        # Check if motor exists
        if loan.motor_id and not Motor.objects.filter(id=loan.motor_id).exists():
            issues["errors"].append(
                f"Loan references non-existent motor (ID: {loan.motor_id})"
            )

        # Check if applicant exists
        if not loan.applicant or not loan.applicant.is_active:
            issues["warnings"].append("Loan applicant is inactive")

        # Check payment schedule consistency
        schedules = PaymentSchedule.objects.filter(loan=loan)
        total_scheduled = schedules.aggregate(models.Sum("amount"))["amount__sum"] or Decimal("0")

        if total_scheduled != loan.amount:
            issues["errors"].append(
                f"Payment schedule total ({total_scheduled}) does not match loan amount ({loan.amount})"
            )

        # Check payments
        payments = Payment.objects.filter(loan=loan)
        total_paid = payments.aggregate(models.Sum("amount"))["amount__sum"] or Decimal("0")

        if loan.status == "completed" and total_paid < loan.amount:
            issues["errors"].append(
                f"Loan marked completed but not fully paid (paid: {total_paid}, owed: {loan.amount})"
            )

        if total_paid > loan.amount:
            issues["errors"].append(
                f"Total paid ({total_paid}) exceeds loan amount ({loan.amount})"
            )

        # Check for late payments
        overdue_schedules = schedules.filter(
            due_date__lt=models.F("payment__paid_date"),
            status="unpaid",
        )
        if overdue_schedules.exists():
            issues["warnings"].append(f"{overdue_schedules.count()} payment(s) are overdue")

        return issues

    @staticmethod
    def check_payment_consistency(payment_id: int) -> dict:
        """Check consistency of a payment record."""
        from motofinai.apps.payments.models import Payment
        from motofinai.apps.loans.models import LoanApplication

        issues = {"errors": [], "warnings": []}

        try:
            payment = Payment.objects.select_related("loan").get(id=payment_id)
        except Payment.DoesNotExist:
            issues["errors"].append(f"Payment {payment_id} not found")
            return issues

        # Check if loan exists
        if not LoanApplication.objects.filter(id=payment.loan_id).exists():
            issues["errors"].append(
                f"Payment references non-existent loan (ID: {payment.loan_id})"
            )

        # Check if payment date is in future
        if payment.paid_date > datetime.now():
            issues["errors"].append("Payment date is in the future")

        # Check if payment amount matches scheduled amount
        if hasattr(payment, "schedule") and payment.schedule:
            scheduled = payment.schedule.amount
            if payment.amount > scheduled * Decimal("1.1"):
                issues["warnings"].append(
                    f"Payment amount ({payment.amount}) exceeds scheduled amount ({scheduled}) by more than 10%"
                )

        return issues

    @staticmethod
    def check_inventory_consistency(motor_id: int) -> dict:
        """Check consistency of inventory records."""
        from motofinai.apps.inventory.models import Motor
        from motofinai.apps.loans.models import LoanApplication

        issues = {"errors": [], "warnings": []}

        try:
            motor = Motor.objects.get(id=motor_id)
        except Motor.DoesNotExist:
            issues["errors"].append(f"Motor {motor_id} not found")
            return issues

        # Check if VIN is unique
        duplicates = Motor.objects.filter(vin=motor.vin).exclude(id=motor.id)
        if duplicates.exists():
            issues["errors"].append(
                f"VIN {motor.vin} is duplicated in {duplicates.count()} other record(s)"
            )

        # Check if motor is assigned to multiple loans
        active_loans = LoanApplication.objects.filter(
            motor=motor,
            status__in=["pending", "approved", "active"],
        )
        if active_loans.count() > 1:
            issues["errors"].append(
                f"Motor is assigned to {active_loans.count()} active loans"
            )

        # Check if motor status is consistent
        if motor.status == "active" and active_loans.count() == 0:
            issues["warnings"].append("Motor marked active but not assigned to any active loan")

        return issues

    @staticmethod
    def check_system_consistency() -> dict:
        """
        Perform comprehensive system consistency check.
        Returns dict with all issues found.
        """
        from motofinai.apps.loans.models import LoanApplication
        from motofinai.apps.payments.models import Payment
        from motofinai.apps.inventory.models import Motor

        issues = {
            "errors": [],
            "warnings": [],
            "timestamp": datetime.now().isoformat(),
        }

        # Check all loans
        for loan in LoanApplication.objects.all():
            loan_issues = ConsistencyChecker.check_loan_consistency(loan.id)
            issues["errors"].extend(loan_issues["errors"])
            issues["warnings"].extend(loan_issues["warnings"])

        # Check for orphaned payments
        orphaned_payments = Payment.objects.filter(loan_application__isnull=True)
        if orphaned_payments.exists():
            issues["errors"].append(
                f"Found {orphaned_payments.count()} orphaned payment(s) with no loan"
            )

        # Check for orphaned inventory
        orphaned_motors = Motor.objects.filter(
            purchase_order__isnull=True,
            status__in=["active", "reserved"],
        )
        if orphaned_motors.exists():
            issues["warnings"].append(
                f"Found {orphaned_motors.count()} motor(s) without purchase order"
            )

        return issues


class TransactionConsistency:
    """
    Utility for maintaining consistency within database transactions.
    Ensures atomicity of multi-step operations.
    """

    @staticmethod
    def execute_with_consistency_check(
        operation_func,
        *args,
        consistency_check_func=None,
        **kwargs,
    ):
        """
        Execute an operation within a transaction with consistency verification.
        Rolls back if consistency check fails.
        """
        with transaction.atomic():
            result = operation_func(*args, **kwargs)

            # Run consistency check if provided
            if consistency_check_func:
                issues = consistency_check_func(result)
                if issues["errors"]:
                    raise ConcurrencyException(
                        "Operation failed consistency check",
                        code="consistency_check_failed",
                        details=issues,
                    )

            return result

    @staticmethod
    @transaction.atomic
    def safe_update_with_version(
        model_class: Type[VersionedModel],
        instance_id: int,
        current_version: int,
        update_fields: dict,
    ):
        """
        Safely update an object checking current version.
        Raises ConcurrencyException if version doesn't match.
        """
        obj = model_class.objects.select_for_update().get(id=instance_id)

        if obj.version != current_version:
            raise ConcurrencyException(
                f"Object has been modified by another user",
                code="version_mismatch",
            )

        # Update fields
        for field, value in update_fields.items():
            setattr(obj, field, value)

        obj.increment_version()
        obj.save(update_fields=list(update_fields.keys()) + ["version"])

        return obj


class RaceConditionDetector:
    """
    Detects and logs potential race conditions in the system.
    Used for monitoring and debugging concurrent operation issues.
    """

    @staticmethod
    def detect_version_conflicts(model_class: Type[VersionedModel], hours: int = 1) -> dict:
        """
        Detect objects that had multiple updates within a time window.
        Indicates potential concurrent modification attempts.
        """
        from datetime import timedelta
        from django.utils import timezone

        cutoff_time = timezone.now() - timedelta(hours=hours)

        conflicts = model_class.objects.filter(
            last_modified_at__gte=cutoff_time,
            version__gt=1,
        ).order_by("-version")

        return {
            "detected_at": timezone.now().isoformat(),
            "time_window_hours": hours,
            "high_version_objects": [
                {
                    "id": obj.id,
                    "version": obj.version,
                    "last_modified": obj.last_modified_at.isoformat(),
                }
                for obj in conflicts[:10]  # Return top 10
            ],
        }

    @staticmethod
    def detect_deadlocks(model_class: Type[VersionedModel]) -> dict:
        """
        Monitor for deadlock patterns (objects with very high version numbers).
        Indicates potential excessive concurrent modifications.
        """
        high_version_objects = model_class.objects.filter(version__gte=10).order_by("-version")

        return {
            "detected_at": datetime.now().isoformat(),
            "objects_with_high_versions": [
                {
                    "id": obj.id,
                    "version": obj.version,
                    "last_modified": obj.last_modified_at.isoformat(),
                }
                for obj in high_version_objects[:20]
            ],
        }
