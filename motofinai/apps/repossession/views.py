from decimal import Decimal
from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import DetailView, FormView, TemplateView

from .forms import RepossessionCloseForm, RepossessionReminderForm
from .models import RepossessionCase


class RepossessionCaseListView(LoginRequiredMixin, TemplateView):
    template_name = "pages/repossession/case_list.html"
    required_roles = ("admin", "finance")

    def get_queryset(self):
        queryset = RepossessionCase.objects.select_related(
            "loan_application",
            "loan_application__motor",
        )
        status = self.request.GET.get("status")
        if status in dict(RepossessionCase.Status.choices):
            queryset = queryset.filter(status=status)
        return queryset

    def get_summary(self) -> Dict[str, Any]:
        open_cases = RepossessionCase.objects.open()
        aggregate = open_cases.aggregate(total_amount=Sum("total_overdue_amount"))
        total = aggregate["total_amount"] or Decimal("0.00")
        total = total.quantize(Decimal("0.01"))
        return {
            "open_count": open_cases.count(),
            "active_count": open_cases.filter(status=RepossessionCase.Status.ACTIVE).count(),
            "warning_count": open_cases.filter(status=RepossessionCase.Status.WARNING).count(),
            "reminder_count": open_cases.filter(status=RepossessionCase.Status.REMINDER).count(),
            "overdue_total": total,
        }

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        context.update(
            {
                "cases": queryset,
                "summary": self.get_summary(),
                "status_choices": RepossessionCase.Status.choices,
            }
        )
        return context


class RepossessionCaseDetailView(LoginRequiredMixin, DetailView):
    model = RepossessionCase
    template_name = "pages/repossession/case_detail.html"
    context_object_name = "case"
    required_roles = ("admin", "finance")

    def get_queryset(self):
        return super().get_queryset().select_related(
            "loan_application",
            "loan_application__motor",
        ).prefetch_related("events")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.setdefault("reminder_form", RepossessionReminderForm())
        context.setdefault("close_form", RepossessionCloseForm())
        loan = self.object.loan_application
        risk_assessment = getattr(loan, "risk_assessment", None)
        context["risk_assessment"] = risk_assessment
        return context


class RepossessionCaseReminderView(LoginRequiredMixin, FormView):
    form_class = RepossessionReminderForm
    required_roles = ("admin", "finance")

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.case = get_object_or_404(
            RepossessionCase.objects.select_related(
                "loan_application",
                "loan_application__motor",
            ).prefetch_related("events"),
            pk=kwargs["pk"],
        )
        if not self.case.is_open:
            raise Http404("This repossession case is already closed.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: RepossessionReminderForm) -> HttpResponse:
        self.case.record_reminder(form.cleaned_data["message"], user=self.request.user)
        messages.success(self.request, "Reminder recorded for the repossession case.")
        return redirect(self.get_success_url())

    def form_invalid(self, form: RepossessionReminderForm) -> HttpResponse:
        context = {
            "case": self.case,
            "reminder_form": form,
            "close_form": RepossessionCloseForm(),
        }
        return render(
            self.request,
            "pages/repossession/case_detail.html",
            context,
            status=400,
        )

    def get_success_url(self) -> str:
        return reverse("repossession:case-detail", args=[self.case.pk])


class RepossessionCaseCloseView(LoginRequiredMixin, FormView):
    form_class = RepossessionCloseForm
    required_roles = ("admin", "finance")

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.case = get_object_or_404(
            RepossessionCase.objects.select_related(
                "loan_application",
                "loan_application__motor",
            ).prefetch_related("events"),
            pk=kwargs["pk"],
        )
        if not self.case.is_open and self.case.status != RepossessionCase.Status.REMINDER:
            raise Http404("This repossession case is already closed.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: RepossessionCloseForm) -> HttpResponse:
        self.case.close_case(form.cleaned_data["notes"], user=self.request.user)
        messages.success(self.request, "Repossession case closed.")
        return redirect(self.get_success_url())

    def form_invalid(self, form: RepossessionCloseForm) -> HttpResponse:
        context = {
            "case": self.case,
            "reminder_form": RepossessionReminderForm(),
            "close_form": form,
        }
        return render(
            self.request,
            "pages/repossession/case_detail.html",
            context,
            status=400,
        )

    def get_success_url(self) -> str:
        return reverse("repossession:case-detail", args=[self.case.pk])
