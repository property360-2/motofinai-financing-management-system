from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import FinancingTermForm
from .models import FinancingTerm


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
