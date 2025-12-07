from decimal import Decimal
from typing import Any, Dict
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.urls import reverse
from django.views.generic import FormView, TemplateView
from django.utils import timezone

from motofinai.apps.inventory.models import Motor
from motofinai.apps.loans.models import LoanApplication, PaymentSchedule
from motofinai.apps.payments.models import Payment
from motofinai.apps.pos.models import POSSession
from motofinai.apps.repossession.models import RepossessionCase
from motofinai.apps.reports.forms import (
    ApplicantsReportForm,
    ApprovedLoansReportForm,
    OngoingLoansReportForm,
    PaymentReconciliationReportForm,
    ReleasedMotorsReportForm,
    MotorcycleStatusReportForm,
    ComprehensiveReportsFilterForm,
)
from motofinai.apps.reports.models import ReportSchedule


class BaseReportView(LoginRequiredMixin, FormView):
    template_name = "pages/reports/base_report.html"
    required_roles = ("admin", "finance")
    form_class = None
    report_title = ""
    report_description = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["report_title"] = self.report_title
        context["report_description"] = self.report_description
        context["breadcrumbs"] = [
            {"label": "Reports", "url": reverse("reports:list")},
            {"label": self.report_title},
        ]
        return context

    def get_report_data(self, filters):
        return {}

    def form_valid(self, form):
        filters = form.cleaned_data
        export_format = filters.pop("export_format", "view")
        report_data = self.get_report_data(filters)
        if export_format == "view":
            context = self.get_context_data(form=form)
            context.update(report_data)
            return self.render_to_response(context)
        return self.render_to_response(self.get_context_data(form=form))



class ApplicantsReportView(BaseReportView):
    form_class = ApplicantsReportForm
    template_name = "pages/reports/applicants_report.html"
    report_title = "All Applicants Report"
    report_description = "View all loan applicants with their application status and details."

    def get_report_data(self, filters):
        queryset = LoanApplication.objects.select_related("applicant_address")
        if filters.get("status"):
            queryset = queryset.filter(status=filters["status"])
        if filters.get("search_name"):
            search = filters["search_name"]
            queryset = queryset.filter(
                Q(applicant_first_name__icontains=search)
                | Q(applicant_last_name__icontains=search)
            )
        if filters.get("date_from"):
            queryset = queryset.filter(created_at__date__gte=filters["date_from"])
        if filters.get("date_to"):
            queryset = queryset.filter(created_at__date__lte=filters["date_to"])
        return {
            "applicants": queryset,
            "total_count": queryset.count(),
            "status_summary": dict(
                queryset.values("status").annotate(count=Count("id"))
            ),
        }


class ApprovedLoansReportView(BaseReportView):
    form_class = ApprovedLoansReportForm
    template_name = "pages/reports/approved_loans_report.html"
    report_title = "Approved Loans Report"
    report_description = "View all loans that have been approved with their terms and details."

    def get_report_data(self, filters):
        queryset = LoanApplication.objects.filter(status=LoanApplication.Status.APPROVED).select_related("financing_term")
        if filters.get("min_amount"):
            queryset = queryset.filter(loan_amount__gte=filters["min_amount"])
        if filters.get("max_amount"):
            queryset = queryset.filter(loan_amount__lte=filters["max_amount"])
        if filters.get("date_from"):
            queryset = queryset.filter(approved_at__date__gte=filters["date_from"])
        if filters.get("date_to"):
            queryset = queryset.filter(approved_at__date__lte=filters["date_to"])
        total_approved = queryset.aggregate(Sum("loan_amount"))["loan_amount__sum"] or Decimal("0.00")
        return {
            "approved_loans": queryset,
            "total_count": queryset.count(),
            "total_approved_amount": total_approved,
            "average_amount": (total_approved / queryset.count() if queryset.count() > 0 else Decimal("0.00")),
        }


class ReleasedMotorsReportView(BaseReportView):
    form_class = ReleasedMotorsReportForm
    template_name = "pages/reports/released_motors_report.html"
    report_title = "Released Motors Report"
    report_description = "View all motorcycles that have been released to borrowers."

    def get_report_data(self, filters):
        queryset = LoanApplication.objects.filter(status=LoanApplication.Status.ACTIVE).select_related("motor")
        if filters.get("brand"):
            queryset = queryset.filter(motor__brand__icontains=filters["brand"])
        if filters.get("color"):
            queryset = queryset.filter(motor__color__icontains=filters["color"])
        if filters.get("date_from"):
            queryset = queryset.filter(activated_at__date__gte=filters["date_from"])
        if filters.get("date_to"):
            queryset = queryset.filter(activated_at__date__lte=filters["date_to"])
        return {
            "released_motors": queryset,
            "total_count": queryset.count(),
            "by_brand": dict(queryset.values("motor__brand").annotate(count=Count("id"))),
        }


