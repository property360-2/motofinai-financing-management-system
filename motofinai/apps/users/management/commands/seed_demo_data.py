"""
Seed comprehensive demo data for the DC Financing Corporation financing system.

This command populates the database with realistic test data including:
- Test users with different roles (admin, finance)
- Financing terms
- Motorcycle inventory
- Sample loan applications with various statuses
- Payment schedules and payments
- Risk assessments
- Repossession cases
"""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from motofinai.apps.inventory.models import Motor
from motofinai.apps.loans.models import FinancingTerm, LoanApplication
from motofinai.apps.payments.models import Payment


User = get_user_model()


class Command(BaseCommand):
    help = "Seed demo data for the DC Financing Corporation system including users, inventory, loans, and payments."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing demo data before seeding (WARNING: Destructive)",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write(self.style.WARNING("Clearing existing demo data..."))
            self._clear_demo_data()

        self.stdout.write(self.style.NOTICE("Starting demo data seeding..."))

        # Seed in order of dependencies
        users = self._seed_users()
        financing_terms = self._seed_financing_terms()
        motors = self._seed_motors()
        loans = self._seed_loan_applications(users, motors, financing_terms)
        self._seed_payments(loans, users)

        self.stdout.write(self.style.SUCCESS("\n[OK] Demo data seeding completed successfully!"))
        self.stdout.write(self.style.SUCCESS("\nLogin credentials:"))
        self.stdout.write("  Admin User:")
        self.stdout.write("    Username: admin_demo | Password: Demo123456!")
        self.stdout.write("  Finance User:")
        self.stdout.write("    Username: finance_demo | Password: Demo123456!")
        self.stdout.write("  Finance Manager:")
        self.stdout.write("    Username: finance_manager | Password: Demo123456!")

    def _clear_demo_data(self):
        """Clear demo data (keeping superusers)."""
        # Delete dependent data first to avoid protected foreign key errors
        Payment.objects.all().delete()
        LoanApplication.objects.all().delete()
        Motor.objects.all().delete()
        FinancingTerm.objects.all().delete()
        # Now delete users
        User.objects.filter(username__contains="demo").delete()
        User.objects.filter(username__contains="finance_").delete()
        User.objects.filter(username__contains="credit_").delete()
        self.stdout.write(self.style.SUCCESS("  [OK] Demo data cleared"))

    def _seed_users(self):
        """Create test users with different roles."""
        self.stdout.write("\n1. Seeding users...")

        users = {}

        # Admin user
        admin, created = User.objects.get_or_create(
            username="admin_demo",
            defaults={
                "email": "admin@dcfinancing.demo",
                "first_name": "Admin",
                "last_name": "User",
                "role": User.Roles.ADMIN,
                "is_staff": True,
                "is_active": True,
            },
        )
        if created:
            admin.set_password("Demo123456!")
            admin.save()
            self.stdout.write(f"  [OK] Created admin user: {admin.username}")
        else:
            self.stdout.write(f"  -> Admin user already exists: {admin.username}")
        users["admin"] = admin

        # Finance users
        finance_user, created = User.objects.get_or_create(
            username="finance_demo",
            defaults={
                "email": "finance@dcfinancing.demo",
                "first_name": "Finance",
                "last_name": "User",
                "role": User.Roles.FINANCE,
                "is_staff": False,
                "is_active": True,
            },
        )
        if created:
            finance_user.set_password("Demo123456!")
            finance_user.save()
            self.stdout.write(f"  [OK] Created finance user: {finance_user.username}")
        else:
            self.stdout.write(f"  -> Finance user already exists: {finance_user.username}")
        users["finance"] = finance_user

        # Finance manager
        finance_manager, created = User.objects.get_or_create(
            username="finance_manager",
            defaults={
                "email": "manager@dcfinancing.demo",
                "first_name": "Maria",
                "last_name": "Santos",
                "role": User.Roles.FINANCE,
                "is_staff": False,
                "is_active": True,
            },
        )
        if created:
            finance_manager.set_password("Demo123456!")
            finance_manager.save()
            self.stdout.write(f"  [OK] Created finance manager: {finance_manager.username}")
        else:
            self.stdout.write(f"  -> Finance manager already exists: {finance_manager.username}")
        users["finance_manager"] = finance_manager

        return users

    def _seed_financing_terms(self):
        """Create financing term options."""
        self.stdout.write("\n2. Seeding financing terms...")

        terms_data = [
            {"term_years": 1, "interest_rate": Decimal("8.50")},
            {"term_years": 2, "interest_rate": Decimal("10.00")},
            {"term_years": 3, "interest_rate": Decimal("12.50")},
            {"term_years": 4, "interest_rate": Decimal("14.00")},
            {"term_years": 5, "interest_rate": Decimal("15.50")},
        ]

        terms = []
        for term_data in terms_data:
            term, created = FinancingTerm.objects.get_or_create(
                term_years=term_data["term_years"],
                interest_rate=term_data["interest_rate"],
                defaults={"is_active": True},
            )
            if created:
                self.stdout.write(f"  [OK] Created financing term: {term}")
            else:
                self.stdout.write(f"  -> Financing term already exists: {term}")
            terms.append(term)

        return terms

    def _seed_motors(self):
        """Create motorcycle inventory."""
        self.stdout.write("\n3. Seeding motorcycle inventory...")

        motors_data = [
            {
                "type": "scooter",
                "brand": "Honda",
                "model_name": "Click 160",
                "year": 2024,
                "color": "Red",
                "purchase_price": Decimal("89000.00"),
            },
            {
                "type": "underbone",
                "brand": "Honda",
                "model_name": "Wave 125",
                "year": 2024,
                "color": "Black",
                "purchase_price": Decimal("75000.00"),
            },
            {
                "type": "sport",
                "brand": "Yamaha",
                "model_name": "Sniper 155",
                "year": 2024,
                "color": "Blue",
                "purchase_price": Decimal("95000.00"),
            },
            {
                "type": "scooter",
                "brand": "Yamaha",
                "model_name": "NMAX 155",
                "year": 2024,
                "color": "White",
                "purchase_price": Decimal("125000.00"),
            },
            {
                "type": "underbone",
                "brand": "Suzuki",
                "model_name": "Raider 150",
                "year": 2023,
                "color": "Orange",
                "purchase_price": Decimal("82000.00"),
            },
            {
                "type": "sport",
                "brand": "Kawasaki",
                "model_name": "Ninja 400",
                "year": 2024,
                "color": "Green",
                "purchase_price": Decimal("350000.00"),
            },
            {
                "type": "scooter",
                "brand": "Honda",
                "model_name": "ADV 150",
                "year": 2024,
                "color": "Gray",
                "purchase_price": Decimal("165000.00"),
            },
            {
                "type": "underbone",
                "brand": "Yamaha",
                "model_name": "Mio i125",
                "year": 2023,
                "color": "Pink",
                "purchase_price": Decimal("78000.00"),
            },
            {
                "type": "sport",
                "brand": "Honda",
                "model_name": "CBR150R",
                "year": 2024,
                "color": "Red",
                "purchase_price": Decimal("185000.00"),
            },
            {
                "type": "scooter",
                "brand": "Suzuki",
                "model_name": "Burgman 125",
                "year": 2024,
                "color": "Silver",
                "purchase_price": Decimal("110000.00"),
            },
        ]

        motors = []
        for motor_data in motors_data:
            motor, created = Motor.objects.get_or_create(
                brand=motor_data["brand"],
                model_name=motor_data["model_name"],
                year=motor_data["year"],
                defaults={
                    "type": motor_data["type"],
                    "color": motor_data["color"],
                    "purchase_price": motor_data["purchase_price"],
                },
            )
            if created:
                self.stdout.write(f"  [OK] Created motor: {motor}")
            else:
                self.stdout.write(f"  -> Motor already exists: {motor}")
            motors.append(motor)

        return motors

    def _seed_loan_applications(self, users, motors, financing_terms):
        """Create sample loan applications with various statuses."""
        self.stdout.write("\n4. Seeding loan applications...")

        # Get available motors and terms
        term_3yr = next(t for t in financing_terms if t.term_years == 3)
        term_2yr = next(t for t in financing_terms if t.term_years == 2)
        term_5yr = next(t for t in financing_terms if t.term_years == 5)

        loans_data = [
            # Active loan with some payments
            {
                "applicant_first_name": "Juan",
                "applicant_last_name": "Dela Cruz",
                "applicant_email": "juan.delacruz@example.com",
                "applicant_phone": "+63 917 123 4567",
                "date_of_birth": date(1990, 5, 15),
                "employment_status": LoanApplication.EmploymentStatus.EMPLOYED,
                "employer_name": "ABC Corporation",
                "monthly_income": Decimal("35000.00"),
                "motor": motors[3],  # Yamaha NMAX (SOLD)
                "financing_term": term_3yr,
                "loan_amount": Decimal("125000.00"),
                "down_payment": Decimal("25000.00"),
                "has_valid_id": True,
                "has_proof_of_income": True,
                "status": LoanApplication.Status.ACTIVE,
                "submitted_by": users["finance"],
                "submitted_at": timezone.now() - timedelta(days=90),
            },
            # Pending loan application
            {
                "applicant_first_name": "Maria",
                "applicant_last_name": "Santos",
                "applicant_email": "maria.santos@example.com",
                "applicant_phone": "+63 918 234 5678",
                "date_of_birth": date(1995, 8, 20),
                "employment_status": LoanApplication.EmploymentStatus.EMPLOYED,
                "employer_name": "XYZ Industries",
                "monthly_income": Decimal("28000.00"),
                "motor": motors[0],  # Honda Click 160 (AVAILABLE)
                "financing_term": term_2yr,
                "loan_amount": Decimal("89000.00"),
                "down_payment": Decimal("20000.00"),
                "has_valid_id": True,
                "has_proof_of_income": False,
                "status": LoanApplication.Status.PENDING,
                "submitted_by": users["finance_manager"],
                "submitted_at": timezone.now() - timedelta(days=5),
            },
            # Approved loan (ready to activate)
            {
                "applicant_first_name": "Pedro",
                "applicant_last_name": "Garcia",
                "applicant_email": "pedro.garcia@example.com",
                "applicant_phone": "+63 919 345 6789",
                "date_of_birth": date(1988, 12, 10),
                "employment_status": LoanApplication.EmploymentStatus.SELF_EMPLOYED,
                "employer_name": "Garcia Auto Parts",
                "monthly_income": Decimal("45000.00"),
                "motor": motors[4],  # Suzuki Raider (RESERVED)
                "financing_term": term_2yr,
                "loan_amount": Decimal("82000.00"),
                "down_payment": Decimal("15000.00"),
                "has_valid_id": True,
                "has_proof_of_income": True,
                "status": LoanApplication.Status.APPROVED,
                "submitted_by": users["finance"],
                "submitted_at": timezone.now() - timedelta(days=15),
            },
            # Active loan with overdue payments
            {
                "applicant_first_name": "Jose",
                "applicant_last_name": "Reyes",
                "applicant_email": "jose.reyes@example.com",
                "applicant_phone": "+63 920 456 7890",
                "date_of_birth": date(1992, 3, 25),
                "employment_status": LoanApplication.EmploymentStatus.EMPLOYED,
                "employer_name": "DEF Company",
                "monthly_income": Decimal("25000.00"),
                "motor": motors[7],  # Yamaha Mio (SOLD)
                "financing_term": term_3yr,
                "loan_amount": Decimal("78000.00"),
                "down_payment": Decimal("10000.00"),
                "has_valid_id": True,
                "has_proof_of_income": True,
                "status": LoanApplication.Status.ACTIVE,
                "submitted_by": users["finance_manager"],
                "submitted_at": timezone.now() - timedelta(days=180),
            },
            # Recently completed loan
            {
                "applicant_first_name": "Ana",
                "applicant_last_name": "Lopez",
                "applicant_email": "ana.lopez@example.com",
                "applicant_phone": "+63 921 567 8901",
                "date_of_birth": date(1993, 7, 8),
                "employment_status": LoanApplication.EmploymentStatus.EMPLOYED,
                "employer_name": "GHI Services",
                "monthly_income": Decimal("32000.00"),
                "motor": Motor.objects.get_or_create(
                    brand="Honda",
                    model_name="Beat 110",
                    year=2022,
                    defaults={
                        "type": "scooter",
                        "color": "White",
                        "purchase_price": Decimal("58000.00"),
                    }
                )[0],
                "financing_term": term_2yr,
                "loan_amount": Decimal("58000.00"),
                "down_payment": Decimal("8000.00"),
                "has_valid_id": True,
                "has_proof_of_income": True,
                "status": LoanApplication.Status.COMPLETED,
                "submitted_by": users["finance"],
                "submitted_at": timezone.now() - timedelta(days=800),
            },
        ]

        loans = []
        for loan_data in loans_data:
            # Calculate principal and monthly payment
            principal_amount = loan_data["loan_amount"] - loan_data["down_payment"]
            interest_rate = loan_data["financing_term"].interest_rate

            # Simple interest calculation
            term_years = Decimal(loan_data["financing_term"].term_years)
            total_interest = (principal_amount * (interest_rate / Decimal("100")) * term_years).quantize(
                Decimal("0.01")
            )
            total_amount = principal_amount + total_interest
            monthly_payment = (total_amount / Decimal(loan_data["financing_term"].total_months)).quantize(
                Decimal("0.01")
            )

            loan_defaults = {
                "principal_amount": principal_amount,
                "interest_rate": interest_rate,
                "monthly_payment": monthly_payment,
            }
            loan_defaults.update(loan_data)
            status = loan_defaults.pop("status")

            # Check if loan already exists
            existing = LoanApplication.objects.filter(
                applicant_email=loan_data["applicant_email"],
                motor=loan_data["motor"],
            ).first()

            if existing:
                self.stdout.write(f"  -> Loan already exists for {loan_data['applicant_first_name']} {loan_data['applicant_last_name']}")
                loans.append(existing)
                continue

            # Create the loan
            loan = LoanApplication.objects.create(**loan_defaults)

            # Update status through proper workflow
            if status in [LoanApplication.Status.APPROVED, LoanApplication.Status.ACTIVE, LoanApplication.Status.COMPLETED]:
                # First approval
                loan.approve(approved_by=users.get("finance"))
                loan.approved_at = loan.submitted_at + timedelta(days=1)

                # Second approval (for testing, set both approvals)
                second_approver = users.get("admin")
                loan.second_approval_by = second_approver
                loan.second_approval_at = loan.submitted_at + timedelta(days=2)
                loan.save()

            if status in [LoanApplication.Status.ACTIVE, LoanApplication.Status.COMPLETED]:
                loan.activate()
                loan.activated_at = loan.submitted_at + timedelta(days=5)
                loan.save()

            if status == LoanApplication.Status.COMPLETED:
                loan.complete()
                loan.completed_at = loan.submitted_at + timedelta(days=730)  # 2 years later
                loan.save()

            self.stdout.write(f"  [OK] Created loan application: {loan.applicant_full_name} - {loan.motor}")
            loans.append(loan)

        return loans

    def _seed_payments(self, loans, users):
        """Create sample payments for active loans."""
        self.stdout.write("\n5. Seeding payments...")

        payment_count = 0

        for loan in loans:
            if loan.status not in [LoanApplication.Status.ACTIVE, LoanApplication.Status.COMPLETED]:
                continue

            schedules = loan.payment_schedules.order_by("sequence")

            # For active loans, pay some installments
            if loan.status == LoanApplication.Status.ACTIVE:
                num_payments = min(3, schedules.count())  # Pay first 3 installments

                for schedule in schedules[:num_payments]:
                    # Check if payment already exists
                    if hasattr(schedule, "payment"):
                        continue

                    payment = Payment.objects.create(
                        loan_application=loan,
                        schedule=schedule,
                        amount=schedule.total_amount,
                        payment_date=schedule.due_date,
                        reference=f"PAY-{loan.id}-{schedule.sequence:03d}",
                        recorded_by=users["finance"],
                    )
                    payment_count += 1
                    self.stdout.write(f"  [OK] Created payment: {payment.reference}")

            # For completed loans, mark all as paid
            elif loan.status == LoanApplication.Status.COMPLETED:
                for schedule in schedules:
                    if hasattr(schedule, "payment"):
                        continue

                    payment = Payment.objects.create(
                        loan_application=loan,
                        schedule=schedule,
                        amount=schedule.total_amount,
                        payment_date=schedule.due_date,
                        reference=f"PAY-{loan.id}-{schedule.sequence:03d}",
                        recorded_by=users["finance"],
                    )
                    payment_count += 1

        if payment_count > 0:
            self.stdout.write(f"  [OK] Created {payment_count} payment(s)")
        else:
            self.stdout.write("  -> No payments needed")
