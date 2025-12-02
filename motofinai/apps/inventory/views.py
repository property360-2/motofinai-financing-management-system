from functools import cached_property

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import MotorFilterForm, MotorForm, StockFilterForm, StockForm
from .models import Motor, Stock


class InventoryContextMixin:
    """Shared helpers for inventory views."""

    def user_can_manage_inventory(self) -> bool:
        user = self.request.user
        return getattr(user, "role", "") == "admin" or user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_manage_inventory"] = self.user_can_manage_inventory()
        return context


class MotorListView(InventoryContextMixin, LoginRequiredMixin, ListView):
    model = Motor
    template_name = "pages/inventory/motor_list.html"
    context_object_name = "motors"
    paginate_by = 20
    required_roles = ("admin", "finance")

    @cached_property
    def filter_form(self) -> MotorFilterForm:
        return MotorFilterForm(self.request.GET or None)

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .select_related()
        )
        form = self.filter_form
        if form.is_valid():
            query = form.cleaned_data.get("q")
            if query:
                queryset = queryset.filter(
                    models.Q(brand__icontains=query)
                    | models.Q(model_name__icontains=query)
                    | models.Q(type__icontains=query)
                )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        return context


class MotorDetailView(InventoryContextMixin, LoginRequiredMixin, DetailView):
    model = Motor
    template_name = "pages/inventory/motor_detail.html"
    context_object_name = "motor"
    required_roles = ("admin", "finance")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Inventory", "url": reverse("inventory:motor-list")},
            {"label": "Motorcycles", "url": reverse("inventory:motor-list")},
            {"label": self.object.display_name},
        ]
        return context


class MotorCreateView(
    InventoryContextMixin, LoginRequiredMixin, SuccessMessageMixin, CreateView
):
    model = Motor
    form_class = MotorForm
    template_name = "pages/inventory/motor_form.html"
    success_message = "Motor added to inventory."
    required_roles = ("admin",)

    def get_success_url(self):
        return reverse("inventory:motor-detail", args=[self.object.pk])


class MotorUpdateView(
    InventoryContextMixin, LoginRequiredMixin, SuccessMessageMixin, UpdateView
):
    model = Motor
    form_class = MotorForm
    template_name = "pages/inventory/motor_form.html"
    success_message = "Motor details updated."
    required_roles = ("admin",)

    def get_success_url(self):
        return reverse("inventory:motor-detail", args=[self.object.pk])


class MotorDeleteView(InventoryContextMixin, LoginRequiredMixin, DeleteView):
    model = Motor
    template_name = "pages/inventory/motor_confirm_delete.html"
    success_url = reverse_lazy("inventory:motor-list")
    required_roles = ("admin",)

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, "Motor removed from inventory.")
        return response


class StockListView(InventoryContextMixin, LoginRequiredMixin, ListView):
    model = Stock
    template_name = "pages/inventory/stock_list.html"
    context_object_name = "stocks"
    paginate_by = 20
    required_roles = ("admin", "finance")

    @cached_property
    def filter_form(self) -> StockFilterForm:
        return StockFilterForm(self.request.GET or None)

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .prefetch_related("motors")
        )
        form = self.filter_form
        if form.is_valid():
            query = form.cleaned_data.get("q")
            if query:
                queryset = queryset.filter(
                    models.Q(brand__icontains=query)
                    | models.Q(model_name__icontains=query)
                    | models.Q(color__icontains=query)
                )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        return context


class StockDetailView(InventoryContextMixin, LoginRequiredMixin, DetailView):
    model = Stock
    template_name = "pages/inventory/stock_detail.html"
    context_object_name = "stock"
    required_roles = ("admin", "finance")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["motors"] = self.object.motors.all()
        return context


class StockCreateView(
    InventoryContextMixin, LoginRequiredMixin, SuccessMessageMixin, CreateView
):
    model = Stock
    form_class = StockForm
    template_name = "pages/inventory/stock_form.html"
    success_message = "Stock batch created."
    required_roles = ("admin",)

    def get_success_url(self):
        return reverse("inventory:stock-detail", args=[self.object.pk])


