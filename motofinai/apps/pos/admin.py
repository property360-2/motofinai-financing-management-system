from django.contrib import admin

from .models import POSSession, POSTransaction, ReceiptLog


@admin.register(POSSession)
class POSSessionAdmin(admin.ModelAdmin):
    """Admin for POS sessions."""

    list_display = [
        "id",
        "opened_by",
        "opened_at",
        "status",
        "transaction_count",
        "total_collected",
    ]
    list_filter = ["status", "opened_at"]
    search_fields = ["opened_by__username", "notes"]
    readonly_fields = [
        "opened_at",
        "closed_at",
        "total_collected",
        "cash_variance",
    ]
    fieldsets = (
        ("Session Info", {
            "fields": ("opened_by", "opened_at", "status"),
        }),
        ("Cash Handling", {
            "fields": ("opening_cash", "closing_cash", "cash_variance"),
        }),
        ("Closure", {
            "fields": ("closed_by", "closed_at", "notes"),
            "classes": ("collapse",),
        }),
    )


@admin.register(POSTransaction)
class POSTransactionAdmin(admin.ModelAdmin):
    """Admin for POS transactions."""

    list_display = [
        "id",
        "session",
        "payment",
        "transaction_type",
        "created_at",
    ]
    list_filter = ["transaction_type", "created_at", "session"]
    search_fields = ["payment__loan_application__applicant_first_name"]
    readonly_fields = ["created_at"]


@admin.register(ReceiptLog)
class ReceiptLogAdmin(admin.ModelAdmin):
    """Admin for receipt logs."""

    list_display = [
        "receipt_number",
        "payment",
        "generated_at",
        "printed_at",
        "print_count",
    ]
    list_filter = ["generated_at", "printed_at"]
    search_fields = ["receipt_number", "payment__loan_application__applicant_first_name"]
    readonly_fields = ["generated_at"]
