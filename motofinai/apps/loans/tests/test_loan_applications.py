from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from motofinai.apps.inventory.models import Motor
from motofinai.apps.loans.models import FinancingTerm, LoanApplication
from motofinai.apps.users.models import User


class LoanApplicationWizardTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            username="loan_admin",
            password="password123",
            role=User.Roles.ADMIN,
        )
        self.motor = Motor.objects.create(
            type="Scooter",
            brand="Yamaha",
            model_name="Mio Gear",
            year=2024,
            purchase_price=Decimal("85000.00"),
        )
        self.term = FinancingTerm.objects.create(term_years=2, interest_rate=Decimal("12.00"))
        self.client.force_login(self.admin)

    def test_wizard_creates_pending_application(self):
        url = reverse("loans:new")

        response = self.client.post(
            url,
            data={
                "current_step": "personal",
                "first_name": "Juan",
                "last_name": "Dela Cruz",
                "email": "juan@example.com",
                "phone": "+639171234567",
                "date_of_birth": "1990-05-12",
            },
        )
        self.assertRedirects(response, f"{url}?step=employment")

        response = self.client.post(
            f"{url}?step=employment",
            data={
                "current_step": "employment",
                "employment_status": LoanApplication.EmploymentStatus.EMPLOYED,
                "employer_name": "Motofin Corp",
                "monthly_income": "45000",
            },
        )
        self.assertRedirects(response, f"{url}?step=motor")

        response = self.client.post(
            f"{url}?step=motor",
            data={
                "current_step": "motor",
                "motor": str(self.motor.pk),
                "financing_term": str(self.term.pk),
                "down_payment": "5000",
            },
        )
        self.assertRedirects(response, f"{url}?step=documents")

        response = self.client.post(
            f"{url}?step=documents",
            data={
                "current_step": "documents",
                "has_valid_id": True,
                "has_proof_of_income": True,
                "notes": "Verified employment in person.",
            },
        )
        application = LoanApplication.objects.first()
        self.assertIsNotNone(application)
        assert application is not None
        detail_url = reverse("loans:detail", args=[application.pk])
        self.assertRedirects(response, detail_url)
        self.assertEqual(application.status, LoanApplication.Status.PENDING)
        self.assertEqual(application.loan_amount, Decimal("85000.00"))
        self.assertEqual(application.down_payment, Decimal("5000.00"))
        self.assertGreater(application.monthly_payment, Decimal("0"))

    def test_approval_generates_payment_schedule(self):
        application = LoanApplication.objects.create(
            applicant_first_name="Maria",
            applicant_last_name="Santos",
            applicant_email="maria@example.com",
            applicant_phone="09171234567",
            employment_status=LoanApplication.EmploymentStatus.EMPLOYED,
            monthly_income=Decimal("55000.00"),
            motor=self.motor,
            financing_term=self.term,
            loan_amount=Decimal("85000.00"),
            down_payment=Decimal("5000.00"),
            principal_amount=Decimal("80000.00"),
            interest_rate=self.term.interest_rate,
            monthly_payment=Decimal("0.00"),
            submitted_by=self.admin,
        )
        application.monthly_payment = application.calculate_monthly_payment()
        application.save()

        response = self.client.post(reverse("loans:approve", args=[application.pk]))
        self.assertRedirects(response, reverse("loans:detail", args=[application.pk]))
        application.refresh_from_db()
        self.assertEqual(application.status, LoanApplication.Status.APPROVED)
        self.assertEqual(application.payment_schedules.count(), self.term.total_months)
        first_schedule = application.payment_schedules.order_by("sequence").first()
        assert first_schedule is not None
        self.assertEqual(first_schedule.sequence, 1)
        self.assertGreater(first_schedule.total_amount, Decimal("0"))
        schedules = list(application.payment_schedules.order_by("sequence"))
        total_principal = sum(item.principal_amount for item in schedules)
        total_interest = sum(item.interest_amount for item in schedules)
        total_amount = sum(item.total_amount for item in schedules)
        self.assertEqual(total_principal, application.principal_amount)
        expected_interest = (
            application.principal_amount
            * (application.interest_rate / Decimal("100"))
            * Decimal(self.term.term_years)
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.assertEqual(total_interest, expected_interest)
        self.assertEqual(total_amount, application.principal_amount + expected_interest)
        self.assertTrue(
            all(
                schedule.total_amount == application.monthly_payment
                for schedule in schedules[:-1]
            )
        )

    def test_activation_and_completion(self):
        application = LoanApplication.objects.create(
            applicant_first_name="Lito",
            applicant_last_name="Fernandez",
            applicant_email="lito@example.com",
            applicant_phone="09175555555",
            employment_status=LoanApplication.EmploymentStatus.SELF_EMPLOYED,
            monthly_income=Decimal("60000.00"),
            motor=self.motor,
            financing_term=self.term,
            loan_amount=Decimal("85000.00"),
            down_payment=Decimal("0.00"),
            principal_amount=Decimal("85000.00"),
            interest_rate=self.term.interest_rate,
            monthly_payment=Decimal("0.00"),
            submitted_by=self.admin,
        )
        application.monthly_payment = application.calculate_monthly_payment()
        application.save()
        application.approve()

        response = self.client.post(reverse("loans:activate", args=[application.pk]))
        self.assertRedirects(response, reverse("loans:detail", args=[application.pk]))
        application.refresh_from_db()
        self.assertEqual(application.status, LoanApplication.Status.ACTIVE)

        response = self.client.post(reverse("loans:complete", args=[application.pk]))
        self.assertRedirects(response, reverse("loans:detail", args=[application.pk]))
        application.refresh_from_db()
        self.assertEqual(application.status, LoanApplication.Status.COMPLETED)

    def test_simple_interest_formula_is_used(self):
        application = LoanApplication.objects.create(
            applicant_first_name="Ana",
            applicant_last_name="Lopez",
            applicant_email="ana@example.com",
            applicant_phone="09171231234",
            employment_status=LoanApplication.EmploymentStatus.EMPLOYED,
            monthly_income=Decimal("70000.00"),
            motor=self.motor,
            financing_term=self.term,
            loan_amount=Decimal("90000.00"),
            down_payment=Decimal("10000.00"),
            principal_amount=Decimal("80000.00"),
            interest_rate=self.term.interest_rate,
            monthly_payment=Decimal("0.00"),
            submitted_by=self.admin,
        )
        expected_payment = (
            (
                application.principal_amount
                + application.principal_amount
                * (application.interest_rate / Decimal("100"))
                * Decimal(self.term.term_years)
            )
            / Decimal(self.term.total_months)
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.assertEqual(application.calculate_monthly_payment(), expected_payment)
