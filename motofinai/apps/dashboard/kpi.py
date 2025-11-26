"""
KPI calculation utilities for Admin and Finance dashboards
"""
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from django.apps import apps


class DashboardKPI:
    """Base class for KPI calculations"""

    @staticmethod
    def get_loan_kpis():
        """Calculate loan-related KPIs"""
        LoanApplication = apps.get_model('loans', 'LoanApplication')

        total_loans = LoanApplication.objects.count()
        approved_loans = LoanApplication.objects.filter(status='approved').count()
        active_loans = LoanApplication.objects.filter(status='active').count()
        completed_loans = LoanApplication.objects.filter(status='completed').count()
        pending_loans = LoanApplication.objects.filter(status='pending').count()

        # Calculate total loan value
        total_loan_value = LoanApplication.objects.filter(
            status__in=['approved', 'active', 'completed']
        ).aggregate(total=Sum('loan_amount'))['total'] or Decimal('0')

        # Average loan amount
        avg_loan_amount = LoanApplication.objects.filter(
            status__in=['approved', 'active', 'completed']
        ).aggregate(avg=Avg('loan_amount'))['avg'] or Decimal('0')

        return {
            'total_loans': total_loans,
            'approved_loans': approved_loans,
            'active_loans': active_loans,
            'completed_loans': completed_loans,
            'pending_loans': pending_loans,
            'total_loan_value': total_loan_value,
            'avg_loan_amount': avg_loan_amount,
        }

    @staticmethod
    def get_payment_kpis(month=None):
        """Calculate payment-related KPIs"""
        PaymentSchedule = apps.get_model('loans', 'PaymentSchedule')
        Payment = apps.get_model('payments', 'Payment')

        # Default to current month
        if month is None:
            month = timezone.now()

        month_start = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month.month == 12:
            month_end = month.replace(year=month.year + 1, month=1, day=1)
        else:
            month_end = month.replace(month=month.month + 1, day=1)

        # Total collected this month
        total_collected = Payment.objects.filter(
            payment_date__gte=month_start,
            payment_date__lt=month_end
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # Pending payments (due this month but not paid)
        pending_amount = PaymentSchedule.objects.filter(
            due_date__gte=month_start,
            due_date__lt=month_end,
            status='due'
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')

        # Overdue payments
        today = timezone.now().date()
        overdue_amount = PaymentSchedule.objects.filter(
            due_date__lt=today,
            status='overdue'
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')

        overdue_count = PaymentSchedule.objects.filter(
            due_date__lt=today,
            status='overdue'
        ).count()

        # Collection rate (paid / (paid + pending + overdue))
        total_expected = total_collected + pending_amount + overdue_amount
        collection_rate = (total_collected / total_expected * 100) if total_expected > 0 else Decimal('0')

        return {
            'total_collected': total_collected,
            'pending_amount': pending_amount,
            'overdue_amount': overdue_amount,
            'overdue_count': overdue_count,
            'collection_rate': collection_rate,
            'month': month,
        }

    @staticmethod
    def get_risk_kpis():
        """Calculate risk assessment KPIs"""
        RiskAssessment = apps.get_model('risk', 'RiskAssessment')

        total_assessments = RiskAssessment.objects.count()

        risk_distribution = RiskAssessment.objects.values('risk_level').annotate(
            count=Count('id')
        )

        # Convert to dict for easier access
        distribution = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0}
        for item in risk_distribution:
            distribution[item['risk_level']] = item['count']

        # Average risk score
        avg_score = RiskAssessment.objects.aggregate(
            avg=Avg('score')
        )['avg'] or Decimal('0')

        # High risk percentage
        high_risk_pct = (distribution['HIGH'] / total_assessments * 100) if total_assessments > 0 else 0

        return {
            'total_assessments': total_assessments,
            'low_risk': distribution['LOW'],
            'medium_risk': distribution['MEDIUM'],
            'high_risk': distribution['HIGH'],
            'avg_score': avg_score,
            'high_risk_pct': high_risk_pct,
        }

    @staticmethod
    def get_repossession_kpis():
        """Calculate repossession-related KPIs"""
        RepossessionCase = apps.get_model('repossession', 'RepossessionCase')

        total_cases = RepossessionCase.objects.count()

        status_counts = RepossessionCase.objects.values('status').annotate(
            count=Count('id')
        )

        # Convert to dict
        status_distribution = {
            'WARNING': 0,
            'ACTIVE': 0,
            'REMINDER': 0,
            'RECOVERED': 0,
            'CLOSED': 0,
        }
        for item in status_counts:
            status_distribution[item['status']] = item['count']

        # Critical cases (active + reminder)
        critical_cases = status_distribution['ACTIVE'] + status_distribution['REMINDER']

        # Recovery rate
        resolved_cases = status_distribution['RECOVERED'] + status_distribution['CLOSED']
        recovery_rate = (resolved_cases / total_cases * 100) if total_cases > 0 else 0

        # Total overdue amount across active cases
        total_overdue = RepossessionCase.objects.filter(
            status__in=['WARNING', 'ACTIVE', 'REMINDER']
        ).aggregate(total=Sum('total_overdue_amount'))['total'] or Decimal('0')

        return {
            'total_cases': total_cases,
            'critical_cases': critical_cases,
            'warning': status_distribution['WARNING'],
            'active': status_distribution['ACTIVE'],
            'reminder': status_distribution['REMINDER'],
            'recovered': status_distribution['RECOVERED'],
            'closed': status_distribution['CLOSED'],
            'recovery_rate': recovery_rate,
            'total_overdue': total_overdue,
        }

    @staticmethod
    def get_inventory_kpis():
        """Calculate inventory-related KPIs"""
        Motor = apps.get_model('inventory', 'Motor')
        LoanApplication = apps.get_model('loans', 'LoanApplication')

        total_units = Motor.objects.count()

        # Count motors by deriving status from loan applications
        available_count = 0
        reserved_count = 0
        sold_count = 0
        repossessed_count = 0

        for motor in Motor.objects.all():
            status = motor.status  # This is derived from loan applications
            if status == 'available':
                available_count += 1
            elif status == 'reserved':
                reserved_count += 1
            elif status == 'sold':
                sold_count += 1
            elif status == 'repossessed':
                repossessed_count += 1

        status_distribution = {
            'available': available_count,
            'reserved': reserved_count,
            'sold': sold_count,
            'repossessed': repossessed_count,
        }

        # Total inventory value (all motors)
        total_value = Motor.objects.aggregate(
            total=Sum('purchase_price')
        )['total'] or Decimal('0')

        # Average motor price
        avg_price = Motor.objects.aggregate(
            avg=Avg('purchase_price')
        )['avg'] or Decimal('0')

        return {
            'total_units': total_units,
            'available': status_distribution['available'],
            'reserved': status_distribution['reserved'],
            'sold': status_distribution['sold'],
            'repossessed': status_distribution['repossessed'],
            'total_value': total_value,
            'avg_price': avg_price,
        }

    @staticmethod
    def get_user_kpis():
        """Calculate user-related KPIs"""
        User = apps.get_model('users', 'User')

        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        admin_users = User.objects.filter(role='admin').count()
        finance_users = User.objects.filter(role='finance').count()

        return {
            'total_users': total_users,
            'active_users': active_users,
            'admin_users': admin_users,
            'finance_users': finance_users,
        }

    @staticmethod
    def get_audit_kpis(days=30):
        """Calculate audit trail KPIs"""
        AuditLogEntry = apps.get_model('audit', 'AuditLogEntry')

        since = timezone.now() - timedelta(days=days)

        total_events = AuditLogEntry.objects.filter(
            created_at__gte=since
        ).count()

        # Events by action
        action_counts = AuditLogEntry.objects.filter(
            created_at__gte=since
        ).values('action').annotate(count=Count('id'))

        # Recent logins
        recent_logins = AuditLogEntry.objects.filter(
            action='LOGIN',
            created_at__gte=since
        ).count()

        return {
            'total_events': total_events,
            'recent_logins': recent_logins,
            'action_counts': list(action_counts),
            'days': days,
        }

    @staticmethod
    def get_recent_activities(limit=10):
        """Get recent system activities"""
        AuditLogEntry = apps.get_model('audit', 'AuditLogEntry')

        return AuditLogEntry.objects.select_related('actor').order_by('-created_at')[:limit]


class AdminDashboardKPI(DashboardKPI):
    """Admin-specific KPI aggregator"""

    @classmethod
    def get_all_kpis(cls):
        """Get all KPIs for admin dashboard"""
        return {
            'loans': cls.get_loan_kpis(),
            'payments': cls.get_payment_kpis(),
            'risk': cls.get_risk_kpis(),
            'repossession': cls.get_repossession_kpis(),
            'inventory': cls.get_inventory_kpis(),
            'users': cls.get_user_kpis(),
            'audit': cls.get_audit_kpis(),
            'recent_activities': cls.get_recent_activities(),
        }


class FinanceDashboardKPI(DashboardKPI):
    """Finance-specific KPI aggregator"""

    @classmethod
    def get_all_kpis(cls):
        """Get all KPIs for finance dashboard"""
        return {
            'loans': cls.get_loan_kpis(),
            'payments': cls.get_payment_kpis(),
            'risk': cls.get_risk_kpis(),
            'repossession': cls.get_repossession_kpis(),
            'recent_activities': cls.get_recent_activities(limit=5),
        }


class LoanOfficerDashboardKPI(DashboardKPI):
    """Loan Officer-specific KPI aggregator"""

    @classmethod
    def get_all_kpis(cls):
        """Get all KPIs for loan officer dashboard"""
        return {
            'loans': cls.get_loan_kpis(),
            'payments': cls.get_payment_kpis(),
            'repossession': cls.get_repossession_kpis(),
            'recent_activities': cls.get_recent_activities(limit=8),
        }
