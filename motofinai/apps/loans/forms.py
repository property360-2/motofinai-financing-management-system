from decimal import Decimal

from django import forms

from motofinai.apps.inventory.models import Motor

from .models import FinancingTerm, LoanApplication, LoanDocument

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


class LoanPersonalInfoForm(forms.Form):
    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": INPUT_CLASSES}),
    )
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": INPUT_CLASSES}),
    )
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": INPUT_CLASSES}))
    phone = forms.CharField(
        max_length=32,
        widget=forms.TextInput(attrs={"class": INPUT_CLASSES}),
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": INPUT_CLASSES, "type": "date"}),
    )


class LoanEmploymentForm(forms.Form):
    employment_status = forms.ChoiceField(
        choices=LoanApplication.EmploymentStatus.choices,
        widget=forms.Select(attrs={"class": INPUT_CLASSES}),
    )
    employer_name = forms.CharField(
        required=False,
        max_length=150,
        widget=forms.TextInput(attrs={"class": INPUT_CLASSES}),
    )
    monthly_income = forms.DecimalField(
        min_value=0,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={"class": INPUT_CLASSES, "step": "0.01", "min": "0"}
        ),
    )


class LoanMotorSelectionForm(forms.Form):
    motor = forms.ModelChoiceField(
        queryset=Motor.objects.all(),
        widget=forms.Select(attrs={"class": INPUT_CLASSES}),
    )
    financing_term = forms.ModelChoiceField(
        queryset=FinancingTerm.objects.filter(is_active=True),
        widget=forms.Select(attrs={"class": INPUT_CLASSES}),
    )
    down_payment = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={"class": INPUT_CLASSES, "step": "0.01", "min": "0"}
        ),
        help_text="Optional upfront payment to lower the financed amount.",
    )

    def clean(self):
        cleaned_data = super().clean()
        motor: Motor | None = cleaned_data.get("motor")
        down_payment = cleaned_data.get("down_payment") or Decimal("0.00")
        if motor and down_payment and down_payment > motor.purchase_price:
            self.add_error(
                "down_payment",
                "Down payment cannot exceed the motorcycle purchase price.",
            )
        cleaned_data["down_payment"] = down_payment
        return cleaned_data


class LoanSupportingDocsForm(forms.Form):
    has_valid_id = forms.BooleanField(
        label="Applicant presented a valid government ID",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": (
                    "h-4 w-4 rounded border-slate-300 text-sky-600 "
                    "focus:ring-sky-500"
                )
            }
        ),
    )
    has_proof_of_income = forms.BooleanField(
        label="Income documents received",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": (
                    "h-4 w-4 rounded border-slate-300 text-sky-600 "
                    "focus:ring-sky-500"
                )
            }
        ),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": f"{INPUT_CLASSES} min-h-[120px]",
                "rows": 5,
            }
        ),
    )


class LoanDocumentUploadForm(forms.ModelForm):
    class Meta:
        model = LoanDocument
        fields = ["document_type", "title", "file"]
        widgets = {
            "document_type": forms.Select(attrs={"class": INPUT_CLASSES}),
            "title": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "file": forms.ClearableFileInput(
                attrs={
                    "class": (
                        "block w-full cursor-pointer rounded-md border border-dashed border-slate-300 "
                        "px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
                    )
                }
            ),
        }

    def clean_file(self):
        uploaded = self.cleaned_data.get("file")
        if not uploaded:
            return uploaded
        allowed_types = {"application/pdf", "image/jpeg", "image/png"}
        content_type = getattr(uploaded, "content_type", None)
        if content_type and content_type not in allowed_types:
            raise forms.ValidationError("Only PDF, JPEG, or PNG files are supported.")
        if uploaded.size <= 0:
            raise forms.ValidationError("Uploaded document appears to be empty.")
        return uploaded


class LoanApprovalForm(forms.Form):
    """Form for approving loan applications with optional custom terms."""

    custom_interest_rate = forms.DecimalField(
        required=False,
        min_value=Decimal("0.00"),
        decimal_places=2,
        help_text="Leave blank to use the financing term's interest rate",
        widget=forms.NumberInput(
            attrs={
                "class": INPUT_CLASSES,
                "min": "0",
                "step": "0.01",
                "placeholder": "e.g., 12.50 for 12.5%",
            }
        ),
    )
    custom_term_years = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=10,
        help_text="Leave blank to use the financing term's duration",
        widget=forms.NumberInput(
            attrs={
                "class": INPUT_CLASSES,
                "min": "1",
                "max": "10",
                "step": "1",
                "placeholder": "e.g., 3 for 3 years",
            }
        ),
    )
    approval_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": INPUT_CLASSES,
                "rows": "4",
                "placeholder": "Optional notes about this approval decision",
            }
        ),
    )


class CreditInvestigationForm(forms.Form):
    """Form for credit investigator to approve or flag loan applications."""

    approved = forms.BooleanField(
        required=False,
        label="Approve this loan",
        widget=forms.CheckboxInput(
            attrs={
                "class": "h-4 w-4 rounded border-slate-300 text-sky-600 focus:ring-sky-500"
            }
        ),
    )
    investigation_notes = forms.CharField(
        required=True,
        label="Investigation Notes",
        help_text="Required: Document your assessment and reasoning",
        widget=forms.Textarea(
            attrs={
                "class": INPUT_CLASSES,
                "rows": "6",
                "placeholder": "Document your credit investigation findings, risk factors, and final assessment...",
            }
        ),
    )
