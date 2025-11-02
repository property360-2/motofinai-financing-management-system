from django.contrib import admin

from .models import FinancingTerm, LoanApplication, LoanDocument, PaymentSchedule


@admin.register(FinancingTerm)
class FinancingTermAdmin(admin.ModelAdmin):
    list_display = ("term_years", "interest_rate", "is_active", "created_at")
    list_filter = ("is_active", "term_years")
    search_fields = ("term_years__exact",)
    ordering = ("term_years", "interest_rate")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("term_years", "interest_rate", "is_active")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


class PaymentScheduleInline(admin.TabularInline):
    model = PaymentSchedule
    extra = 0
    readonly_fields = (
        "sequence",
        "due_date",
        "principal_amount",
        "interest_amount",
        "total_amount",
        "status",
        "paid_at",
    )
    can_delete = False


class LoanDocumentInline(admin.TabularInline):
    model = LoanDocument
    extra = 0
    readonly_fields = (
        "document_type",
        "title",
        "file",
        "uploaded_by",
        "uploaded_at",
    )
    can_delete = False


@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "applicant_full_name",
        "motor",
        "loan_amount",
        "monthly_payment",
        "status",
        "submitted_at",
    )
    list_filter = ("status", "financing_term__term_years")
    search_fields = (
        "applicant_first_name",
        "applicant_last_name",
        "applicant_email",
    )
    readonly_fields = (
        "submitted_at",
        "approved_at",
        "activated_at",
        "completed_at",
        "updated_at",
    )
    fieldsets = (
        (
            "Applicant",
            {
                "fields": (
                    "applicant_first_name",
                    "applicant_last_name",
                    "applicant_email",
                    "applicant_phone",
                    "date_of_birth",
                    "employment_status",
                    "employer_name",
                    "monthly_income",
                    "has_valid_id",
                    "has_proof_of_income",
                )
            },
        ),
        (
            "Loan details",
            {
                "fields": (
                    "motor",
                    "financing_term",
                    "loan_amount",
                    "down_payment",
                    "principal_amount",
                    "interest_rate",
                    "monthly_payment",
                    "status",
                    "notes",
                    "submitted_by",
                )
            },
        ),
        (
            "Timeline",
            {
                "fields": (
                    "submitted_at",
                    "approved_at",
                    "activated_at",
                    "completed_at",
                    "updated_at",
                )
            },
        ),
    )
    inlines = (PaymentScheduleInline, LoanDocumentInline)
