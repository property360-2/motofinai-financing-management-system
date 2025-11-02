from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from motofinai.apps.inventory.models import Motor
from motofinai.apps.loans.models import FinancingTerm, LoanApplication, PaymentSchedule
from motofinai.apps.risk.models import RiskAssessment
from motofinai.apps.users.models import User


class RiskAssessmentManagerTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="risk_officer",
            password="password123",
            role=User.Roles.FINANCE,
        )
        self.motor = Motor.objects.create(
            type="Underbone",
            brand="Honda",
            model_name="RS125",
            year=2023,
            purchase_price=Decimal("65000.00"),
        )
        self.term = FinancingTerm.objects.create(term_years=2, interest_rate=Decimal("10.00"))

    def create_application(self, **overrides) -> LoanApplication:
        defaults = {
            "applicant_first_name": "Ana",
            "applicant_last_name": "Lopez",
            "applicant_email": "ana@example.com",
            "applicant_phone": "09171234567",
            "employment_status": LoanApplication.EmploymentStatus.EMPLOYED,
            "monthly_income": Decimal("50000.00"),
            "motor": self.motor,
            "financing_term": self.term,
            "loan_amount": Decimal("65000.00"),
            "down_payment": Decimal("5000.00"),
            "principal_amount": Decimal("60000.00"),
            "interest_rate": self.term.interest_rate,
            "monthly_payment": Decimal("0.00"),
            "submitted_by": self.user,
        }
        defaults.update(overrides)
        loan = LoanApplication.objects.create(**defaults)
        loan.monthly_payment = loan.calculate_monthly_payment()
        loan.save(update_fields=["monthly_payment"])
        return loan

    def test_evaluate_for_loan_applies_formula(self):
        loan = self.create_application()
        loan.approve()

        overdue_schedules = loan.payment_schedules.order_by("sequence")[:2]
        for schedule in overdue_schedules:
            schedule.status = PaymentSchedule.Status.OVERDUE
            schedule.save(update_fields=["status"])

        assessment = RiskAssessment.objects.evaluate_for_loan(
            loan,
            base_score=30,
            credit_score=650,
        )

        expected_income_factor = Decimal("12.00")
        expected_credit_factor = Decimal("25.00")
        expected_score = 30 + (2 * 15) + expected_income_factor - expected_credit_factor

        self.assertEqual(assessment.missed_payments, 2)
        self.assertEqual(assessment.income_factor, expected_income_factor)
        self.assertEqual(assessment.credit_factor, expected_credit_factor)
        expected_dti = (
            loan.monthly_payment / loan.monthly_income * Decimal("100")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.assertEqual(assessment.debt_to_income_ratio, expected_dti)
        self.assertEqual(assessment.score, int(expected_score))
        self.assertEqual(assessment.risk_level, RiskAssessment.RiskLevel.MEDIUM)

    def test_evaluate_handles_low_income_and_unemployment(self):
        loan = self.create_application(
            employment_status=LoanApplication.EmploymentStatus.UNEMPLOYED,
            monthly_income=Decimal("0.00"),
        )
        loan.approve()
        first_schedule = loan.payment_schedules.order_by("sequence").first()
        assert first_schedule is not None
        first_schedule.status = PaymentSchedule.Status.OVERDUE
        first_schedule.save(update_fields=["status"])

        assessment = RiskAssessment.objects.evaluate_for_loan(
            loan,
            base_score=30,
            credit_score=500,
        )

        self.assertEqual(assessment.income_factor, Decimal("30.00"))
        self.assertEqual(assessment.debt_to_income_ratio, Decimal("100.00"))
        self.assertEqual(assessment.employment_penalty, RiskAssessment.EMPLOYMENT_PENALTIES[LoanApplication.EmploymentStatus.UNEMPLOYED])
        self.assertEqual(assessment.score, 75)
        self.assertEqual(assessment.risk_level, RiskAssessment.RiskLevel.HIGH)


class RiskAssessmentViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="risk_viewer",
            password="password123",
            role=User.Roles.FINANCE,
        )
        self.motor = Motor.objects.create(
            type="Scooter",
            brand="Yamaha",
            model_name="Mio",
            year=2024,
            purchase_price=Decimal("90000.00"),
        )
        self.term = FinancingTerm.objects.create(term_years=3, interest_rate=Decimal("12.00"))
        self.client.force_login(self.user)

    def create_assessed_application(self) -> RiskAssessment:
        loan = LoanApplication.objects.create(
            applicant_first_name="Ben",
            applicant_last_name="Castro",
            applicant_email="ben@example.com",
            applicant_phone="09181234567",
            employment_status=LoanApplication.EmploymentStatus.EMPLOYED,
            monthly_income=Decimal("45000.00"),
            motor=self.motor,
            financing_term=self.term,
            loan_amount=Decimal("90000.00"),
            down_payment=Decimal("10000.00"),
            principal_amount=Decimal("80000.00"),
            interest_rate=self.term.interest_rate,
            monthly_payment=Decimal("0.00"),
            submitted_by=self.user,
        )
        loan.monthly_payment = loan.calculate_monthly_payment()
        loan.save(update_fields=["monthly_payment"])
        loan.approve()
        return loan.evaluate_risk()

    def test_dashboard_displays_assessments(self):
        assessment = self.create_assessed_application()
        response = self.client.get(reverse("risk:dashboard"))
        self.assertContains(response, f"Application #{assessment.loan_application.pk}")
        self.assertContains(response, "Risk assessments")

    def test_recalculate_updates_credit_and_notes(self):
        assessment = self.create_assessed_application()
        url = reverse("risk:recalculate", args=[assessment.pk])
        response = self.client.post(
            url,
            data={
                "base_score": 35,
                "credit_score": 720,
                "notes": "Updated credit bureau pull",
            },
        )
        self.assertRedirects(response, reverse("risk:detail", args=[assessment.pk]))
        assessment.refresh_from_db()
        self.assertEqual(assessment.base_score, 35)
        self.assertEqual(assessment.credit_score, 720)
        self.assertEqual(assessment.notes, "Updated credit bureau pull")

    def test_generate_view_creates_assessment_for_pending_loan(self):
        loan = LoanApplication.objects.create(
            applicant_first_name="Carla",
            applicant_last_name="Diaz",
            applicant_email="carla@example.com",
            applicant_phone="09171239876",
            employment_status=LoanApplication.EmploymentStatus.SELF_EMPLOYED,
            monthly_income=Decimal("70000.00"),
            motor=self.motor,
            financing_term=self.term,
            loan_amount=Decimal("90000.00"),
            down_payment=Decimal("20000.00"),
            principal_amount=Decimal("70000.00"),
            interest_rate=self.term.interest_rate,
            monthly_payment=Decimal("0.00"),
            submitted_by=self.user,
        )
        loan.monthly_payment = loan.calculate_monthly_payment()
        loan.save(update_fields=["monthly_payment"])

        response = self.client.post(reverse("risk:evaluate-loan", args=[loan.pk]))
        assessment = RiskAssessment.objects.get(loan_application=loan)
        self.assertRedirects(response, reverse("risk:detail", args=[assessment.pk]))
        self.assertEqual(assessment.loan_application, loan)
