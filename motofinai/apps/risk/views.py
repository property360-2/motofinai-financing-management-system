from __future__ import annotations

from typing import Any, Dict
from datetime import datetime, timedelta
from calendar import monthrange
import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Avg, Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views import View
from django.views.generic import DetailView, TemplateView

from motofinai.apps.loans.models import LoanApplication

from .forms import RiskAssessmentInputForm
from .models import RiskAssessment


class RiskAssessmentDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "pages/risk/dashboard.html"
    context_object_name = "assessments"
    required_roles = ("admin", "finance")

    def get_date_range(self):
        """Get date range from request or default to current month"""
        now = timezone.now()

        # Get start and end dates from GET parameters
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')

        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                # Fall back to current month if invalid dates
                start_date = now.replace(day=1).date()
                _, last_day = monthrange(now.year, now.month)
                end_date = now.replace(day=last_day).date()
        else:
            # Default to current month
            start_date = now.replace(day=1).date()
            _, last_day = monthrange(now.year, now.month)
            end_date = now.replace(day=last_day).date()

        return start_date, end_date

    def get_queryset(self):
        """Get filtered assessments based on date range, search, and risk level"""
        start_date, end_date = self.get_date_range()

        assessments = (
            RiskAssessment.objects.select_related(
                "loan_application",
                "loan_application__motor",
            )
            .filter(calculated_at__date__gte=start_date, calculated_at__date__lte=end_date)
            .order_by("-updated_at")
        )

        # Search filter
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            assessments = assessments.filter(
                Q(loan_application__applicant__first_name__icontains=search_query) |
                Q(loan_application__applicant__last_name__icontains=search_query) |
                Q(loan_application__applicant__email__icontains=search_query)
            )

        # Risk level filter
        risk_level = self.request.GET.get('risk_level', '').strip()
        if risk_level and risk_level in ['LOW', 'MEDIUM', 'HIGH']:
            assessments = assessments.filter(risk_level=risk_level)

        return assessments

    def get_chart_data(self):
        """Generate chart data for risk assessment visualization"""
        # Risk Distribution for Pie Chart
        all_assessments = RiskAssessment.objects.all()
        distribution = all_assessments.by_level()

        risk_distribution = {
            'labels': ['Low Risk', 'Medium Risk', 'High Risk'],
            'data': [
                distribution.get(RiskAssessment.RiskLevel.LOW, 0),
                distribution.get(RiskAssessment.RiskLevel.MEDIUM, 0),
                distribution.get(RiskAssessment.RiskLevel.HIGH, 0),
            ]
        }

        # Risk Factor Impact (last 6 months trend)
        now = timezone.now()
        risk_factors = []

        for i in range(5, -1, -1):
            month_date = now - timedelta(days=30 * i)
            month_start = month_date.replace(day=1).date()
            _, last_day = monthrange(month_date.year, month_date.month)
            month_end = month_date.replace(day=last_day).date()

            month_assessments = RiskAssessment.objects.filter(
                calculated_at__date__gte=month_start,
                calculated_at__date__lte=month_end
            )

            avg_score = month_assessments.aggregate(avg=Avg('score'))['avg'] or 0

            risk_factors.append({
                'month': month_date.strftime('%b'),
                'avg_score': round(float(avg_score), 2),
            })

        return {
            'risk_distribution': risk_distribution,
            'risk_factors': risk_factors,
        }

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        assessments = self.get_queryset()
        start_date, end_date = self.get_date_range()

        # Add pagination
        paginator = Paginator(assessments, 20)  # 20 items per page
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Calculate statistics on ALL assessments (not just paginated)
        distribution = assessments.by_level()
        avg_score = assessments.aggregate(avg=models.Avg("score"))["avg"] or 0

        # Get chart data and serialize to JSON
        chart_data = self.get_chart_data()
        chart_data_json = mark_safe(json.dumps(chart_data))

        context.update(
            {
                "assessments": page_obj,
                "page_obj": page_obj,
                "is_paginated": page_obj.has_other_pages(),
                "paginator": paginator,
                "distribution": distribution,
                "total_assessments": assessments.count(),
                "high_risk_count": distribution.get(RiskAssessment.RiskLevel.HIGH, 0),
                "medium_risk_count": distribution.get(RiskAssessment.RiskLevel.MEDIUM, 0),
                "low_risk_count": distribution.get(RiskAssessment.RiskLevel.LOW, 0),
                "average_score": round(float(avg_score), 2),
                "chart_data": chart_data_json,
                "start_date": start_date,
                "end_date": end_date,
                "search_query": self.request.GET.get('search', ''),
                "risk_level_filter": self.request.GET.get('risk_level', ''),
                "page_title": "AI Risk Scoring",
            }
        )
        return context


class RiskAssessmentDetailView(LoginRequiredMixin, DetailView):
    model = RiskAssessment
    template_name = "pages/risk/assessment_detail.html"
    context_object_name = "assessment"
    required_roles = ("admin", "finance")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        assessment = self.object
        loan = assessment.loan_application
        form = kwargs.get("form") or RiskAssessmentInputForm(
            initial={
                "base_score": assessment.base_score,
                "credit_score": assessment.credit_score,
                "notes": assessment.notes,
            }
        )
        context.update(
            {
                "loan": loan,
                "form": form,
                "schedules": loan.payment_schedules.order_by("sequence"),
            }
        )
        return context


class RiskAssessmentRecalculateView(LoginRequiredMixin, View):
    required_roles = ("admin", "finance")

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        assessment = get_object_or_404(RiskAssessment, pk=pk)
        form = RiskAssessmentInputForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            RiskAssessment.objects.evaluate_for_loan(
                assessment.loan_application,
                base_score=data["base_score"],
                credit_score=data["credit_score"],
                notes=data["notes"],
            )
            messages.success(request, "Risk assessment recalculated using the latest factors.")
            return redirect("risk:detail", pk=assessment.pk)
        detail_view = RiskAssessmentDetailView.as_view()
        return detail_view(request, pk=pk, form=form)


class LoanRiskEvaluateView(LoginRequiredMixin, View):
    required_roles = ("admin", "finance")

    def post(self, request: HttpRequest, loan_pk: int) -> HttpResponse:
        loan = get_object_or_404(LoanApplication, pk=loan_pk)
        assessment = RiskAssessment.objects.evaluate_for_loan(loan)
        messages.success(request, "Risk assessment generated for this application.")
        return redirect(reverse("risk:detail", args=[assessment.pk]))
