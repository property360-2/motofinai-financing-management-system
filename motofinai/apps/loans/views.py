from collections import OrderedDict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Iterable

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.functional import cached_property
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import (
    FinancingTermForm,
    LoanApprovalForm,
    LoanDocumentUploadForm,
    LoanEmploymentForm,
    LoanMotorSelectionForm,
    LoanPersonalInfoForm,
    LoanSupportingDocsForm,
)
from motofinai.apps.inventory.models import Motor

from .models import FinancingTerm, LoanApplication, LoanDocument


class FinancingTermContextMixin:
    """Helpers shared across financing term views."""

    def user_can_manage_terms(self) -> bool:
        user = self.request.user
        return getattr(user, "role", "") == "admin" or user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_manage_terms"] = self.user_can_manage_terms()
        return context


class FinancingTermListView(FinancingTermContextMixin, LoginRequiredMixin, ListView):
    model = FinancingTerm
    template_name = "pages/loans/financingterm_list.html"
    context_object_name = "terms"
    required_roles = ("admin", "finance")
    paginate_by = 20


class FinancingTermCreateView(
    FinancingTermContextMixin, LoginRequiredMixin, SuccessMessageMixin, CreateView
):
    model = FinancingTerm
    form_class = FinancingTermForm
    template_name = "pages/loans/financingterm_form.html"
    success_url = reverse_lazy("terms:list")
    success_message = "Financing term created."
    required_roles = ("admin",)


class FinancingTermUpdateView(
    FinancingTermContextMixin, LoginRequiredMixin, SuccessMessageMixin, UpdateView
):
    model = FinancingTerm
    form_class = FinancingTermForm
    template_name = "pages/loans/financingterm_form.html"
    success_url = reverse_lazy("terms:list")
    success_message = "Financing term updated."
    required_roles = ("admin",)


class FinancingTermDeleteView(FinancingTermContextMixin, LoginRequiredMixin, DeleteView):
    model = FinancingTerm
    template_name = "pages/loans/financingterm_confirm_delete.html"
    success_url = reverse_lazy("terms:list")
    required_roles = ("admin",)

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, "Financing term removed.")
        return response


