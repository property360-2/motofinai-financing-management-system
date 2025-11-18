from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from motofinai.apps.inventory.models import Motor
from motofinai.apps.users.models import User


class InventoryViewTests(TestCase):
    def setUp(self) -> None:
        self.admin = get_user_model().objects.create_user(
            username="admin_user",
            password="password123",
            role=User.Roles.ADMIN,
        )
        self.finance = get_user_model().objects.create_user(
            username="finance_user",
            password="password123",
            role=User.Roles.FINANCE,
        )

    def _motor_payload(self, **overrides):
        payload = {
            "type": "scooter",
            "brand": "Honda",
            "model_name": "Click 125i",
            "year": date.today().year,
            "color": "Black",
            "purchase_price": "95000.00",
            "chassis_number": "CHASSIS-123",
            "notes": "For display unit.",
        }
        payload.update(overrides)
        return payload

    def test_admin_can_create_motor(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("inventory:motor-create"),
            data=self._motor_payload(),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Motor.objects.count(), 1)
        motor = Motor.objects.first()
        assert motor is not None
        self.assertEqual(motor.brand, "Honda")
        self.assertEqual(motor.purchase_price, Decimal("95000.00"))

    def test_finance_cannot_access_create_view(self):
        self.client.force_login(self.finance)
        response = self.client.get(reverse("inventory:motor-create"))
        self.assertEqual(response.status_code, 403)

    def test_finance_can_view_list_and_filter(self):
        Motor.objects.create(
            type="scooter",
            brand="Honda",
            model_name="Click",
            year=date.today().year,
            color="Black",
            purchase_price=Decimal("90000.00"),
            chassis_number="CHASSIS-001",
        )
        Motor.objects.create(
            type="underbone",
            brand="Yamaha",
            model_name="Sniper",
            year=date.today().year,
            color="Blue",
            purchase_price=Decimal("115000.00"),
            chassis_number="CHASSIS-002",
        )
        self.client.force_login(self.finance)
        response = self.client.get(
            reverse("inventory:motor-list"),
            data={"q": "Yamaha"},
        )
        self.assertEqual(response.status_code, 200)
        motors = list(response.context["motors"])
        self.assertEqual(len(motors), 1)
        self.assertEqual(motors[0].brand, "Yamaha")

    def test_admin_can_delete_motor(self):
        motor = Motor.objects.create(
            type="scooter",
            brand="Honda",
            model_name="Grazia",
            year=date.today().year,
            color="Red",
            purchase_price=Decimal("98000.00"),
            chassis_number="CHASSIS-DELETE",
        )
        self.client.force_login(self.admin)
        response = self.client.post(reverse("inventory:motor-delete", args=[motor.pk]))
        self.assertRedirects(response, reverse("inventory:motor-list"))
        self.assertFalse(Motor.objects.filter(pk=motor.pk).exists())
