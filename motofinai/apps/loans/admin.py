from django.contrib import admin

from .models import FinancingTerm


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