class OngoingLoansReportView(BaseReportView):
    form_class = OngoingLoansReportForm
    template_name = "pages/reports/ongoing_loans_report.html"
    report_title = "Ongoing Loans Report"
    report_description = "View all active loans with current payment status and outstanding balance."

    def get_report_data(self, filters):
        queryset = LoanApplication.objects.filter(status=LoanApplication.Status.ACTIVE).prefetch_related("payment_schedules")
        loans_data = []
        for loan in queryset:
            outstanding_schedules = loan.payment_schedules.exclude(status=PaymentSchedule.Status.PAID)
            outstanding_amount = sum((s.total_amount for s in outstanding_schedules), Decimal("0.00"))
            if filters.get("min_outstanding") and outstanding_amount < Decimal(str(filters["min_outstanding"])):
                continue
            if filters.get("max_outstanding") and outstanding_amount > Decimal(str(filters["max_outstanding"])):
                continue
            loans_data.append({"loan": loan, "outstanding_amount": outstanding_amount, "remaining_schedules": outstanding_schedules.count()})
        total_outstanding = sum((item["outstanding_amount"] for item in loans_data), Decimal("0.00"))
        return {"ongoing_loans": loans_data, "total_count": len(loans_data), "total_outstanding": total_outstanding}


class MotorcycleStatusReportView(BaseReportView):
    form_class = MotorcycleStatusReportForm
    template_name = "pages/reports/motorcycle_status_report.html"
    report_title = "Motorcycle Status Report"
    report_description = "View status and location information for all motorcycles in the system."

    def get_report_data(self, filters):
        from motofinai.apps.inventory.models import Motor
        queryset = Motor.objects.select_related("current_location").all()
        if filters.get("location"):
            queryset = queryset.filter(current_location__name__icontains=filters["location"])
        return {"motorcycles": queryset, "total_count": queryset.count()}


class PaymentReconciliationReportView(BaseReportView):
    form_class = PaymentReconciliationReportForm
    template_name = "pages/reports/payment_reconciliation_report.html"
    report_title = "Payment Reconciliation Report"
    report_description = "Verify and reconcile all payments collected against schedules and POS sessions."

    def get_report_data(self, filters):
        queryset = Payment.objects.select_related("loan_application", "schedule")
        if filters.get("payment_method"):
            queryset = queryset.filter(payment_method=filters["payment_method"])
        if filters.get("date_from"):
            queryset = queryset.filter(payment_date__gte=filters["date_from"])
        if filters.get("date_to"):
            queryset = queryset.filter(payment_date__lte=filters["date_to"])
        if filters.get("reconciliation_status") == "reconciled":
            queryset = queryset.filter(reconciled=True)
        elif filters.get("reconciliation_status") == "unreconciled":
            queryset = queryset.filter(reconciled=False)
        total_collected = queryset.aggregate(Sum("amount"))["amount__sum"] or Decimal("0.00")
        reconciled_count = queryset.filter(reconciled=True).count()
        unreconciled_count = queryset.filter(reconciled=False).count()
        sessions = POSSession.objects.all()
        session_total = sessions.aggregate(total=Sum("total_collected"))["total"] or Decimal("0.00")
        return {
            "payments": queryset,
            "total_count": queryset.count(),
            "total_collected": total_collected,
            "reconciled_count": reconciled_count,
            "unreconciled_count": unreconciled_count,
            "pos_sessions": sessions,
            "pos_session_total": session_total,
        }


class ReportListView(LoginRequiredMixin, TemplateView):
    template_name = "pages/reports/report_list.html"
    required_roles = ("admin", "finance")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["reports"] = [
            {"title": "All Applicants", "description": "View all loan applicants", "url": reverse("reports:applicants"), "icon": "users"},
            {"title": "Approved Loans", "description": "View all approved loans", "url": reverse("reports:approved_loans"), "icon": "check-circle"},
            {"title": "Released Motors", "description": "View all released motorcycles", "url": reverse("reports:released_motors"), "icon": "truck"},
            {"title": "Ongoing Loans", "description": "View all ongoing loans", "url": reverse("reports:ongoing_loans"), "icon": "arrow-right-circle"},
            {"title": "Motorcycle Status", "description": "View motorcycle locations and status", "url": reverse("reports:motorcycle_status"), "icon": "map"},
            {"title": "Payment Reconciliation", "description": "Reconcile payments and verify collections", "url": reverse("reports:payment_reconciliation"), "icon": "calculator"},
        ]
        context["breadcrumbs"] = [{"label": "Reports"}]
        return context


