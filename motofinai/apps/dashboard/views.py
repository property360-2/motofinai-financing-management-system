"""
Dashboard views for Admin and Finance roles
"""
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone

from .kpi import AdminDashboardKPI, FinanceDashboardKPI, LoanOfficerDashboardKPI
from .reports import LoanReport, PaymentReport, RiskReport, InventoryReport


class AdminDashboardView(LoginRequiredMixin, TemplateView):
    """Admin dashboard with comprehensive KPIs"""
    template_name = 'pages/dashboard/admin_dashboard.html'
    required_roles = ['admin']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all KPIs
        kpis = AdminDashboardKPI.get_all_kpis()

        context.update({
            'page_title': 'Admin Dashboard',
            'kpis': kpis,
            'current_month': timezone.now().strftime('%B %Y'),
        })

        return context


class FinanceDashboardView(LoginRequiredMixin, TemplateView):
    """Finance dashboard with role-specific metrics"""
    template_name = 'pages/dashboard/finance_dashboard.html'
    required_roles = ['finance', 'admin']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get finance-specific KPIs
        kpis = FinanceDashboardKPI.get_all_kpis()

        context.update({
            'page_title': 'Finance Dashboard',
            'kpis': kpis,
            'current_month': timezone.now().strftime('%B %Y'),
        })

        return context


class LoanOfficerDashboardView(LoginRequiredMixin, TemplateView):
    """Loan Officer dashboard with application tracking and repossession alerts"""
    template_name = 'pages/dashboard/loan_officer_dashboard.html'
    required_roles = ['finance', 'admin']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from motofinai.apps.loans.models import LoanApplication
        from motofinai.apps.repossession.models import RepossessionCase

        # Get loan officer KPIs
        kpis = LoanOfficerDashboardKPI.get_all_kpis()

        # Get recent applications categorized
        recent_pending = LoanApplication.objects.filter(
            status='pending'
        ).select_related('applicant', 'motor').order_by('-created_at')[:10]

        recent_approved = LoanApplication.objects.filter(
            status='approved'
        ).select_related('applicant', 'motor').order_by('-created_at')[:10]

        recent_active = LoanApplication.objects.filter(
            status='active'
        ).select_related('applicant', 'motor').order_by('-created_at')[:10]

        # Get repossession alerts categorized by risk
        high_risk_repos = RepossessionCase.objects.filter(
            status='active'
        ).select_related('loan__applicant', 'loan__motor').order_by('-created_at')[:10]

        medium_risk_repos = RepossessionCase.objects.filter(
            status='reminder'
        ).select_related('loan__applicant', 'loan__motor').order_by('-created_at')[:10]

        low_risk_repos = RepossessionCase.objects.filter(
            status='warning'
        ).select_related('loan__applicant', 'loan__motor').order_by('-created_at')[:10]

        context.update({
            'page_title': 'Loan Officer Dashboard',
            'kpis': kpis,
            'current_month': timezone.now().strftime('%B %Y'),
            'recent_pending': recent_pending,
            'recent_approved': recent_approved,
            'recent_active': recent_active,
            'high_risk_repos': high_risk_repos,
            'medium_risk_repos': medium_risk_repos,
            'low_risk_repos': low_risk_repos,
        })

        return context


# Report Export Views

class ExportLoansView(LoginRequiredMixin, View):
    """Export loans to Excel"""
    required_roles = ['admin', 'finance']

    def get(self, request):
        return LoanReport.generate_excel()


class ExportPaymentsView(LoginRequiredMixin, View):
    """Export payments to Excel"""
    required_roles = ['admin', 'finance']

    def get(self, request):
        return PaymentReport.generate_excel()


class ExportRiskView(LoginRequiredMixin, View):
    """Export risk assessments to Excel"""
    required_roles = ['admin', 'finance']

    def get(self, request):
        return RiskReport.generate_excel()


class ExportInventoryView(LoginRequiredMixin, View):
    """Export inventory to Excel"""
    required_roles = ['admin']

    def get(self, request):
        return InventoryReport.generate_excel()
