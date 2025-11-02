"""Forms for managing loan risk assessments."""

from django import forms

from .models import RiskAssessmentManager


class RiskAssessmentInputForm(forms.Form):
    base_score = forms.IntegerField(
        min_value=0,
        max_value=100,
        initial=RiskAssessmentManager.DEFAULT_BASE_SCORE,
        help_text="Starting point for the risk formula before penalties and deductions.",
        label="Base score",
    )
    credit_score = forms.IntegerField(
        min_value=300,
        max_value=850,
        initial=RiskAssessmentManager.DEFAULT_CREDIT_SCORE,
        help_text="Recent credit score pulled from the applicant's bureau report.",
        label="Credit score",
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="Optional remarks that justify manual adjustments or context from underwriting.",
        label="Internal notes",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = " ".join(
                part
                for part in [
                    "mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm",
                    "focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500",
                    existing,
                ]
                if part
            )
