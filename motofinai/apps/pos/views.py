"""Views for POS payment terminal and session management."""

from decimal import Decimal
from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import DetailView, FormView, ListView, TemplateView

from motofinai.apps.loans.models import LoanApplication, PaymentSchedule
from motofinai.apps.payments.models import Payment, PaymentMethod
from motofinai.apps.pos.forms import (
    PaymentRecordForm,
    POSSessionCloseForm,
    POSSessionOpenForm,
    QuickPayForm,
)
from motofinai.apps.pos.models import POSSession, POSTransaction, ReceiptLog, get_next_receipt_number


class POSTerminalView(LoginRequiredMixin, TemplateView):
    """Main POS terminal for payment entry and customer search."""

    template_name = "pages/pos/terminal.html"
    required_roles = ("admin", "finance")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        # Get or create active session
        active_session = POSSession.objects.active().first()
        context["active_session"] = active_session
        context["form"] = QuickPayForm()

        if active_session:
            context["session_transactions"] = active_session.transactions.select_related(
                "payment__loan_application"
            )
            context["session_total"] = active_session.total_collected
            context["transaction_count"] = active_session.transaction_count

        context["breadcrumbs"] = [
            {"label": "Payments", "url": reverse("payments:list")},
            {"label": "POS Terminal"},
        ]
        return context


class QuickPaySearchView(LoginRequiredMixin, View):
    """AJAX endpoint for quick customer search."""

    required_roles = ("admin", "finance")

    def get(self, request: HttpRequest) -> JsonResponse:
        search_query = request.GET.get("q", "").strip()
        if len(search_query) < 2:
            return JsonResponse({"error": "Query too short"}, status=400)

        # Search for loans by applicant name, phone, or loan ID
        loans = LoanApplication.objects.filter(
            status=LoanApplication.Status.ACTIVE
        ).select_related("motor")

        # Filter by search query
        loans = loans.filter(
            Q(applicant_first_name__icontains=search_query)
            | Q(applicant_last_name__icontains=search_query)
            | Q(applicant_phone__icontains=search_query)
            | Q(applicant_email__icontains=search_query)
            | (Q(id=int(search_query)) if search_query.isdigit() else Q())
        )[:10]

        results = []
        for loan in loans:
            # Get next due payment
            next_schedule = loan.payment_schedules.exclude(
                status=PaymentSchedule.Status.PAID
            ).first()

            results.append({
                "id": loan.id,
                "name": loan.applicant_full_name,
                "phone": loan.applicant_phone,
                "motorcycle": f"{loan.motor.brand} {loan.motor.model_name}",
                "next_due": float(next_schedule.total_amount) if next_schedule else 0,
                "url": reverse("pos:quick_pay", kwargs={"pk": loan.id}),
            })

        return JsonResponse({"results": results})


class QuickPayView(LoginRequiredMixin, DetailView):
    """Quick pay interface for rapid payment recording."""

    model = LoanApplication
    template_name = "pages/pos/quick_pay.html"
    context_object_name = "loan"
    required_roles = ("admin", "finance")

    def get_queryset(self):
        return LoanApplication.objects.filter(
            status=LoanApplication.Status.ACTIVE
        ).select_related("motor", "financing_term").prefetch_related("payment_schedules")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        loan = self.object

        # Get outstanding payments
        outstanding = loan.payment_schedules.exclude(
            status=PaymentSchedule.Status.PAID
        ).order_by("due_date")

        context["outstanding_schedules"] = outstanding
        context["next_due"] = outstanding.first() if outstanding.exists() else None
        context["form"] = PaymentRecordForm()

        # Active session
        context["active_session"] = POSSession.objects.active().first()

        context["breadcrumbs"] = [
            {"label": "Payments", "url": reverse("payments:list")},
            {"label": "POS Terminal", "url": reverse("pos:terminal")},
            {"label": f"Quick Pay - {loan.applicant_full_name}"},
        ]
        return context

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        loan = self.get_object()
        form = PaymentRecordForm(request.POST)

        if form.is_valid():
            # Get next due schedule
            next_schedule = loan.payment_schedules.exclude(
                status=PaymentSchedule.Status.PAID
            ).first()

            if not next_schedule:
                messages.error(request, "No outstanding payments for this loan.")
                return redirect("pos:quick_pay", pk=loan.id)

            # Validate amount matches
            if Decimal(str(form.cleaned_data["amount"])) != next_schedule.total_amount:
                messages.error(
                    request,
                    f"Payment amount must match the due amount: ₱{next_schedule.total_amount}",
                )
                return redirect("pos:quick_pay", pk=loan.id)

            # Get active session
            session = POSSession.objects.active().first()
            if not session:
                messages.error(request, "No active POS session. Please open a session first.")
                return redirect("pos:terminal")

            try:
                with transaction.atomic():
                    # Create payment
                    payment = form.save(commit=False)
                    payment.loan_application = loan
                    payment.schedule = next_schedule
                    payment.recorded_by = request.user
                    payment.save()

                    # Create POS transaction
                    POSTransaction.objects.create(
                        session=session,
                        payment=payment,
                        transaction_type=POSTransaction.TransactionType.PAYMENT,
                    )

                    # Generate receipt
                    receipt = ReceiptLog.objects.create(
                        payment=payment,
                        receipt_number=get_next_receipt_number(),
                    )

                    messages.success(request, f"Payment recorded successfully! Receipt: {receipt.receipt_number}")
                    return redirect("pos:receipt_view", receipt_id=receipt.id)

            except ValidationError as e:
                messages.error(request, f"Payment error: {e.message}")
                return redirect("pos:quick_pay", pk=loan.id)
        else:
            context = self.get_context_data(object=self.object)
            context["form"] = form
            return self.render_to_response(context)


