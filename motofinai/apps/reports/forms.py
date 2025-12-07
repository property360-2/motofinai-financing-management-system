"""Forms for report generation and filtering."""

from datetime import date, timedelta

from django import forms

INPUT_CLASSES = (
    "block w-full rounded-md border border-slate-300 px-3 py-2 text-sm "
    "shadow-sm focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
)


class BaseReportFilterForm(forms.Form):
    """Base form for report filtering with common fields."""

    date_from = forms.DateField(
        label="From Date",
        required=False,
        widget=forms.DateInput(
            attrs={"class": INPUT_CLASSES, "type": "date"}
        ),
        help_text="Filter records from this date onwards",
    )
    date_to = forms.DateField(
        label="To Date",
        required=False,
        widget=forms.DateInput(
            attrs={"class": INPUT_CLASSES, "type": "date"}
        ),
        help_text="Filter records up to this date",
    )
    export_format = forms.ChoiceField(
        label="Export Format",
        required=False,
        initial="view",
        choices=[
            ("view", "View on Screen"),
            ("csv", "Download as CSV"),
            ("excel", "Download as Excel"),
            ("pdf", "Download as PDF"),
        ],
        widget=forms.Select(
            attrs={"class": INPUT_CLASSES}
        ),
    )


class ApplicantsReportForm(BaseReportFilterForm):
    """Filter form for all applicants report."""

    status = forms.ChoiceField(
        label="Status",
        required=False,
        choices=[
            ("", "All Statuses"),
            ("active", "Active"),
            ("rejected", "Rejected"),
            ("approved", "Approved"),
            ("pending", "Pending"),
        ],
        widget=forms.Select(attrs={"class": INPUT_CLASSES}),
    )
    search_name = forms.CharField(
        label="Search by Name",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "Applicant name...",
            }
        ),
    )


class ApprovedLoansReportForm(BaseReportFilterForm):
    """Filter form for approved loans report."""

    min_amount = forms.DecimalField(
        label="Minimum Loan Amount",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": INPUT_CLASSES,
                "step": "0.01",
                "placeholder": "0.00",
            }
        ),
    )
    max_amount = forms.DecimalField(
        label="Maximum Loan Amount",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": INPUT_CLASSES,
                "step": "0.01",
                "placeholder": "0.00",
            }
        ),
    )


class ReleasedMotorsReportForm(BaseReportFilterForm):
    """Filter form for released motors report."""

    brand = forms.CharField(
        label="Brand",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "e.g., Honda, Yamaha...",
            }
        ),
    )
    color = forms.CharField(
        label="Color",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "Color...",
            }
        ),
    )


class OngoingLoansReportForm(BaseReportFilterForm):
    """Filter form for ongoing loans report."""

    min_outstanding = forms.DecimalField(
        label="Minimum Outstanding Balance",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": INPUT_CLASSES,
                "step": "0.01",
                "placeholder": "0.00",
            }
        ),
    )
    max_outstanding = forms.DecimalField(
        label="Maximum Outstanding Balance",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": INPUT_CLASSES,
                "step": "0.01",
                "placeholder": "0.00",
            }
        ),
    )
    payment_status = forms.ChoiceField(
        label="Payment Status",
        required=False,
        choices=[
            ("", "All Statuses"),
            ("on_time", "On Time"),
            ("overdue", "Overdue"),
            ("partial", "Partially Paid"),
        ],
        widget=forms.Select(attrs={"class": INPUT_CLASSES}),
    )


class MotorcycleStatusReportForm(BaseReportFilterForm):
    """Filter form for motorcycle status report."""

    status = forms.ChoiceField(
        label="Status",
        required=False,
        choices=[
            ("", "All Statuses"),
            ("released", "Released"),
            ("impounded", "Impounded"),
            ("transferred", "Transferred"),
            ("disposed", "Disposed"),
        ],
        widget=forms.Select(attrs={"class": INPUT_CLASSES}),
    )
    location = forms.CharField(
        label="Location",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "Storage location...",
            }
        ),
    )


class PaymentReconciliationReportForm(BaseReportFilterForm):
    """Filter form for payment reconciliation report."""

    payment_method = forms.ChoiceField(
        label="Payment Method",
        required=False,
        choices=[
            ("", "All Methods"),
            ("cash", "Cash"),
            ("check", "Check"),
            ("bank_transfer", "Bank Transfer"),
            ("credit_card", "Credit Card"),
            ("mobile_money", "Mobile Money"),
            ("other", "Other"),
        ],
        widget=forms.Select(attrs={"class": INPUT_CLASSES}),
    )
    reconciliation_status = forms.ChoiceField(
        label="Reconciliation Status",
        required=False,
        choices=[
            ("", "All"),
            ("reconciled", "Reconciled"),
            ("unreconciled", "Unreconciled"),
        ],
        widget=forms.Select(attrs={"class": INPUT_CLASSES}),
    )


class ComprehensiveReportsFilterForm(forms.Form):
    """Filter form for comprehensive reports dashboard."""

    start_date = forms.DateField(
        label="Start Date",
        required=False,
        widget=forms.DateInput(
            attrs={"class": INPUT_CLASSES, "type": "date"}
        ),
        help_text="Filter data from this date",
    )
    end_date = forms.DateField(
        label="End Date",
        required=False,
        widget=forms.DateInput(
            attrs={"class": INPUT_CLASSES, "type": "date"}
        ),
        help_text="Filter data up to this date",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default dates: last 30 days
        if not self.is_bound or not self.data.get('start_date'):
            self.fields['start_date'].initial = date.today() - timedelta(days=30)
        if not self.is_bound or not self.data.get('end_date'):
            self.fields['end_date'].initial = date.today()
