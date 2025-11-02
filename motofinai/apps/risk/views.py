from __future__ import annotations

from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, TemplateView

from motofinai.apps.loans.models import LoanApplication

from .forms import RiskAssessmentInputForm
from .models import RiskAssessment


class RiskAssessmentDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "pages/risk/dashboard.html"
    context_object_name = "assessments"
    required_roles = ("admin", "finance")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        assessments = (
            RiskAssessment.objects.select_related(
                "loan_application",
                "loan_application__motor",
            )
            .order_by("-updated_at")
        )
        distribution = assessments.by_level()
        context.update(
            {
                "assessments": assessments,
                "distribution": distribution,
                "total_assessments": assessments.count(),
                "high_risk_count": distribution.get(RiskAssessment.RiskLevel.HIGH, 0),
                "medium_risk_count": distribution.get(RiskAssessment.RiskLevel.MEDIUM, 0),
                "low_risk_count": distribution.get(RiskAssessment.RiskLevel.LOW, 0),
                "average_score": assessments.aggregate(avg=models.Avg("score"))["avg"],
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
