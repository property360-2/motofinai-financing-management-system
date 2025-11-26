from decimal import Decimal
from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone

from motofinai.apps.users.models import User
from motofinai.apps.inventory.models import Stock, Motor
from motofinai.apps.loans.models import FinancingTerm, LoanApplication, PaymentSchedule
from motofinai.apps.payments.models import Payment
from motofinai.apps.repossession.models import RepossessionCase
from motofinai.apps.risk.models import RiskAssessment
from motofinai.apps.dashboard.kpi import DashboardKPI


class DashboardKPITest(TestCase):
    """Tests for Dashboard KPI calculations."""

    def setUp(self):
        """Create test data."""
        # Create test users
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="password",
            role="admin"
        )

        self.finance_user = User.objects.create_user(
            username="finance",
            email="finance@test.com",
            password="password",
            role="finance"
        )

        # Create financing term
        self.financing_term = FinancingTerm.objects.create(
            term_years=2,
            interest_rate=Decimal("12.00")
        )

        # Create stock and motor
        self.stock = Stock.objects.create(
            brand="Yamaha",
            model_name="Mio",
            year=2024,
            quantity_available=10
        )

        self.motor = Motor.objects.create(
            type=Motor.Type.SCOOTER,
            brand="Yamaha",
            model_name="Mio",
            year=2024,
            chassis_number="TEST123",
            stock=self.stock,
            purchase_price=Decimal("75000.00"),
            approval_status=Motor.ApprovalStatus.APPROVED
        )

    def test_get_loan_kpis_with_various_statuses(self):
        """Test that loan KPIs correctly count loans with different statuses."""
        # Create loans with different statuses
        LoanApplication.objects.create(
            applicant_first_name="Pending",
            applicant_last_name="Applicant",
            applicant_email="pending@test.com",
            applicant_phone="09123456789",
            employment_status="employed",
            monthly_income=Decimal("30000.00"),
            motor=self.motor,
            financing_term=self.financing_term,
            loan_amount=Decimal("75000.00"),
            down_payment=Decimal("15000.00"),
            principal_amount=Decimal("60000.00"),
            interest_rate=Decimal("12.00"),
            monthly_payment=Decimal("2500.00"),
            submitted_by=self.admin_user,
            status='pending'  # Use valid status
        )

        LoanApplication.objects.create(
            applicant_first_name="Approved",
            applicant_last_name="Applicant",
            applicant_email="approved@test.com",
            applicant_phone="09123456780",
            employment_status="employed",
            monthly_income=Decimal("30000.00"),
            motor=self.motor,
            financing_term=self.financing_term,
            loan_amount=Decimal("80000.00"),
            down_payment=Decimal("16000.00"),
            principal_amount=Decimal("64000.00"),
            interest_rate=Decimal("12.00"),
            monthly_payment=Decimal("2667.00"),
            submitted_by=self.admin_user,
            status='approved'  # Use valid status
        )

        kpis = DashboardKPI.get_loan_kpis()

        self.assertEqual(kpis['total_loans'], 2)
        self.assertEqual(kpis['pending_loans'], 1)
        self.assertEqual(kpis['approved_loans'], 1)
        self.assertEqual(kpis['active_loans'], 0)
        self.assertEqual(kpis['completed_loans'], 0)

    def test_get_payment_kpis_uses_correct_status_values(self):
        """Test that payment KPIs use correct PaymentSchedule status values."""
        # Create a loan
        loan = LoanApplication.objects.create(
            applicant_first_name="Test",
            applicant_last_name="Applicant",
            applicant_email="test@test.com",
            applicant_phone="09123456789",
            employment_status="employed",
            monthly_income=Decimal("30000.00"),
            motor=self.motor,
            financing_term=self.financing_term,
            loan_amount=Decimal("75000.00"),
            down_payment=Decimal("15000.00"),
            principal_amount=Decimal("60000.00"),
            interest_rate=Decimal("12.00"),
            monthly_payment=Decimal("2500.00"),
            submitted_by=self.admin_user,
            status='active'
        )

        # Create payment schedules with correct status values
        today = timezone.now().date()

        # Due payment (this month)
        PaymentSchedule.objects.create(
            loan_application=loan,
            sequence=1,
            due_date=today + timedelta(days=5),
            principal_amount=Decimal("2500.00"),
            interest_amount=Decimal("500.00"),
            total_amount=Decimal("3000.00"),
            status='due'  # Correct status value
        )

        # Overdue payment
        PaymentSchedule.objects.create(
            loan_application=loan,
            sequence=2,
            due_date=today - timedelta(days=10),
            principal_amount=Decimal("2500.00"),
            interest_amount=Decimal("500.00"),
            total_amount=Decimal("3000.00"),
            status='overdue'  # Correct status value
        )

        # Paid payment
        PaymentSchedule.objects.create(
            loan_application=loan,
            sequence=3,
            due_date=today - timedelta(days=5),
            principal_amount=Decimal("2500.00"),
            interest_amount=Decimal("500.00"),
            total_amount=Decimal("3000.00"),
            status='paid'  # Correct status value
        )

        # Get payment KPIs - should not raise errors with correct status values
        kpis = DashboardKPI.get_payment_kpis()

        # Verify KPIs are calculated
        self.assertIn('pending_amount', kpis)
        self.assertIn('overdue_amount', kpis)
        self.assertIn('overdue_count', kpis)

        # Verify overdue calculations use correct status
        self.assertEqual(kpis['overdue_count'], 1)
        self.assertEqual(kpis['overdue_amount'], Decimal('3000.00'))

    def test_payment_kpis_collection_rate_calculation(self):
        """Test payment collection rate calculation."""
        # Create a loan
        loan = LoanApplication.objects.create(
            applicant_first_name="Test",
            applicant_last_name="Applicant",
            applicant_email="test@test.com",
            applicant_phone="09123456789",
            employment_status="employed",
            monthly_income=Decimal("30000.00"),
            motor=self.motor,
            financing_term=self.financing_term,
            loan_amount=Decimal("75000.00"),
            down_payment=Decimal("15000.00"),
            principal_amount=Decimal("60000.00"),
            interest_rate=Decimal("12.00"),
            monthly_payment=Decimal("2500.00"),
            submitted_by=self.admin_user,
            status='active'
        )

        today = timezone.now().date()
        month_start = today.replace(day=1)

        # Create a due schedule (not yet paid)
        schedule = PaymentSchedule.objects.create(
            loan_application=loan,
            sequence=1,
            due_date=month_start + timedelta(days=5),
            principal_amount=Decimal("2500.00"),
            interest_amount=Decimal("500.00"),
            total_amount=Decimal("3000.00"),
            status='due'  # Start as due, payment will mark it as paid
        )

        # Record payment (this will automatically mark schedule as paid)
        Payment.objects.create(
            schedule=schedule,
            amount=Decimal("3000.00"),
            payment_date=today,
            recorded_by=self.admin_user
        )

        kpis = DashboardKPI.get_payment_kpis()

        # Verify collection was recorded
        self.assertEqual(kpis['total_collected'], Decimal('3000.00'))

        # Collection rate should be positive
        self.assertGreater(kpis['collection_rate'], Decimal('0'))

    def test_loan_kpis_total_loan_value_calculation(self):
        """Test total loan value calculation."""
        # Create approved loans
        LoanApplication.objects.create(
            applicant_first_name="Applicant",
            applicant_last_name="One",
            applicant_email="app1@test.com",
            applicant_phone="09123456781",
            employment_status="employed",
            monthly_income=Decimal("30000.00"),
            motor=self.motor,
            financing_term=self.financing_term,
            loan_amount=Decimal("50000.00"),
            down_payment=Decimal("10000.00"),
            principal_amount=Decimal("40000.00"),
            interest_rate=Decimal("12.00"),
            monthly_payment=Decimal("1667.00"),
            submitted_by=self.admin_user,
            status='approved'
        )

        LoanApplication.objects.create(
            applicant_first_name="Applicant",
            applicant_last_name="Two",
            applicant_email="app2@test.com",
            applicant_phone="09123456782",
            employment_status="employed",
            monthly_income=Decimal("30000.00"),
            motor=self.motor,
            financing_term=self.financing_term,
            loan_amount=Decimal("60000.00"),
            down_payment=Decimal("12000.00"),
            principal_amount=Decimal("48000.00"),
            interest_rate=Decimal("12.00"),
            monthly_payment=Decimal("2000.00"),
            submitted_by=self.admin_user,
            status='active'
        )

        kpis = DashboardKPI.get_loan_kpis()

        # Total loan value should be sum of approved + active loans
        self.assertEqual(kpis['total_loan_value'], Decimal('110000.00'))
        self.assertEqual(kpis['avg_loan_amount'], Decimal('55000.00'))

    def test_kpis_with_no_data(self):
        """Test that KPIs handle empty database gracefully."""
        kpis = DashboardKPI.get_loan_kpis()

        self.assertEqual(kpis['total_loans'], 0)
        self.assertEqual(kpis['total_loan_value'], Decimal('0'))
        self.assertEqual(kpis['avg_loan_amount'], Decimal('0'))

        payment_kpis = DashboardKPI.get_payment_kpis()

        self.assertEqual(payment_kpis['total_collected'], Decimal('0'))
        self.assertEqual(payment_kpis['pending_amount'], Decimal('0'))
        self.assertEqual(payment_kpis['overdue_amount'], Decimal('0'))
        self.assertEqual(payment_kpis['overdue_count'], 0)
        self.assertEqual(payment_kpis['collection_rate'], Decimal('0'))
