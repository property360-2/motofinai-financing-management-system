from __future__ import annotations

from decimal import Decimal

from django import forms

from motofinai.apps.loans.models import PaymentSchedule

INPUT_CLASSES = (
    "block w-full rounded-md border border-slate-300 px-3 py-2 text-sm "
    "shadow-sm focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
)


class PaymentRecordForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
        widget=forms.NumberInput(
            attrs={
                "class": INPUT_CLASSES,
                "step": "0.01",
                "min": "0",
            }
        ),
        help_text="Enter the exact scheduled amount collected from the borrower.",
    )
    payment_date = forms.DateField(
        widget=forms.DateInput(attrs={"class": INPUT_CLASSES, "type": "date"}),
        help_text="Date the borrower paid this installment.",
    )
    reference = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={"class": INPUT_CLASSES}),
        help_text="Optional receipt number or reference for reconciliation.",
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": f"{INPUT_CLASSES} min-h-[120px]",
                "rows": 4,
            }
        ),
        help_text="Additional context such as payment method or remarks.",
    )

    def __init__(self, *args, schedule: PaymentSchedule, **kwargs):
        self.schedule = schedule
        super().__init__(*args, **kwargs)
        self.fields["amount"].initial = schedule.total_amount
        self.fields["payment_date"].initial = schedule.due_date

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        expected = self.schedule.total_amount
        if amount != expected:
            raise forms.ValidationError(
                "Amount must match the scheduled installment total of ₱%(expected)s.",
                params={"expected": expected},
            )
        return amount

    def clean(self):
        cleaned = super().clean()
        if self.schedule.status == PaymentSchedule.Status.PAID:
            raise forms.ValidationError("This installment has already been recorded as paid.")
        return cleaned
