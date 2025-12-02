from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict
from datetime import datetime, timedelta
from calendar import monthrange
import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.generic import FormView, TemplateView

from motofinai.apps.loans.models import LoanApplication, PaymentSchedule

from .forms import PaymentRecordForm
from .models import Payment


class PaymentScheduleListView(LoginRequiredMixin, TemplateView):
    template_name = "pages/payments/schedule_list.html"
    required_roles = ("admin", "finance", "credit_investigator")

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
        reference_date = timezone.now().date()
        PaymentSchedule.objects.mark_overdue(reference_date)

        start_date, end_date = self.get_date_range()

        schedules = (
            PaymentSchedule.objects.select_related(
                "loan_application",
                "loan_application__motor",
            )
            .filter(due_date__gte=start_date, due_date__lte=end_date)
            .order_by("due_date", "sequence")
        )
        loan_id = self.request.GET.get("loan")
        if loan_id:
            schedules = schedules.filter(loan_application_id=loan_id)
        status = self.request.GET.get("status")
        if status in dict(PaymentSchedule.Status.choices):
            schedules = schedules.filter(status=status)
        return schedules

    def get_summary(self, schedules):
        aggregates = schedules.aggregate(
            due_total=Sum("total_amount", filter=Q(status=PaymentSchedule.Status.DUE)),
            overdue_total=Sum("total_amount", filter=Q(status=PaymentSchedule.Status.OVERDUE)),
            paid_total=Sum("total_amount", filter=Q(status=PaymentSchedule.Status.PAID)),
            due_count=Count("id", filter=Q(status=PaymentSchedule.Status.DUE)),
            overdue_count=Count("id", filter=Q(status=PaymentSchedule.Status.OVERDUE)),
            paid_count=Count("id", filter=Q(status=PaymentSchedule.Status.PAID)),
        )
        due_total = aggregates["due_total"] or Decimal("0.00")
        overdue_total = aggregates["overdue_total"] or Decimal("0.00")
        paid_total = aggregates["paid_total"] or Decimal("0.00")
        denominator = due_total + overdue_total + paid_total
        collection_rate = Decimal("0.00")
        if denominator > 0:
            collection_rate = (paid_total / denominator * Decimal("100")).quantize(Decimal("0.01"))
        return {
            "due_total": due_total,
            "overdue_total": overdue_total,
            "paid_total": paid_total,
            "due_count": aggregates["due_count"] or 0,
            "overdue_count": aggregates["overdue_count"] or 0,
            "paid_count": aggregates["paid_count"] or 0,
            "collection_rate": collection_rate,
            "pending_amount": due_total + overdue_total,
            "total_collected": paid_total,
        }

    def get_chart_data(self):
        """Generate data for payment tracking charts"""
        now = timezone.now()

        # Get last 6 months of data for charts
        months_data = []
        collection_rates = []

        for i in range(5, -1, -1):
            month_date = now - timedelta(days=30 * i)
            month_start = month_date.replace(day=1).date()
            _, last_day = monthrange(month_date.year, month_date.month)
            month_end = month_date.replace(day=last_day).date()

            month_schedules = PaymentSchedule.objects.filter(
                due_date__gte=month_start,
                due_date__lte=month_end
            )

            month_summary = month_schedules.aggregate(
                collected=Sum("total_amount", filter=Q(status=PaymentSchedule.Status.PAID)),
                pending=Sum("total_amount", filter=~Q(status=PaymentSchedule.Status.PAID)),
            )

            collected = float(month_summary["collected"] or 0)
            pending = float(month_summary["pending"] or 0)
            total = collected + pending
            rate = (collected / total * 100) if total > 0 else 0

            months_data.append({
                'month': month_date.strftime('%b'),
                'collected': collected,
                'pending': pending,
            })
            collection_rates.append({
                'month': month_date.strftime('%b'),
                'rate': round(rate, 2),
            })

        return {
            'months_data': months_data,
            'collection_rates': collection_rates,
        }

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        schedules = self.get_queryset()
        start_date, end_date = self.get_date_range()

        # Add pagination
        paginator = Paginator(schedules, 25)  # 25 items per page
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Note: Summary uses all schedules, not just paginated ones
        context.update(
            {
                "schedules": page_obj,
                "page_obj": page_obj,
                "is_paginated": page_obj.has_other_pages(),
                "paginator": paginator,
                "summary": self.get_summary(schedules),
                "loans": LoanApplication.objects.order_by("-submitted_at")[:20],
                "chart_data": self.get_chart_data(),
                "start_date": start_date,
                "end_date": end_date,
                "page_title": "Payment Tracking",
            }
        )
        return context


class RecordPaymentView(LoginRequiredMixin, FormView):
    template_name = "pages/payments/record_payment.html"
    form_class = PaymentRecordForm
    required_roles = ("admin", "finance", "credit_investigator")

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.schedule = get_object_or_404(
            PaymentSchedule.objects.select_related("loan_application", "loan_application__motor"),
            pk=kwargs["pk"],
        )
        self.schedule.refresh_status()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["schedule"] = self.schedule
        return kwargs

    def form_valid(self, form: PaymentRecordForm) -> HttpResponse:
        try:
            Payment.objects.create(
                schedule=self.schedule,
                loan_application=self.schedule.loan_application,
                amount=form.cleaned_data["amount"],
                payment_date=form.cleaned_data["payment_date"],
                reference=form.cleaned_data.get("reference", ""),
                notes=form.cleaned_data.get("notes", ""),
                recorded_by=self.request.user,
            )
        except ValidationError as exc:
            if hasattr(exc, "message_dict"):
                for field, error_list in exc.message_dict.items():
                    for message in error_list:
                        if field in form.fields:
                            form.add_error(field, message)
                        else:
                            form.add_error(None, message)
            else:
                form.add_error(None, "; ".join(exc.messages))
            return self.form_invalid(form)
        messages.success(self.request, "Payment recorded successfully.")
        return redirect(self.get_success_url())

    def form_invalid(self, form: PaymentRecordForm) -> HttpResponse:
        context = self.get_context_data(form=form)
        return self.render_to_response(context, status=400)

    def get_success_url(self) -> str:
        return reverse("payments:schedule-list")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "schedule": self.schedule,
                "loan": self.schedule.loan_application,
            }
        )
        return context