class LoanApplicationWizard(LoginRequiredMixin, TemplateView):
    """Session-backed multi-step wizard for creating loan applications."""

    template_name = "pages/loans/application_wizard.html"
    required_roles = ("admin", "finance")
    session_key = "loan_application_wizard"
    steps: "OrderedDict[str, type]" = OrderedDict(
        (
            ("personal", LoanPersonalInfoForm),
            ("employment", LoanEmploymentForm),
            ("motor", LoanMotorSelectionForm),
            ("documents", LoanSupportingDocsForm),
        )
    )

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if self.current_step not in self.steps:
            raise Http404("Unknown wizard step")
        return super().dispatch(request, *args, **kwargs)

    @property
    def current_step(self) -> str:
        requested_step = self.request.GET.get("step") or self.request.POST.get("current_step")
        if requested_step in self.steps:
            return requested_step
        return next(iter(self.steps))

    @cached_property
    def ordered_steps(self) -> Iterable[str]:
        return tuple(self.steps.keys())

    def get_wizard_data(self) -> Dict[str, Dict[str, Any]]:
        return self.request.session.get(self.session_key, {})

    def serialize_step_data(self, step: str, data: Dict[str, Any]) -> Dict[str, Any]:
        serialized: Dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, (Motor, FinancingTerm)):
                serialized[key] = value.pk
            elif isinstance(value, Decimal):
                serialized[key] = str(value)
            elif isinstance(value, date):
                serialized[key] = value.isoformat()
            else:
                serialized[key] = value
        return serialized

    def deserialize_initial(self, step: str, data: Dict[str, Any]) -> Dict[str, Any]:
        deserialized: Dict[str, Any] = {}
        for key, value in data.items():
            deserialized[key] = value
        return deserialized

    def store_step_data(self, step: str, data: Dict[str, Any]) -> None:
        stored = self.get_wizard_data()
        stored[step] = self.serialize_step_data(step, data)
        self.request.session[self.session_key] = stored
        self.request.session.modified = True

    def clear_wizard(self) -> None:
        if self.session_key in self.request.session:
            del self.request.session[self.session_key]
            self.request.session.modified = True

    def get_initial_for_step(self, step: str) -> Dict[str, Any]:
        stored = self.get_wizard_data().get(step, {})
        return self.deserialize_initial(step, stored)

    def get_form(self) -> forms.Form:
        form_class = self.steps[self.current_step]
        return form_class(initial=self.get_initial_for_step(self.current_step))

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        step = self.current_step
        form_class = self.steps[step]
        form = form_class(request.POST)
        if form.is_valid():
            self.store_step_data(step, form.cleaned_data)
            next_step = self.next_step(step)
            if next_step is None:
                try:
                    application = self.create_application()
                except ValidationError as exc:
                    form.add_error(None, "; ".join(exc.messages))
                    context = self.get_context_data(form=form)
                    return self.render_to_response(context, status=400)
                else:
                    self.clear_wizard()
                    messages.success(request, "Loan application submitted.")
                    return redirect("loans:detail", pk=application.pk)
            return redirect(f"{reverse('loans:new')}?step={next_step}")
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        form = self.get_form()
        return self.render_to_response(self.get_context_data(form=form))

    def next_step(self, current: str) -> str | None:
        steps = list(self.ordered_steps)
        try:
            index = steps.index(current)
        except ValueError:
            return None
        if index + 1 >= len(steps):
            return None
        return steps[index + 1]

    def previous_step(self, current: str) -> str | None:
        steps = list(self.ordered_steps)
        try:
            index = steps.index(current)
        except ValueError:
            return None
        if index == 0:
            return None
        return steps[index - 1]

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "form": kwargs.get("form") or self.get_form(),
                "current_step": self.current_step,
                "steps": list(self.ordered_steps),
                "previous_step": self.previous_step(self.current_step),
            }
        )
        return context

    def create_application(self) -> LoanApplication:
        data = self.get_wizard_data()
        personal = data.get("personal", {})
        employment = data.get("employment", {})
        motor_selection = data.get("motor", {})
        documents = data.get("documents", {})

        motor_id = motor_selection.get("motor")
        term_id = motor_selection.get("financing_term")
        try:
            motor = Motor.objects.get(pk=motor_id)
            term = FinancingTerm.objects.get(pk=term_id)
        except Motor.DoesNotExist as exc:
            raise ValidationError("Selected motorcycle is no longer available.") from exc
        except FinancingTerm.DoesNotExist as exc:
            raise ValidationError("Selected financing term is no longer available.") from exc

        loan_amount = motor.purchase_price.quantize(Decimal("0.01"))
        down_payment = Decimal(motor_selection.get("down_payment") or "0")
        principal_amount = (loan_amount - down_payment).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if principal_amount <= Decimal("0"):
            raise ValidationError("Principal amount must be greater than zero.")

        application = LoanApplication(
            applicant_first_name=personal.get("first_name", "").strip(),
            applicant_last_name=personal.get("last_name", "").strip(),
            applicant_email=personal.get("email"),
            applicant_phone=personal.get("phone"),
            date_of_birth=self.parse_date(personal.get("date_of_birth")),
            employment_status=employment.get("employment_status"),
            employer_name=employment.get("employer_name", ""),
            monthly_income=Decimal(employment.get("monthly_income") or "0"),
            motor=motor,
            financing_term=term,
            loan_amount=loan_amount,
            down_payment=down_payment,
            principal_amount=principal_amount,
            interest_rate=term.interest_rate,
            monthly_payment=Decimal("0.00"),
            has_valid_id=bool(documents.get("has_valid_id")),
            has_proof_of_income=bool(documents.get("has_proof_of_income")),
            notes=documents.get("notes", ""),
            submitted_by=self.request.user,
        )
        application.monthly_payment = application.calculate_monthly_payment()
        application.full_clean()
        application.save()
        return application

    def parse_date(self, value: Any) -> date | None:
        if not value:
            return None
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(value)
        except (TypeError, ValueError):
            return None


class LoanApplicationListView(LoginRequiredMixin, ListView):
    model = LoanApplication
    template_name = "pages/loans/application_list.html"
    context_object_name = "applications"
    paginate_by = 20
    required_roles = ("admin", "finance")


