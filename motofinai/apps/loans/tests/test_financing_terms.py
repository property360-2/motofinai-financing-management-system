from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from motofinai.apps.loans.forms import FinancingTermForm
from motofinai.apps.loans.models import FinancingTerm
from motofinai.apps.users.models import User


class FinancingTermViewTests(TestCase):
    def setUp(self) -> None:
        self.admin = get_user_model().objects.create_user(
            username="admin_terms",
            password="password123",
            role=User.Roles.ADMIN,
        )
        self.finance = get_user_model().objects.create_user(
            username="finance_terms",
            password="password123",
            role=User.Roles.FINANCE,
        )

    def test_finance_role_can_view_terms(self):
        FinancingTerm.objects.create(term_years=3, interest_rate=Decimal("12.50"))
        self.client.force_login(self.finance)
        response = self.client.get(reverse("terms:list"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("terms", response.context)
        self.assertEqual(len(response.context["terms"]), 1)

    def test_admin_can_create_term(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("terms:create"),
            data={"term_years": 4, "interest_rate": "15.00", "is_active": True},
        )
        self.assertRedirects(response, reverse("terms:list"))
        self.assertEqual(FinancingTerm.objects.count(), 1)
        term = FinancingTerm.objects.first()
        assert term is not None
        self.assertEqual(term.monthly_interest_rate.quantize(Decimal("0.0001")), Decimal("0.0125"))

    def test_finance_cannot_create_term(self):
        self.client.force_login(self.finance)
        response = self.client.post(
            reverse("terms:create"),
            data={"term_years": 2, "interest_rate": "10.00", "is_active": True},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(FinancingTerm.objects.count(), 0)

    def test_form_validates_positive_interest(self):
        form = FinancingTermForm(
            data={"term_years": 3, "interest_rate": "0.00", "is_active": True}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("interest_rate", form.errors)
