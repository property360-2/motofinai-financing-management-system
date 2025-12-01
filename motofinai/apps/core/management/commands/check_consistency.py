"""
Django management command for system consistency checks.
Detects and reports data inconsistencies and integrity issues.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from motofinai.apps.core.concurrency import ConsistencyChecker
from motofinai.apps.loans.models import LoanApplication
from motofinai.apps.payments.models import Payment
from motofinai.apps.inventory.models import Motor


class Command(BaseCommand):
    """Check system consistency and report issues."""

    help = "Run comprehensive system consistency checks"

    def add_arguments(self, parser):
        parser.add_argument(
            "--loan",
            type=int,
            help="Check consistency of a specific loan",
        )
        parser.add_argument(
            "--payment",
            type=int,
            help="Check consistency of a specific payment",
        )
        parser.add_argument(
            "--motor",
            type=int,
            help="Check consistency of a specific motor",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Run full system consistency check",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed results",
        )
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Attempt to fix detected issues (use with caution)",
        )

    def handle(self, *args, **options):
        """Execute consistency check."""
        self.stdout.write(self.style.SUCCESS("Starting consistency checks...\n"))

        total_errors = 0
        total_warnings = 0

        # Specific checks
        if options["loan"]:
            total_errors, total_warnings = self.check_loan(
                options["loan"], options["verbose"], options["fix"]
            )

        elif options["payment"]:
            total_errors, total_warnings = self.check_payment(
                options["payment"], options["verbose"], options["fix"]
            )

        elif options["motor"]:
            total_errors, total_warnings = self.check_motor(
                options["motor"], options["verbose"], options["fix"]
            )

        elif options["all"]:
            total_errors, total_warnings = self.check_all(
                options["verbose"], options["fix"]
            )

        else:
            # Default: quick system check
            total_errors, total_warnings = self.quick_check(
                options["verbose"], options["fix"]
            )

        # Summary
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 50))
        self.stdout.write(
            self.style.SUCCESS(f"Consistency check completed")
        )
        self.stdout.write(f"Errors found: {self.style.ERROR(str(total_errors))}")
        self.stdout.write(f"Warnings found: {self.style.WARNING(str(total_warnings))}")

        if total_errors > 0 and not options["fix"]:
            self.stdout.write(
                self.style.WARNING(
                    "\nRun with --fix flag to attempt automatic fixes (use with caution)"
                )
            )

        return 0 if total_errors == 0 else 1

    def check_loan(self, loan_id, verbose=False, fix=False):
        """Check specific loan consistency."""
        self.stdout.write(f"\nChecking loan {loan_id}...")

        try:
            loan = LoanApplication.objects.get(id=loan_id)
        except LoanApplication.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Loan {loan_id} not found"))
            return 1, 0

        issues = ConsistencyChecker.check_loan_consistency(loan_id)

        errors = len(issues["errors"])
        warnings = len(issues["warnings"])

        if issues["errors"]:
            self.stdout.write(self.style.ERROR(f"  ✗ {errors} error(s) found:"))
            for error in issues["errors"]:
                self.stdout.write(f"    - {error}")

        if issues["warnings"]:
            self.stdout.write(self.style.WARNING(f"  ⚠ {warnings} warning(s) found:"))
            for warning in issues["warnings"]:
                self.stdout.write(f"    - {warning}")

        if not issues["errors"] and not issues["warnings"]:
            self.stdout.write(self.style.SUCCESS("  ✓ No issues found"))

        return errors, warnings

    def check_payment(self, payment_id, verbose=False, fix=False):
        """Check specific payment consistency."""
        self.stdout.write(f"\nChecking payment {payment_id}...")

        try:
            payment = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Payment {payment_id} not found"))
            return 1, 0

        issues = ConsistencyChecker.check_payment_consistency(payment_id)

        errors = len(issues["errors"])
        warnings = len(issues["warnings"])

        if issues["errors"]:
            self.stdout.write(self.style.ERROR(f"  ✗ {errors} error(s) found:"))
            for error in issues["errors"]:
                self.stdout.write(f"    - {error}")

        if issues["warnings"]:
            self.stdout.write(self.style.WARNING(f"  ⚠ {warnings} warning(s) found:"))
            for warning in issues["warnings"]:
                self.stdout.write(f"    - {warning}")

        if not issues["errors"] and not issues["warnings"]:
            self.stdout.write(self.style.SUCCESS("  ✓ No issues found"))

        return errors, warnings

    def check_motor(self, motor_id, verbose=False, fix=False):
        """Check specific motor consistency."""
        self.stdout.write(f"\nChecking motor {motor_id}...")

        try:
            motor = Motor.objects.get(id=motor_id)
        except Motor.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Motor {motor_id} not found"))
            return 1, 0

        issues = ConsistencyChecker.check_inventory_consistency(motor_id)

        errors = len(issues["errors"])
        warnings = len(issues["warnings"])

        if issues["errors"]:
            self.stdout.write(self.style.ERROR(f"  ✗ {errors} error(s) found:"))
            for error in issues["errors"]:
                self.stdout.write(f"    - {error}")

        if issues["warnings"]:
            self.stdout.write(self.style.WARNING(f"  ⚠ {warnings} warning(s) found:"))
            for warning in issues["warnings"]:
                self.stdout.write(f"    - {warning}")

        if not issues["errors"] and not issues["warnings"]:
            self.stdout.write(self.style.SUCCESS("  ✓ No issues found"))

        return errors, warnings

    def quick_check(self, verbose=False, fix=False):
        """Quick system check for critical issues."""
        self.stdout.write("Running quick consistency check...")

        total_errors = 0
        total_warnings = 0

        # Check for orphaned payments
        orphaned_payments = Payment.objects.filter(loan__isnull=True)
        if orphaned_payments.exists():
            count = orphaned_payments.count()
            self.stdout.write(
                self.style.ERROR(f"  ✗ Found {count} orphaned payment(s)")
            )
            total_errors += count

        # Check for loans without schedules
        loans_without_schedules = LoanApplication.objects.filter(
            status__in=["active", "approved"]
        ).exclude(paymentschedule__isnull=False)
        if loans_without_schedules.exists():
            count = loans_without_schedules.count()
            self.stdout.write(
                self.style.WARNING(
                    f"  ⚠ Found {count} loan(s) without payment schedules"
                )
            )
            total_warnings += count

        # Check for duplicate VINs
        from django.db.models import Count

        duplicate_vins = Motor.objects.values("vin").annotate(
            count=Count("id")
        ).filter(count__gt=1)
        if duplicate_vins.exists():
            count = duplicate_vins.count()
            self.stdout.write(
                self.style.ERROR(f"  ✗ Found {count} duplicate VIN(s)")
            )
            total_errors += count

        if total_errors == 0 and total_warnings == 0:
            self.stdout.write(self.style.SUCCESS("  ✓ Quick check passed"))

        return total_errors, total_warnings

    def check_all(self, verbose=False, fix=False):
        """Run comprehensive system check."""
        self.stdout.write("Running comprehensive consistency check...")

        issues = ConsistencyChecker.check_system_consistency()

        total_errors = len(issues["errors"])
        total_warnings = len(issues["warnings"])

        if issues["errors"]:
            self.stdout.write(
                self.style.ERROR(f"\n✗ {total_errors} error(s) found:")
            )
            for i, error in enumerate(issues["errors"][:20], 1):
                self.stdout.write(f"  {i}. {error}")
            if len(issues["errors"]) > 20:
                self.stdout.write(
                    f"  ... and {len(issues['errors']) - 20} more"
                )

        if issues["warnings"]:
            self.stdout.write(
                self.style.WARNING(f"\n⚠ {total_warnings} warning(s) found:")
            )
            for i, warning in enumerate(issues["warnings"][:20], 1):
                self.stdout.write(f"  {i}. {warning}")
            if len(issues["warnings"]) > 20:
                self.stdout.write(
                    f"  ... and {len(issues['warnings']) - 20} more"
                )

        if total_errors == 0 and total_warnings == 0:
            self.stdout.write(self.style.SUCCESS("\n✓ All checks passed"))

        return total_errors, total_warnings