class LoanApplicationDetailView(LoginRequiredMixin, DetailView):
    model = LoanApplication
    template_name = "pages/loans/application_detail.html"
    context_object_name = "application"
    required_roles = ("admin", "finance")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        self.object.refresh_payment_progress()
        context["schedules"] = self.object.payment_schedules.all()
        from motofinai.apps.risk.models import RiskAssessment

        try:
            assessment = self.object.risk_assessment
        except RiskAssessment.DoesNotExist:
            assessment = self.object.evaluate_risk()
        context["risk_assessment"] = assessment
        from motofinai.apps.repossession.models import RepossessionCase

        try:
            repossession_case = self.object.repossession_case
        except RepossessionCase.DoesNotExist:
            repossession_case = None
        context["repossession_case"] = repossession_case
        return context


class LoanApplicationDocumentsView(LoginRequiredMixin, TemplateView):
    template_name = "pages/loans/application_documents.html"
    required_roles = ("admin", "finance")

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.application = get_object_or_404(LoanApplication, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form(self) -> LoanDocumentUploadForm:
        return LoanDocumentUploadForm()

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "application": self.application,
                "documents": self.application.documents.all(),
                "form": kwargs.get("form") or self.get_form(),
            }
        )
        return context

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return self.render_to_response(self.get_context_data())

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        form = LoanDocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document: LoanDocument = form.save(commit=False)
            document.loan_application = self.application
            document.uploaded_by = request.user
            try:
                document.full_clean()
            except ValidationError as exc:
                errors = exc.message_dict.get("file", exc.messages)
                form.add_error("file", "; ".join(errors))
            else:
                document.save()
                messages.success(request, "Document uploaded successfully.")
                return redirect("loans:documents", pk=self.application.pk)
        context = self.get_context_data(form=form)
        return self.render_to_response(context, status=400)


class LoanApplicationApproveView(LoginRequiredMixin, DetailView):
    """Approve a loan application with optional custom terms."""

    model = LoanApplication
    template_name = "pages/loans/application_approve.html"
    context_object_name = "application"
    required_roles = ("admin", "finance")

    def get_queryset(self):
        return super().get_queryset().filter(status=LoanApplication.Status.PENDING)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.get_form()
        return context

    def get_form(self):
        if self.request.method == "POST":
            return LoanApprovalForm(self.request.POST)
        return LoanApprovalForm()

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        application = get_object_or_404(LoanApplication, pk=pk)

        if application.status != LoanApplication.Status.PENDING:
            messages.error(request, "Only pending applications can be approved.")
            return redirect("loans:detail", pk=pk)

        form = LoanApprovalForm(request.POST)
        if form.is_valid():
            custom_interest_rate = form.cleaned_data.get("custom_interest_rate")
            custom_term_years = form.cleaned_data.get("custom_term_years")

            try:
                application.approve(
                    approved_by=request.user,
                    custom_interest_rate=custom_interest_rate,
                    custom_term_years=custom_term_years,
                )
                messages.success(
                    request, "Loan application approved and payment schedule generated."
                )
                return redirect("loans:detail", pk=pk)
            except ValidationError as exc:
                messages.error(request, "; ".join(exc.messages))
                return self.get(request, pk=pk)
        else:
            # Form has errors, re-render with errors
            context = self.get_context_data(object=application)
            context["form"] = form
            return self.render_to_response(context)


class LoanApplicationActivateView(LoginRequiredMixin, View):
    required_roles = ("admin", "finance")

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        application = get_object_or_404(LoanApplication, pk=pk)
        try:
            application.activate()
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
        else:
            messages.success(request, "Loan marked as active and motorcycle reserved.")
        return redirect("loans:detail", pk=pk)


class LoanApplicationCompleteView(LoginRequiredMixin, View):
    required_roles = ("admin", "finance")

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        application = get_object_or_404(LoanApplication, pk=pk)
        try:
            application.complete()
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
        else:
            messages.success(request, "Loan marked as completed.")
        return redirect("loans:detail", pk=pk)


class LoanDocumentDeleteView(LoginRequiredMixin, View):
    required_roles = ("admin", "finance")

    def post(self, request: HttpRequest, pk: int, document_pk: int) -> HttpResponse:
        application = get_object_or_404(LoanApplication, pk=pk)
        document = get_object_or_404(
            LoanDocument,
            pk=document_pk,
            loan_application=application,
        )
        document.file.delete(save=False)
        document.delete()
        messages.success(request, "Document removed.")
        return redirect("loans:documents", pk=pk)
