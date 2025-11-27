"""CSV export utilities for loan applications."""
import csv
from typing import Any

from django.http import HttpResponse

from .models import LoanApplication


def export_loan_applications_csv(queryset) -> HttpResponse:
    """Export loan applications to CSV format."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="loan_applications.csv"'

    writer = csv.writer(response)

    # Write header
    writer.writerow([
        'Application ID',
        'Applicant First Name',
        'Applicant Last Name',
        'Email',
        'Phone',
        'Motorcycle Brand',
        'Motorcycle Model',
        'Loan Amount',
        'Down Payment',
        'Term (Years)',
        'Interest Rate',
        'Monthly Payment',
        'Status',
        'Employment Status',
        'Applied Date',
    ])

    # Write data rows
    for app in queryset.select_related('motor', 'financing_term'):
        writer.writerow([
            app.pk,
            app.applicant_first_name,
            app.applicant_last_name,
            app.applicant_email,
            app.applicant_phone,
            app.motor.brand if app.motor else '',
            app.motor.model if app.motor else '',
            app.loan_amount,
            app.down_payment,
            app.financing_term.term_years if app.financing_term else '',
            app.financing_term.interest_rate if app.financing_term else '',
            app.monthly_payment,
            app.get_status_display(),
            app.get_employment_status_display() if app.employment_status else '',
            app.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])

    return response
