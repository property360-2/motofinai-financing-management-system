from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Count, Q, Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import FormView, TemplateView

from motofinai.apps.loans.models import LoanApplication, PaymentSchedule

from .forms import PaymentRecordForm
from .models import Payment


class PaymentScheduleListView(LoginRequiredMixin, TemplateView):
    template_name = "pages/payments/schedule_list.html"
    required_roles = ("admin", "finance")

    def get_queryset(self):
        reference_date = timezone.now().date()
        PaymentSchedule.objects.mark_overdue(reference_date)
        schedules = (
            PaymentSchedule.objects.select_related("loan_application", "loan_application__motor")
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
        }

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        schedules = self.get_queryset()
        context.update(
            {
                "schedules": schedules,
                "summary": self.get_summary(schedules),
                "loans": LoanApplication.objects.order_by("-submitted_at")[:20],
            }
        )
        return context


class RecordPaymentView(LoginRequiredMixin, FormView):
    template_name = "pages/payments/record_payment.html"
    form_class = PaymentRecordForm
    required_roles = ("admin", "finance")

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
