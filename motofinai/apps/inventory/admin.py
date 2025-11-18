from django.contrib import admin

from .models import Motor, Stock


@admin.register(Motor)
class MotorAdmin(admin.ModelAdmin):
    list_display = ("display_name", "type", "quantity", "purchase_price", "stock", "created_at")
    list_filter = ("type", "brand", "year", "stock")
    search_fields = ("brand", "model_name", "type", "chassis_number")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("type", "brand", "model_name", "year")}),
        (
            "Details",
            {
                "fields": (
                    "color",
                    "purchase_price",
                    "quantity",
                    "chassis_number",
                    "stock",
                    "notes",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ("__str__", "total_quantity", "quantity_available", "quantity_reserved", "quantity_sold", "quantity_repossessed", "created_at")
    list_filter = ("brand", "year", "created_at")
    search_fields = ("brand", "model_name", "color")
    readonly_fields = ("created_at", "updated_at", "total_quantity")
    fieldsets = (
        (None, {"fields": ("brand", "model_name", "year", "color")}),
        (
            "Inventory breakdown",
            {
                "fields": (
                    "quantity_available",
                    "quantity_reserved",
                    "quantity_sold",
                    "quantity_repossessed",
                    "total_quantity",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
