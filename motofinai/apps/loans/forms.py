from decimal import Decimal

from django import forms

from .models import FinancingTerm

INPUT_CLASSES = (
    "block w-full rounded-md border border-slate-300 px-3 py-2 text-sm "
    "shadow-sm focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
)


class FinancingTermForm(forms.ModelForm):
    class Meta:
        model = FinancingTerm
        fields = ["term_years", "interest_rate", "is_active"]
        widgets = {
            "term_years": forms.NumberInput(
                attrs={"class": INPUT_CLASSES, "min": "1", "step": "1"}
            ),
            "interest_rate": forms.NumberInput(
                attrs={"class": INPUT_CLASSES, "min": "0", "step": "0.01"}
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": (
                        "h-4 w-4 rounded border-slate-300 text-sky-600 "
                        "focus:ring-sky-500"
                    )
                }
            ),
        }

    def clean_interest_rate(self):
        value = self.cleaned_data["interest_rate"]
        if value <= Decimal("0.00"):
            raise forms.ValidationError("Interest rate must be greater than zero.")
        return value
