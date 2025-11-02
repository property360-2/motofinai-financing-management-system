from django.contrib import admin

from .models import Motor


@admin.register(Motor)
class MotorAdmin(admin.ModelAdmin):
    list_display = ("display_name", "status", "purchase_price", "created_at")
    list_filter = ("status", "brand", "type", "year")
    search_fields = ("brand", "model_name", "type", "chassis_number")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("type", "brand", "model_name", "year", "status")}),
        (
            "Details",
            {
                "fields": (
                    "color",
                    "purchase_price",
                    "chassis_number",
                    "image",
                    "notes",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
