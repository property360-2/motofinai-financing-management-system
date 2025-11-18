from datetime import date

from django import forms

from .models import Motor


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
            "status",
            "quantity",
            "color",
            "purchase_price",
            "chassis_number",
            "notes",
        ]
        widgets = {
            "type": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Scooter"}),
            "brand": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Honda"}),
            "model_name": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Click 125i"}),
            "year": forms.NumberInput(attrs={"class": INPUT_CLASSES, "min": 1900}),
            "status": forms.Select(attrs={"class": INPUT_CLASSES}),
            "quantity": forms.NumberInput(attrs={"class": INPUT_CLASSES, "min": 1}),
            "color": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Matte Black"}),
            "purchase_price": forms.NumberInput(
                attrs={"class": INPUT_CLASSES, "step": "0.01", "min": "0"}
            ),
            "chassis_number": forms.TextInput(
                attrs={"class": INPUT_CLASSES, "placeholder": "Optional chassis/VIN"}
            ),
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
    status = forms.ChoiceField(
        required=False,
        choices=[("", "All statuses"), *Motor.Status.choices],
        widget=forms.Select(attrs={"class": INPUT_CLASSES}),
    )
    q = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "Search by keyword (brand, model, type, chassis)",
            }
        ),
    )
