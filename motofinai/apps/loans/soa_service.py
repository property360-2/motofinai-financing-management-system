"""Service for generating Statement of Accounts (SOA) data."""

from decimal import Decimal
from typing import Dict, Any
from django.db.models import Sum, Q, DecimalField, Count

from motofinai.apps.loans.models import LoanApplication
from motofinai.apps.payments.models import Payment


class SOAService:
    """Service class for generating Statement of Accounts data."""

    @staticmethod
    def generate_soa_data(loan_id: int) -> Dict[str, Any]:
        """
        Generate comprehensive SOA data for a loan application.

        Args:
            loan_id: Primary key of the LoanApplication

        Returns:
            Dictionary containing all SOA data including customer info,
            loan summary, payment schedules, and calculations
        """
        # Fetch loan with related data
        loan = LoanApplication.objects.select_related(
            'motor', 'financing_term'
        ).prefetch_related(
            'payment_schedules__payment'
        ).get(pk=loan_id)

        # Customer information
        customer_data = {
            'name': loan.applicant_full_name,
            'email': loan.applicant_email,
            'phone': loan.applicant_phone,
        }

        # Loan summary
        # Use custom term if provided, otherwise use financing term
        term_years = loan.custom_term_years or loan.financing_term.term_years
        total_months = term_years * 12
        total_interest = loan.principal_amount * (loan.interest_rate / Decimal('100')) * Decimal(term_years)

        loan_data = {
            'id': loan.id,
            'motorcycle': loan.motor.display_name,
            'loan_amount': loan.loan_amount,
            'down_payment': loan.down_payment,
            'principal_amount': loan.principal_amount,
            'interest_rate': loan.interest_rate,
            'term_years': term_years,
            'total_months': total_months,
            'monthly_payment': loan.monthly_payment,
            'total_interest': total_interest,
            'status': loan.get_status_display(),
        }

        # Payment schedule aggregations
        schedules_agg = loan.payment_schedules.aggregate(
            due_total=Sum('total_amount', filter=Q(status='due'), output_field=DecimalField()),
            overdue_total=Sum('total_amount', filter=Q(status='overdue'), output_field=DecimalField()),
            paid_total=Sum('total_amount', filter=Q(status='paid'), output_field=DecimalField()),
            principal_total=Sum('principal_amount', output_field=DecimalField()),
            interest_total=Sum('interest_amount', output_field=DecimalField()),
            due_count=Count('id', filter=Q(status='due')),
            overdue_count=Count('id', filter=Q(status='overdue')),
            paid_count=Count('id', filter=Q(status='paid')),
        )

        # Calculate totals
        due_total = schedules_agg['due_total'] or Decimal('0.00')
        overdue_total = schedules_agg['overdue_total'] or Decimal('0.00')
        paid_total = schedules_agg['paid_total'] or Decimal('0.00')
        principal_total = schedules_agg['principal_total'] or Decimal('0.00')
        interest_total = schedules_agg['interest_total'] or Decimal('0.00')

        total_expected = principal_total + interest_total
        outstanding = due_total + overdue_total
        balance = total_expected - paid_total

        collection_rate = (paid_total / total_expected * 100) if total_expected > 0 else Decimal('0')

        summary_data = {
            'due_total': due_total,
            'overdue_total': overdue_total,
            'paid_total': paid_total,
            'outstanding': outstanding,
            'balance': balance,
            'collection_rate': round(collection_rate, 2),
            'total_expected': total_expected,
        }

        # Payment schedules with full details
        schedules = loan.payment_schedules.select_related('payment').order_by('sequence')
        schedules_list = []

        for schedule in schedules:
            schedule_data = {
                'sequence': schedule.sequence,
                'due_date': schedule.due_date,
                'principal_amount': schedule.principal_amount,
                'interest_amount': schedule.interest_amount,
                'total_amount': schedule.total_amount,
                'status': schedule.get_status_display(),
                'paid_at': schedule.paid_at,
            }

            # Add payment details if paid
            if hasattr(schedule, 'payment') and schedule.payment:
                payment = schedule.payment
                schedule_data['payment'] = {
                    'date': payment.payment_date,
                    'amount': payment.amount,
                    'method': payment.get_payment_method_display(),
                    'reference': payment.reference,
                    'recorded_by': payment.recorded_by.get_full_name() if payment.recorded_by else 'System',
                }
            else:
                schedule_data['payment'] = None

            schedules_list.append(schedule_data)

        # Payment history
        payments = Payment.objects.filter(
            loan_application=loan
        ).select_related('recorded_by', 'schedule').order_by('payment_date')

        payments_list = []
        for payment in payments:
            payments_list.append({
                'date': payment.payment_date,
                'amount': payment.amount,
                'method': payment.get_payment_method_display(),
                'reference': payment.reference,
                'schedule_sequence': payment.schedule.sequence if payment.schedule else None,
                'recorded_by': payment.recorded_by.get_full_name() if payment.recorded_by else 'System',
                'recorded_at': payment.recorded_at,
            })

        return {
            'customer': customer_data,
            'loan': loan_data,
            'summary': summary_data,
            'schedules': schedules_list,
            'payments': payments_list,
            'loan_object': loan,  # Include for template access
        }
