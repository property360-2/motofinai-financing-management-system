"""Forms for POS payment system."""

from decimal import Decimal

from django import forms

from motofinai.apps.loans.models import LoanApplication
from motofinai.apps.payments.models import Payment, PaymentMethod

INPUT_CLASSES = (
    "block w-full rounded-md border border-slate-300 px-3 py-2 text-sm "
    "shadow-sm focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
)


class QuickPayForm(forms.Form):
    """Quick payment form for rapid customer lookup and payment."""

    customer_search = forms.CharField(
        label="Find Customer",
        max_length=200,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "Search by name, phone, or loan number...",
                "autocomplete": "off",
            }
        ),
        help_text="Search by applicant name, phone number, or loan application ID",
    )


class PaymentRecordForm(forms.ModelForm):
    """Form for recording a payment with payment method details."""

    class Meta:
        model = Payment
        fields = [
            "payment_method",
            "amount",
            "check_number",
            "check_date",
            "bank_name",
            "bank_reference",
            "notes",
        ]
        widgets = {
            "payment_method": forms.Select(
                attrs={
                    "class": INPUT_CLASSES,
                    "id": "payment-method",
                }
            ),
            "amount": forms.NumberInput(
                attrs={
                    "class": INPUT_CLASSES,
                    "step": "0.01",
                    "min": "0.01",
                    "placeholder": "0.00",
                }
            ),
            "check_number": forms.TextInput(
                attrs={
                    "class": INPUT_CLASSES,
                    "placeholder": "Check number",
                }
            ),
            "check_date": forms.DateInput(
                attrs={
                    "class": INPUT_CLASSES,
                    "type": "date",
                }
            ),
            "bank_name": forms.TextInput(
                attrs={
                    "class": INPUT_CLASSES,
                    "placeholder": "Bank name",
                }
            ),
            "bank_reference": forms.TextInput(
                attrs={
                    "class": INPUT_CLASSES,
                    "placeholder": "Transaction reference number",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": INPUT_CLASSES,
                    "rows": "3",
                    "placeholder": "Additional payment notes...",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make conditional fields not required by default
        self.fields["check_number"].required = False
        self.fields["check_date"].required = False
        self.fields["bank_name"].required = False
        self.fields["bank_reference"].required = False
        self.fields["notes"].required = False

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get("payment_method")

        # Validate check-specific fields
        if payment_method == PaymentMethod.CHECK:
            if not cleaned_data.get("check_number"):
                raise forms.ValidationError("Check number is required for check payments.")
            if not cleaned_data.get("check_date"):
                raise forms.ValidationError("Check date is required for check payments.")

        # Validate bank transfer fields
        if payment_method == PaymentMethod.BANK_TRANSFER:
            if not cleaned_data.get("bank_name"):
                raise forms.ValidationError("Bank name is required for bank transfer payments.")
            if not cleaned_data.get("bank_reference"):
                raise forms.ValidationError("Bank reference is required for bank transfer payments.")

        return cleaned_data


class POSSessionOpenForm(forms.Form):
    """Form to open a new POS session."""

    opening_cash = forms.DecimalField(
        label="Opening Cash Float",
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00"),
        widget=forms.NumberInput(
            attrs={
                "class": INPUT_CLASSES,
                "step": "0.01",
                "min": "0",
                "placeholder": "0.00",
            }
        ),
        help_text="Initial cash float for this session",
    )
    notes = forms.CharField(
        label="Session Notes (Optional)",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": INPUT_CLASSES,
                "rows": "3",
                "placeholder": "Any notes about this session...",
            }
        ),
    )


class POSSessionCloseForm(forms.Form):
    """Form to close a POS session."""

    closing_cash = forms.DecimalField(
        label="Closing Cash Count",
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00"),
        widget=forms.NumberInput(
            attrs={
                "class": INPUT_CLASSES,
                "step": "0.01",
                "min": "0",
                "placeholder": "0.00",
            }
        ),
        help_text="Actual cash counted at session close",
    )
    notes = forms.CharField(
        label="Discrepancy Notes (Optional)",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": INPUT_CLASSES,
                "rows": "3",
                "placeholder": "Note any cash discrepancies or issues...",
            }
        ),
    )
