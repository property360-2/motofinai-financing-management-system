from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from motofinai.apps.inventory.models import Motor
from motofinai.apps.loans.models import FinancingTerm, LoanApplication, PaymentSchedule
from motofinai.apps.repossession.models import RepossessionCase, RepossessionEvent
from motofinai.apps.users.models import User


class RepossessionCaseWorkflowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="finance_user",
            password="securepass123",
            role=User.Roles.FINANCE,
        )
        self.client.force_login(self.user)
        self.motor = Motor.objects.create(
            type="Scooter",
            brand="Honda",
            model_name="Click 150",
            year=2024,
            purchase_price=Decimal("98500.00"),
        )
        self.term = FinancingTerm.objects.create(term_years=2, interest_rate=Decimal("12.00"))
        self.application = LoanApplication.objects.create(
            applicant_first_name="Jamie",
            applicant_last_name="Santos",
            applicant_email="jamie@example.com",
            applicant_phone="09171234568",
            employment_status=LoanApplication.EmploymentStatus.EMPLOYED,
            monthly_income=Decimal("52000.00"),
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

    def make_overdue(self, count: int = 1) -> list[PaymentSchedule]:
        schedules = list(self.application.payment_schedules.order_by("sequence")[:count])
        reference_date = timezone.localdate() - timedelta(days=1)
        for schedule in schedules:
            schedule.due_date = reference_date - timedelta(days=schedule.sequence)
            schedule.status = PaymentSchedule.Status.DUE
            schedule.save(update_fields=["due_date", "status"])
        self.application.refresh_payment_progress(reference_date=reference_date)
        return schedules

    def test_overdue_creates_warning_case(self):
        schedules = self.make_overdue(1)
        case = self.application.repossession_case
        self.assertEqual(case.status, RepossessionCase.Status.WARNING)
        self.assertEqual(case.overdue_installments, 1)
        self.assertEqual(case.total_overdue_amount, schedules[0].total_amount)
        self.assertTrue(case.events.exists())

    def test_multiple_overdue_escalates_to_active(self):
        self.make_overdue(2)
        case = self.application.repossession_case
        self.assertEqual(case.status, RepossessionCase.Status.ACTIVE)
        self.assertEqual(case.overdue_installments, 2)

    def test_reminder_view_records_event(self):
        self.make_overdue(1)
        case = self.application.repossession_case
        url = reverse("repossession:send-reminder", args=[case.pk])
        response = self.client.post(url, data={"message": "Called customer"})
        self.assertRedirects(response, reverse("repossession:case-detail", args=[case.pk]))
        case.refresh_from_db()
        self.assertEqual(case.status, RepossessionCase.Status.REMINDER)
        self.assertIsNotNone(case.last_reminder_sent_at)
        self.assertTrue(
            case.events.filter(event_type=RepossessionEvent.EventType.REMINDER).exists()
        )

    def test_close_case_sets_status_closed(self):
        self.make_overdue(1)
        case = self.application.repossession_case
        url = reverse("repossession:close-case", args=[case.pk])
        response = self.client.post(url, data={"notes": "Unit recovered"})
        self.assertRedirects(response, reverse("repossession:case-detail", args=[case.pk]))
        case.refresh_from_db()
        self.assertEqual(case.status, RepossessionCase.Status.CLOSED)
        self.assertEqual(case.resolution_notes, "Unit recovered")

    def test_payment_recovery_marks_case_recovered(self):
        schedules = self.make_overdue(1)
        case = self.application.repossession_case
        schedule = schedules[0]
        url = reverse("payments:record-payment", args=[schedule.pk])
        payload = {
            "amount": schedule.total_amount,
            "payment_date": timezone.localdate().isoformat(),
            "reference": "OR-1001",
        }
        response = self.client.post(url, data=payload)
        self.assertRedirects(response, reverse("payments:schedule-list"))
        case.refresh_from_db()
        self.assertEqual(case.status, RepossessionCase.Status.RECOVERED)
        self.assertEqual(case.overdue_installments, 0)
        self.assertEqual(case.total_overdue_amount, Decimal("0.00"))

    def test_list_and_detail_views_render(self):
        self.make_overdue(1)
        case = self.application.repossession_case
        list_response = self.client.get(reverse("repossession:case-list"))
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, "Repossession cases")
        detail_response = self.client.get(reverse("repossession:case-detail", args=[case.pk]))
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, case.loan_application.applicant_full_name)
