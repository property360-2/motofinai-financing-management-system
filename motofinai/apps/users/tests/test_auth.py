from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse

from motofinai.apps.users.decorators import role_required
from motofinai.apps.users.models import User


class AuthenticationFlowTests(TestCase):
    def setUp(self) -> None:
        self.password = "testpass123"
        self.user = get_user_model().objects.create_user(
            username="finance_user",
            password=self.password,
            role=User.Roles.FINANCE,
        )

    def test_login_page_renders(self):
        response = self.client.get(reverse("users:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome back")

    def test_user_can_login_via_form(self):
        response = self.client.post(
            reverse("users:login"),
            {"username": self.user.username, "password": self.password},
            HTTP_USER_AGENT="pytest",
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("home"))
        home = self.client.get(reverse("home"))
        self.assertTrue(home.context["user"].is_authenticated)


class RoleRequiredDecoratorTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.admin = get_user_model().objects.create_user(
            username="admin_user",
            password="pass12345",
            role=User.Roles.ADMIN,
        )
        self.finance = get_user_model().objects.create_user(
            username="finance_role",
            password="pass12345",
            role=User.Roles.FINANCE,
        )

    def test_role_required_redirects_anonymous_user(self):
        @role_required(User.Roles.ADMIN)
        def secured_view(request):
            return HttpResponse("ok")

        request = self.factory.get("/secure/")
        request.user = AnonymousUser()
        response = secured_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:login"), response.headers["Location"])

    def test_role_required_blocks_non_matching_role(self):
        @role_required(User.Roles.ADMIN)
        def secured_view(request):
            return HttpResponse("ok")

        request = self.factory.get("/secure/")
        request.user = self.finance
        with self.assertRaises(PermissionDenied):
            secured_view(request)

    def test_role_required_allows_matching_role(self):
        @role_required(User.Roles.ADMIN)
        def secured_view(request):
            return HttpResponse("ok")

        request = self.factory.get("/secure/")
        request.user = self.admin
        response = secured_view(request)
        self.assertEqual(response.status_code, 200)
