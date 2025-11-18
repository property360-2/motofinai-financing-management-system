from django.contrib import admin

from .models import Motor, Stock


@admin.register(Motor)
class MotorAdmin(admin.ModelAdmin):
    list_display = ("display_name", "type", "quantity", "purchase_price", "motor_status", "stock", "created_at")
    list_filter = ("type", "brand", "year", "stock")
    search_fields = ("brand", "model_name", "type", "chassis_number")
    readonly_fields = ("created_at", "updated_at", "motor_status")
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
        ("Status", {"fields": ("motor_status",), "description": "Motor status is derived from associated loan applications"}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def motor_status(self, obj):
        """Display motor status as a colored badge."""
        status = obj.status
        colors = {
            'available': '#10b981',  # Green
            'reserved': '#f59e0b',   # Amber
            'sold': '#6b7280',       # Gray
            'repossessed': '#ef4444' # Red
        }
        return f'<span style="background-color: {colors.get(status, "#999")}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px;">{status.upper()}</span>'

    motor_status.short_description = 'Status'
    motor_status.allow_tags = True


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
