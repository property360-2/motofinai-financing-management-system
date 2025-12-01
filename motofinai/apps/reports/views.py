from decimal import Decimal
from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.urls import reverse
from django.views.generic import FormView, TemplateView

from motofinai.apps.loans.models import LoanApplication, PaymentSchedule
from motofinai.apps.payments.models import Payment
from motofinai.apps.pos.models import POSSession
from motofinai.apps.reports.forms import (
    ApplicantsReportForm,
    ApprovedLoansReportForm,
    OngoingLoansReportForm,
    PaymentReconciliationReportForm,
    ReleasedMotorsReportForm,
    MotorcycleStatusReportForm,
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