class ReceiptView(LoginRequiredMixin, DetailView):
    """Display and print receipt for payment."""

    model = ReceiptLog
    template_name = "pages/pos/receipt.html"
    context_object_name = "receipt"
    required_roles = ("admin", "finance")
    pk_url_kwarg = "receipt_id"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        receipt = self.object
        context["payment"] = receipt.payment
        context["loan"] = receipt.payment.loan_application
        context["breadcrumbs"] = [
            {"label": "Payments", "url": reverse("payments:list")},
            {"label": "POS Terminal", "url": reverse("pos:terminal")},
            {"label": f"Receipt {receipt.receipt_number}"},
        ]
        return context

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Mark receipt as printed."""
        receipt = self.get_object()
        receipt.mark_printed(printed_by=request.user)
        messages.success(request, "Receipt marked as printed.")
        return redirect("pos:receipt_view", receipt_id=receipt.id)


class POSSessionListView(LoginRequiredMixin, ListView):
    """List POS sessions with summary data."""

    model = POSSession
    template_name = "pages/pos/session_list.html"
    context_object_name = "sessions"
    paginate_by = 20
    required_roles = ("admin", "finance")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["active_session"] = POSSession.objects.active().first()
        context["breadcrumbs"] = [
            {"label": "Payments", "url": reverse("payments:list")},
            {"label": "POS Sessions"},
        ]
        return context


class POSSessionOpenView(LoginRequiredMixin, FormView):
    """Open a new POS session."""

    form_class = POSSessionOpenForm
    template_name = "pages/pos/session_open.html"
    success_url = reverse_lazy("pos:terminal")
    required_roles = ("admin", "finance")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        # Check if session already open
        context["active_session"] = POSSession.objects.active().first()
        context["breadcrumbs"] = [
            {"label": "Payments", "url": reverse("payments:list")},
            {"label": "POS Terminal", "url": reverse("pos:terminal")},
            {"label": "Open Session"},
        ]
        return context

    def form_valid(self, form) -> HttpResponse:
        # Check if session already open
        if POSSession.objects.active().exists():
            messages.error(self.request, "A session is already open. Close it first.")
            return redirect("pos:terminal")

        session = POSSession.objects.create(
            opened_by=self.request.user,
            opening_cash=form.cleaned_data["opening_cash"],
            notes=form.cleaned_data.get("notes", ""),
        )
        messages.success(self.request, f"POS session opened with ₱{session.opening_cash} float.")
        return redirect(self.success_url)


class POSSessionCloseView(LoginRequiredMixin, FormView):
    """Close the active POS session."""

    form_class = POSSessionCloseForm
    template_name = "pages/pos/session_close.html"
    success_url = reverse_lazy("pos:terminal")
    required_roles = ("admin", "finance")

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.session = POSSession.objects.active().first()
        if not self.session:
            messages.error(request, "No active session to close.")
            return redirect("pos:terminal")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["session"] = self.session
        context["session_total"] = self.session.total_collected
        context["expected_cash"] = self.session.opening_cash + self.session.total_collected
        context["breadcrumbs"] = [
            {"label": "Payments", "url": reverse("payments:list")},
            {"label": "POS Terminal", "url": reverse("pos:terminal")},
            {"label": "Close Session"},
        ]
        return context

    def form_valid(self, form) -> HttpResponse:
        try:
            self.session.close_session(
                closing_cash=form.cleaned_data["closing_cash"],
                closed_by=self.request.user,
            )
            # Update notes if provided
            if form.cleaned_data.get("notes"):
                self.session.notes = form.cleaned_data["notes"]
                self.session.save()

            variance = self.session.cash_variance
            if variance == 0:
                messages.success(self.request, "Session closed successfully with no variance.")
            elif variance > 0:
                messages.warning(
                    self.request,
                    f"Session closed with overage of ₱{variance}.",
                )
            else:
                messages.warning(
                    self.request,
                    f"Session closed with shortage of ₱{abs(variance)}.",
                )
            return redirect(self.success_url)
        except ValidationError as e:
            messages.error(self.request, str(e))
            return redirect("pos:session_close")


class POSSessionDetailView(LoginRequiredMixin, DetailView):
    """View details of a POS session."""

    model = POSSession
    template_name = "pages/pos/session_detail.html"
    context_object_name = "session"
    required_roles = ("admin", "finance")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        session = self.object
        context["transactions"] = session.transactions.select_related(
            "payment__loan_application__motor"
        )
        context["breadcrumbs"] = [
            {"label": "Payments", "url": reverse("payments:list")},
            {"label": "POS Sessions", "url": reverse("pos:session_list")},
            {"label": f"Session {session.id}"},
        ]
        return context