class ComprehensiveReportsDashboardView(LoginRequiredMixin, FormView):
    """Comprehensive reports dashboard with charts and analytics."""
    
    template_name = "pages/reports/comprehensive_dashboard.html"
    form_class = ComprehensiveReportsFilterForm
    required_roles = ("admin", "finance")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get('form') or self.get_form()
        
        # Get date filters
        start_date = form.initial.get('start_date') if hasattr(form, 'initial') else timezone.now().date() - timedelta(days=30)
        end_date = form.initial.get('end_date') if hasattr(form, 'initial') else timezone.now().date()
        
        if form.is_bound and form.is_valid():
            start_date = form.cleaned_data.get('start_date') or start_date
            end_date = form.cleaned_data.get('end_date') or end_date
        
        # KPI Cards Data
        total_loans = LoanApplication.objects.count()
        active_loans = LoanApplication.objects.filter(status='active').count()
        completed_loans = LoanApplication.objects.filter(status='completed').count()
        
        # Collection rate
        schedules_agg = PaymentSchedule.objects.aggregate(
            due_total=Sum('total_amount', filter=Q(status='due')),
            overdue_total=Sum('total_amount', filter=Q(status='overdue')),
            paid_total=Sum('total_amount', filter=Q(status='paid')),
        )
        total_expected = (schedules_agg['due_total'] or Decimal('0')) + \
                        (schedules_agg['overdue_total'] or Decimal('0')) + \
                        (schedules_agg['paid_total'] or Decimal('0'))
        paid_total = schedules_agg['paid_total'] or Decimal('0')
        collection_rate = (paid_total / total_expected * 100) if total_expected > 0 else 0
        
        # Repossession rate
        total_repossessions = RepossessionCase.objects.count()
        repossession_rate = (total_repossessions / total_loans * 100) if total_loans > 0 else 0
        
        # Motors loaned
        motors_loaned_count = Motor.objects.filter(loan_applications__status='active').distinct().count()
        
        # Motors loaned by brand
        motors_by_brand = Motor.objects.filter(
            loan_applications__status='active'
        ).values('brand').annotate(
            count=Count('id', distinct=True)
        ).order_by('-count')[:10]
        
        motors_brand_labels = [item['brand'] for item in motors_by_brand]
        motors_brand_data = [item['count'] for item in motors_by_brand]
        
        # Payment status distribution
        payment_status = PaymentSchedule.objects.aggregate(
            due_count=Count('id', filter=Q(status='due')),
            overdue_count=Count('id', filter=Q(status='overdue')),
            paid_count=Count('id', filter=Q(status='paid')),
        )
        
        # Loan status distribution
        loan_status = LoanApplication.objects.aggregate(
            pending_count=Count('id', filter=Q(status='pending')),
            approved_count=Count('id', filter=Q(status='approved')),
            active_count=Count('id', filter=Q(status='active')),
            completed_count=Count('id', filter=Q(status='completed')),
        )
        
        # Monthly collection trends (last 12 months)
        monthly_trends = []
        monthly_labels = []
        current_date = timezone.now().date()

        for i in range(11, -1, -1):
            target_month = current_date - relativedelta(months=i)
            month_start = target_month.replace(day=1)
            next_month = month_start + relativedelta(months=1)
            month_end = next_month - timedelta(days=1)

            month_total = Payment.objects.filter(
                payment_date__gte=month_start,
                payment_date__lte=month_end
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            monthly_trends.append(float(month_total))
            monthly_labels.append(month_start.strftime('%b %Y'))
        
        # Repossession cases by status
        repossession_by_status = RepossessionCase.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        repo_status_labels = [item['status'].title() for item in repossession_by_status]
        repo_status_data = [item['count'] for item in repossession_by_status]
        
        context.update({
            'start_date': start_date,
            'end_date': end_date,
            # KPIs
            'total_loans': total_loans,
            'collection_rate': round(collection_rate, 2),
            'repossession_rate': round(repossession_rate, 2),
            'motors_loaned_count': motors_loaned_count,
            # Chart data (JSON serialized)
            'motors_brand_labels_json': json.dumps(motors_brand_labels),
            'motors_brand_data_json': json.dumps(motors_brand_data),
            'payment_status_labels_json': json.dumps(['Due', 'Overdue', 'Paid']),
            'payment_status_data_json': json.dumps([
                payment_status['due_count'],
                payment_status['overdue_count'],
                payment_status['paid_count'],
            ]),
            'loan_status_labels_json': json.dumps(['Pending', 'Approved', 'Active', 'Completed']),
            'loan_status_data_json': json.dumps([
                loan_status['pending_count'],
                loan_status['approved_count'],
                loan_status['active_count'],
                loan_status['completed_count'],
            ]),
            'monthly_labels_json': json.dumps(monthly_labels),
            'monthly_data_json': json.dumps(monthly_trends),
            'repo_status_labels_json': json.dumps(repo_status_labels),
            'repo_status_data_json': json.dumps(repo_status_data),
            # Breadcrumbs
            'breadcrumbs': [
                {"label": "Reports", "url": reverse("reports:list")},
                {"label": "Comprehensive Dashboard"},
            ],
        })
        
        return context

    def form_valid(self, form):
        # Just refresh the page with filtered data
        return self.render_to_response(self.get_context_data(form=form))
