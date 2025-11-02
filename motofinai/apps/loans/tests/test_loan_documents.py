from __future__ import annotations

import shutil
import tempfile
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from motofinai.apps.inventory.models import Motor
from motofinai.apps.loans.models import (
    FinancingTerm,
    LoanApplication,
    LoanDocument,
)
from motofinai.apps.users.models import User


class LoanDocumentManagementTests(TestCase):
    def setUp(self):
        super().setUp()
        self.temp_media = tempfile.mkdtemp()
        override = override_settings(MEDIA_ROOT=self.temp_media)
        override.enable()
        self.addCleanup(override.disable)
        self.addCleanup(lambda: shutil.rmtree(self.temp_media, ignore_errors=True))

        self.admin = get_user_model().objects.create_user(
            username="loan_admin",
            password="password123",
            role=User.Roles.ADMIN,
        )
        self.motor = Motor.objects.create(
            type="Scooter",
            brand="Honda",
            model_name="Click 125",
            year=2024,
            purchase_price=Decimal("95000.00"),
        )
        self.term = FinancingTerm.objects.create(
            term_years=2,
            interest_rate=Decimal("10.00"),
        )
        self.application = LoanApplication.objects.create(
            applicant_first_name="Pedro",
            applicant_last_name="Cruz",
            applicant_email="pedro@example.com",
            applicant_phone="09171234567",
            employment_status=LoanApplication.EmploymentStatus.EMPLOYED,
            monthly_income=Decimal("45000.00"),
            motor=self.motor,
            financing_term=self.term,
            loan_amount=self.motor.purchase_price,
            down_payment=Decimal("5000.00"),
            principal_amount=Decimal("90000.00"),
            interest_rate=self.term.interest_rate,
            monthly_payment=Decimal("0.00"),
            submitted_by=self.admin,
        )
        self.application.monthly_payment = self.application.calculate_monthly_payment()
        self.application.save(update_fields=["monthly_payment"])
        self.client.force_login(self.admin)

    def test_upload_document_success(self):
        upload = SimpleUploadedFile(
            "valid-id.pdf",
            b"fake file contents",
            content_type="application/pdf",
        )
        url = reverse("loans:documents", args=[self.application.pk])
        response = self.client.post(
            url,
            data={
                "document_type": LoanDocument.DocumentType.VALID_ID,
                "title": "Government ID",
                "file": upload,
            },
        )
        self.assertRedirects(response, url)
        documents = LoanDocument.objects.filter(loan_application=self.application)
        self.assertEqual(documents.count(), 1)
        document = documents.first()
        assert document is not None
        self.assertEqual(document.uploaded_by, self.admin)
        self.assertTrue(document.file.storage.exists(document.file.name))

    def test_rejects_unsupported_file_type(self):
        upload = SimpleUploadedFile(
            "script.exe",
            b"pretend binary",
            content_type="application/octet-stream",
        )
        url = reverse("loans:documents", args=[self.application.pk])
        response = self.client.post(
            url,
            data={
                "document_type": LoanDocument.DocumentType.OTHER,
                "title": "Executable",
                "file": upload,
            },
        )
        self.assertEqual(response.status_code, 400)
        form = response.context["form"]
        self.assertIn(
            "Only PDF, JPEG, or PNG files are supported.",
            form.errors.get("file", []),
        )
        self.assertFalse(
            LoanDocument.objects.filter(loan_application=self.application).exists()
        )

    def test_delete_document_removes_file(self):
        document = LoanDocument.objects.create(
            loan_application=self.application,
            document_type=LoanDocument.DocumentType.PROOF_OF_INCOME,
            title="Payslip",
            file=SimpleUploadedFile(
                "payslip.png",
                b"binarydata",
                content_type="image/png",
            ),
            uploaded_by=self.admin,
        )
        delete_url = reverse(
            "loans:document-delete",
            args=[self.application.pk, document.pk],
        )
        response = self.client.post(delete_url)
        self.assertRedirects(
            response,
            reverse("loans:documents", args=[self.application.pk]),
        )
        self.assertFalse(
            LoanDocument.objects.filter(loan_application=self.application).exists()
        )
        self.assertFalse(document.file.storage.exists(document.file.name))
