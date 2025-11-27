from decimal import Decimal
from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q, Sum
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

        # Status filter
        status = self.request.GET.get("status")
        if status in dict(RepossessionCase.Status.choices):
            queryset = queryset.filter(status=status)

        # Search functionality
        search = self.request.GET.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(loan_application__applicant_first_name__icontains=search)
                | Q(loan_application__applicant_last_name__icontains=search)
                | Q(loan_application__applicant_email__icontains=search)
                | Q(loan_application__applicant_phone__icontains=search)
                | Q(loan_application__motor__brand__icontains=search)
                | Q(loan_application__motor__model__icontains=search)
            )

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

        # Add pagination
        paginator = Paginator(queryset, 20)  # 20 items per page
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context.update(
            {
                "cases": page_obj,
                "page_obj": page_obj,
                "is_paginated": page_obj.has_other_pages(),
                "paginator": paginator,
                "summary": self.get_summary(),
                "status_choices": RepossessionCase.Status.choices,
                "search_query": self.request.GET.get("search", ""),
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
        # Breadcrumbs
        context["breadcrumbs"] = [
            {"label": "Repossession", "url": reverse("repossession:case-list")},
            {"label": "Cases", "url": reverse("repossession:case-list")},
            {"label": f"Case #{self.object.pk}"},
        ]
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
