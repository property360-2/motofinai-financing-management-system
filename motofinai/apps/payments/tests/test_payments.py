from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from motofinai.apps.inventory.models import Motor
from motofinai.apps.loans.models import FinancingTerm, LoanApplication, PaymentSchedule
from motofinai.apps.users.models import User


class PaymentWorkflowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="finance_user",
            password="password123",
            role=User.Roles.FINANCE,
        )
        self.client.force_login(self.user)
        self.motor = Motor.objects.create(
            type="Scooter",
            brand="Yamaha",
            model_name="Aerox",
            year=2024,
            purchase_price=Decimal("95000.00"),
        )
        self.term = FinancingTerm.objects.create(term_years=2, interest_rate=Decimal("12.00"))
        self.application = LoanApplication.objects.create(
            applicant_first_name="Alex",
            applicant_last_name="Reyes",
            applicant_email="alex@example.com",
            applicant_phone="09171234567",
            employment_status=LoanApplication.EmploymentStatus.EMPLOYED,
            monthly_income=Decimal("55000.00"),
            motor=self.motor,
            financing_term=self.term,
            loan_amount=self.motor.purchase_price,
            down_payment=Decimal("5000.00"),
            principal_amount=self.motor.purchase_price - Decimal("5000.00"),
            interest_rate=self.term.interest_rate,
            monthly_payment=Decimal("0.00"),
            submitted_by=self.user,
        )
        self.application.update_monthly_payment()
        self.application.save()
        self.application.approve()
        self.application.activate()

    def test_overdue_schedules_are_flagged(self):
        schedule = self.application.payment_schedules.order_by("sequence").first()
        assert schedule is not None
        schedule.due_date = timezone.now().date() - timedelta(days=10)
        schedule.status = PaymentSchedule.Status.DUE
        schedule.save(update_fields=["due_date", "status"])

        response = self.client.get(reverse("payments:schedule-list"))
        self.assertEqual(response.status_code, 200)
        schedule.refresh_from_db()
        self.assertEqual(schedule.status, PaymentSchedule.Status.OVERDUE)
        summary = response.context["summary"]
        self.assertEqual(summary["overdue_count"], 1)
        self.assertEqual(summary["overdue_total"], schedule.total_amount)
        self.assertContains(response, "Overdue")

    def test_recording_payment_marks_schedule_paid(self):
        schedule = self.application.payment_schedules.order_by("sequence").first()
        assert schedule is not None
        url = reverse("payments:record-payment", args=[schedule.pk])
        payload = {
            "amount": schedule.total_amount,
            "payment_date": timezone.localdate().isoformat(),
            "reference": "OR-0001",
            "notes": "Paid in cash",
        }
        response = self.client.post(url, data=payload)
        self.assertRedirects(response, reverse("payments:schedule-list"))
        schedule.refresh_from_db()
        self.assertEqual(schedule.status, PaymentSchedule.Status.PAID)
        payment = schedule.payment
        self.assertEqual(payment.amount, schedule.total_amount)
        self.assertEqual(payment.recorded_by, self.user)
        self.assertEqual(payment.reference, "OR-0001")

    def test_recording_incorrect_amount_shows_error(self):
        schedule = self.application.payment_schedules.order_by("sequence").first()
        assert schedule is not None
        url = reverse("payments:record-payment", args=[schedule.pk])
        response = self.client.post(
            url,
            data={
                "amount": schedule.total_amount - Decimal("100.00"),
                "payment_date": timezone.localdate().isoformat(),
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertContains(
            response,
            "Amount must match the scheduled installment total",
            status_code=400,
        )
        schedule.refresh_from_db()
        self.assertEqual(schedule.status, PaymentSchedule.Status.DUE)

    def test_paying_all_installments_completes_active_loan(self):
        schedules = list(self.application.payment_schedules.order_by("sequence"))
        for schedule in schedules:
            url = reverse("payments:record-payment", args=[schedule.pk])
            response = self.client.post(
                url,
                data={
                    "amount": schedule.total_amount,
                    "payment_date": (timezone.localdate() + timedelta(days=schedule.sequence)).isoformat(),
                    "reference": f"RCPT-{schedule.sequence:02d}",
                },
            )
            self.assertRedirects(response, reverse("payments:schedule-list"))
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, LoanApplication.Status.COMPLETED)
        self.assertIsNotNone(self.application.completed_at)
