from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "schedule",
        "loan_application",
        "amount",
        "payment_date",
        "recorded_by",
        "recorded_at",
    )
    list_filter = ("payment_date", "recorded_by")
    search_fields = (
        "loan_application__applicant_first_name",
        "loan_application__applicant_last_name",
        "reference",
    )
    autocomplete_fields = ("loan_application", "recorded_by")
    raw_id_fields = ("schedule",)
