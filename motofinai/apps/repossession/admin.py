from django.contrib import admin

from .models import RepossessionCase, RepossessionEvent


@admin.register(RepossessionCase)
class RepossessionCaseAdmin(admin.ModelAdmin):
    list_display = (
        "loan_application",
        "status",
        "overdue_installments",
        "total_overdue_amount",
        "last_reminder_sent_at",
        "updated_at",
    )
    list_filter = ("status",)
    search_fields = (
        "loan_application__applicant_first_name",
        "loan_application__applicant_last_name",
        "loan_application__applicant_email",
    )
    readonly_fields = ("created_at", "updated_at", "closed_at")


@admin.register(RepossessionEvent)
class RepossessionEventAdmin(admin.ModelAdmin):
    list_display = ("case", "event_type", "created_by", "created_at")
    list_filter = ("event_type",)
    search_fields = ("description",)
    readonly_fields = ("created_at",)