class StockUpdateView(
    InventoryContextMixin, LoginRequiredMixin, SuccessMessageMixin, UpdateView
):
    model = Stock
    form_class = StockForm
    template_name = "pages/inventory/stock_form.html"
    success_message = "Stock batch updated."
    required_roles = ("admin",)

    def get_success_url(self):
        return reverse("inventory:stock-detail", args=[self.object.pk])


class StockDeleteView(InventoryContextMixin, LoginRequiredMixin, DeleteView):
    model = Stock
    template_name = "pages/inventory/stock_confirm_delete.html"
    success_url = reverse_lazy("inventory:stock-list")
    required_roles = ("admin",)

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, "Stock batch removed.")
        return response


class MotorApprovalListView(InventoryContextMixin, LoginRequiredMixin, ListView):
    """List motorcycles pending approval for finance officers."""

    model = Motor
    template_name = "pages/inventory/motor_approval_list.html"
    context_object_name = "motors"
    paginate_by = 20
    required_roles = ("admin", "finance")

    @cached_property
    def filter_form(self) -> MotorFilterForm:
        return MotorFilterForm(self.request.GET or None)

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .filter(approval_status=Motor.ApprovalStatus.PENDING)
            .select_related("approved_by")
            .order_by("-created_at")
        )
        form = self.filter_form
        if form.is_valid():
            query = form.cleaned_data.get("q")
            if query:
                queryset = queryset.filter(
                    models.Q(brand__icontains=query)
                    | models.Q(model_name__icontains=query)
                    | models.Q(type__icontains=query)
                    | models.Q(chassis_number__icontains=query)
                )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        # Count pending approvals
        context["pending_count"] = Motor.objects.filter(
            approval_status=Motor.ApprovalStatus.PENDING
        ).count()
        return context


class MotorApprovalDetailView(InventoryContextMixin, LoginRequiredMixin, DetailView):
    """View details of a motorcycle pending approval."""

    model = Motor
    template_name = "pages/inventory/motor_approval_detail.html"
    context_object_name = "motor"
    required_roles = ("admin", "finance")

    def get_queryset(self):
        # Can view pending or already approved/rejected motors
        return super().get_queryset().filter(
            approval_status__in=[
                Motor.ApprovalStatus.PENDING,
                Motor.ApprovalStatus.APPROVED,
                Motor.ApprovalStatus.REJECTED,
            ]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        motor = self.object
        # Show loan applications for this motor
        context["reserved_applications"] = motor.get_reserved_applications()
        context["sold_applications"] = motor.get_sold_applications()
        return context


class MotorApproveView(LoginRequiredMixin, View):
    """Approve a motorcycle for financing."""

    required_roles = ("admin", "finance")

    def post(self, request, pk):
        motor = get_object_or_404(Motor, pk=pk)

        if motor.approval_status != Motor.ApprovalStatus.PENDING:
            messages.error(request, "Only pending motors can be approved.")
            return redirect("inventory:motor-approval-detail", pk=motor.pk)

        notes = request.POST.get("approval_notes", "").strip()

        try:
            motor.approve(approved_by=request.user, notes=notes)
            messages.success(
                request, f"Motorcycle '{motor.display_name}' has been approved."
            )
        except ValidationError as e:
            messages.error(request, f"Error approving motorcycle: {e}")

        return redirect("inventory:motor-approval-detail", pk=motor.pk)


class MotorRejectView(LoginRequiredMixin, View):
    """Reject a motorcycle for financing."""

    required_roles = ("admin", "finance")

    def post(self, request, pk):
        motor = get_object_or_404(Motor, pk=pk)

        if motor.approval_status != Motor.ApprovalStatus.PENDING:
            messages.error(request, "Only pending motors can be rejected.")
            return redirect("inventory:motor-approval-detail", pk=motor.pk)

        notes = request.POST.get("rejection_notes", "").strip()
        if not notes:
            messages.error(request, "Please provide a reason for rejection.")
            return redirect("inventory:motor-approval-detail", pk=motor.pk)

        try:
            motor.reject(approved_by=request.user, notes=notes)
            messages.warning(
                request, f"Motorcycle '{motor.display_name}' has been rejected."
            )
        except ValidationError as e:
            messages.error(request, f"Error rejecting motorcycle: {e}")

        return redirect("inventory:motor-approval-list")
