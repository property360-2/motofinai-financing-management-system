from django.contrib import admin

from .models import Motor, Stock, MotorReceiving, ReceivingInspection, ReceivingDocument


@admin.register(Motor)
class MotorAdmin(admin.ModelAdmin):
    list_display = ("display_name", "type", "quantity", "purchase_price", "motor_status", "stock", "created_at")
    list_filter = ("type", "brand", "year", "stock")
    search_fields = ("brand", "model_name", "type")
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


@admin.register(MotorReceiving)
class MotorReceivingAdmin(admin.ModelAdmin):
    """Admin for motor receiving workflow."""
    list_display = ["__str__", "vin_number", "status", "inspection_status", "supplier_name", "received_at"]
    list_filter = ["status", "inspection_status", "received_at", "motorcycle_type"]
    search_fields = ["vin_number", "engine_number", "brand", "supplier_name", "invoice_number"]
    readonly_fields = ["received_at", "received_by", "accepted_at", "inspected_at"]
    fieldsets = (
        ("Motor Information", {
            "fields": ("brand", "model_name", "year", "vin_number", "engine_number", "motorcycle_type", "color"),
        }),
        ("Receiving Details", {
            "fields": ("supplier_name", "purchase_order_number", "invoice_number", "purchase_price", "quantity"),
        }),
        ("Receiving Status", {
            "fields": ("status", "received_by", "received_at"),
        }),
        ("Inspection", {
            "fields": ("inspection_status", "inspected_by", "inspected_at", "inspection_notes"),
        }),
        ("Acceptance", {
            "fields": ("accepted_by", "accepted_at", "rejection_reason"),
        }),
        ("Notes", {
            "fields": ("notes",),
        }),
    )


@admin.register(ReceivingInspection)
class ReceivingInspectionAdmin(admin.ModelAdmin):
    """Admin for motor inspection records."""
    list_display = ["motor_receiving", "overall_result", "inspector", "inspected_at"]
    list_filter = ["overall_result", "inspected_at", "engine_condition", "frame_condition"]
    search_fields = ["motor_receiving__vin_number", "motor_receiving__brand"]
    readonly_fields = ["inspected_at"]
    fieldsets = (
        ("Motor", {
            "fields": ("motor_receiving",),
        }),
        ("Inspection Results", {
            "fields": (
                "engine_condition", "frame_condition", "electrical_system",
                "tires_condition", "brakes_condition", "paint_condition", "overall_result"
            ),
        }),
        ("Findings", {
            "fields": ("issues_found", "recommendations"),
        }),
        ("Inspector Info", {
            "fields": ("inspector", "inspected_at"),
        }),
    )


@admin.register(ReceivingDocument)
class ReceivingDocumentAdmin(admin.ModelAdmin):
    """Admin for receiving documents."""
    list_display = ["document_name", "document_type", "reference_number", "motor_receiving", "uploaded_at"]
    list_filter = ["document_type", "uploaded_at"]
    search_fields = ["document_name", "reference_number", "motor_receiving__vin_number"]
    readonly_fields = ["uploaded_at", "file_size"]
    fieldsets = (
        ("Document Info", {
            "fields": ("motor_receiving", "document_type", "document_name", "reference_number"),
        }),
        ("File", {
            "fields": ("file_path", "file_size"),
        }),
        ("Details", {
            "fields": ("document_date", "description"),
        }),
        ("Metadata", {
            "fields": ("uploaded_by", "uploaded_at"),
        }),
    )
