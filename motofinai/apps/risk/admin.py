from django.contrib import admin

from .models import RiskAssessment


@admin.register(RiskAssessment)
class RiskAssessmentAdmin(admin.ModelAdmin):
    list_display = (
        "loan_application",
        "score",
        "risk_level",
        "missed_payments",
        "debt_to_income_ratio",
        "updated_at",
    )
    list_filter = ("risk_level", "updated_at")
    search_fields = (
        "loan_application__applicant_first_name",
        "loan_application__applicant_last_name",
        "loan_application__applicant_email",
    )
    readonly_fields = (
        "score",
        "risk_level",
        "missed_payments",
        "income_factor",
        "credit_factor",
        "debt_to_income_ratio",
        "employment_penalty",
        "updated_at",
        "calculated_at",
    )
