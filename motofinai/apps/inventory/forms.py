from datetime import date

from django import forms

from .models import Motor, Stock


INPUT_CLASSES = (
    "block w-full rounded-md border border-slate-300 px-3 py-2 text-sm "
    "shadow-sm focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
)


class MotorForm(forms.ModelForm):
    class Meta:
        model = Motor
        fields = [
            "type",
            "brand",
            "model_name",
            "year",
            "chassis_number",
            "quantity",
            "color",
            "purchase_price",
            "stock",
            "notes",
        ]
        widgets = {
            "type": forms.Select(attrs={"class": INPUT_CLASSES}),
            "brand": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Honda"}),
            "model_name": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Click 125i"}),
            "year": forms.NumberInput(attrs={"class": INPUT_CLASSES, "min": 1900}),
            "chassis_number": forms.TextInput(
                attrs={"class": INPUT_CLASSES, "placeholder": "VIN/Chassis Number (optional)"}
            ),
            "quantity": forms.NumberInput(attrs={"class": INPUT_CLASSES, "min": 1}),
            "color": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Matte Black"}),
            "purchase_price": forms.NumberInput(
                attrs={"class": INPUT_CLASSES, "step": "0.01", "min": "0"}
            ),
            "stock": forms.Select(attrs={"class": INPUT_CLASSES}),
            "notes": forms.Textarea(
                attrs={
                    "class": INPUT_CLASSES,
                    "rows": 4,
                    "placeholder": "Optional additional notes for admins.",
                }
            ),
        }

    def clean_year(self):
        year = self.cleaned_data["year"]
        max_year = date.today().year + 1
        if year > max_year:
            raise forms.ValidationError(
                f"Year cannot be greater than {max_year}. Update the inventory once the model year is available."
            )
        return year


class MotorFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "Search by keyword (brand, model, type)",
            }
        ),
    )


class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = [
            "brand",
            "model_name",
            "year",
            "color",
            "quantity_available",
        ]
        widgets = {
            "brand": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Honda"}),
            "model_name": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Click 125i"}),
            "year": forms.NumberInput(attrs={"class": INPUT_CLASSES, "min": 1900}),
            "color": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Matte Black"}),
            "quantity_available": forms.NumberInput(
                attrs={"class": INPUT_CLASSES, "min": "0"}
            ),
        }

    def clean_year(self):
        year = self.cleaned_data["year"]
        max_year = date.today().year + 1
        if year > max_year:
            raise forms.ValidationError(
                f"Year cannot be greater than {max_year}."
            )
        return year


class StockFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "Search by keyword (brand, model, color)",
            }
        ),
    )


# Receiving workflow forms
class MotorReceivingForm(forms.ModelForm):
    """Form for registering incoming motorcycles."""
    class Meta:
        model_import_path = "motofinai.apps.inventory.models"
        fields = [
            "brand", "model_name", "year", "vin_number", "engine_number",
            "color", "motorcycle_type", "purchase_price", "quantity",
            "supplier_name", "purchase_order_number", "invoice_number", "notes"
        ]
        widgets = {
            "brand": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Honda"}),
            "model_name": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Click 125i"}),
            "year": forms.NumberInput(attrs={"class": INPUT_CLASSES, "min": 1900}),
            "vin_number": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "VIN/Chassis Number"}),
            "engine_number": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Optional engine number"}),
            "color": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Color"}),
            "motorcycle_type": forms.Select(attrs={"class": INPUT_CLASSES}),
            "purchase_price": forms.NumberInput(attrs={"class": INPUT_CLASSES, "step": "0.01", "min": "0"}),
            "quantity": forms.NumberInput(attrs={"class": INPUT_CLASSES, "min": 1}),
            "supplier_name": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Supplier name"}),
            "purchase_order_number": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "PO Number"}),
            "invoice_number": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Invoice Number"}),
            "notes": forms.Textarea(attrs={"class": INPUT_CLASSES, "rows": 3, "placeholder": "Additional notes"}),
        }


class ReceivingInspectionForm(forms.ModelForm):
    """Form for motor inspection during receiving process."""
    class Meta:
        model_import_path = "motofinai.apps.inventory.models"
        fields = [
            "engine_condition", "frame_condition", "electrical_system",
            "tires_condition", "brakes_condition", "paint_condition",
            "overall_result", "issues_found", "recommendations"
        ]
        widgets = {
            "engine_condition": forms.Select(attrs={"class": INPUT_CLASSES}),
            "frame_condition": forms.Select(attrs={"class": INPUT_CLASSES}),
            "electrical_system": forms.Select(attrs={"class": INPUT_CLASSES}),
            "tires_condition": forms.Select(attrs={"class": INPUT_CLASSES}),
            "brakes_condition": forms.Select(attrs={"class": INPUT_CLASSES}),
            "paint_condition": forms.Select(attrs={"class": INPUT_CLASSES}),
            "overall_result": forms.Select(attrs={"class": INPUT_CLASSES}),
            "issues_found": forms.Textarea(attrs={"class": INPUT_CLASSES, "rows": 3, "placeholder": "List any issues found"}),
            "recommendations": forms.Textarea(attrs={"class": INPUT_CLASSES, "rows": 3, "placeholder": "Recommendations for repair or maintenance"}),
        }


class ReceivingDocumentForm(forms.ModelForm):
    """Form for uploading receiving documents."""
    class Meta:
        model_import_path = "motofinai.apps.inventory.models"
        fields = [
            "document_type", "document_name", "file_path",
            "document_date", "reference_number", "description"
        ]
        widgets = {
            "document_type": forms.Select(attrs={"class": INPUT_CLASSES}),
            "document_name": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Document name"}),
            "file_path": forms.FileInput(attrs={"class": INPUT_CLASSES}),
            "document_date": forms.DateInput(attrs={"class": INPUT_CLASSES, "type": "date"}),
            "reference_number": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Reference number"}),
            "description": forms.Textarea(attrs={"class": INPUT_CLASSES, "rows": 2, "placeholder": "Document description"}),
        }
