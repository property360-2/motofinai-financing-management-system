from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from motofinai.apps.audit.models import AuditLogEntry
from motofinai.apps.users.models import User


class AuthenticationAuditLogTests(TestCase):
    def setUp(self) -> None:
        self.password = "auditpass123"
        self.user = get_user_model().objects.create_user(
            username="audited_user",
            password=self.password,
            role=User.Roles.ADMIN,
        )

    def test_login_creates_audit_entry(self):
        self.client.post(
            reverse("users:login"),
            {"username": self.user.username, "password": self.password},
            HTTP_USER_AGENT="pytest",
        )
        log = AuditLogEntry.objects.filter(action="auth.login").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.actor, self.user)
        self.assertEqual(log.metadata.get("session_key"), self.client.session.session_key)

    def test_logout_creates_audit_entry(self):
        self.client.post(
            reverse("users:login"),
            {"username": self.user.username, "password": self.password},
            HTTP_USER_AGENT="pytest",
        )
        previous_session = self.client.session.session_key
        self.client.get(reverse("users:logout"), HTTP_USER_AGENT="pytest")
        log = AuditLogEntry.objects.filter(action="auth.logout").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.actor, self.user)
        self.assertEqual(log.metadata.get("session_key"), previous_session)
