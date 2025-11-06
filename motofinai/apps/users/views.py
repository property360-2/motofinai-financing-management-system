from functools import cached_property

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.db import models
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from motofinai.apps.audit.models import AuditLogEntry

from .forms import LoginForm, UserCreateForm, UserFilterForm, UserUpdateForm

User = get_user_model()


class UserLoginView(LoginView):
    template_name = "pages/login.html"
    form_class = LoginForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("page_title", "Sign in")
        return context

    def get_success_url(self):
        return self.get_redirect_url() or reverse_lazy("home")


class UserLogoutView(LoginRequiredMixin, LogoutView):
    next_page = reverse_lazy("home")
    http_method_names = ["get", "post", "options", "head"]

    def get(self, request, *args, **kwargs):
        """Ensure GET requests trigger logout for header links."""

        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        actor = request.user if request.user.is_authenticated else None
        session_key = request.session.session_key
        ip_address = self._extract_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        response = super().post(request, *args, **kwargs)
        AuditLogEntry.record(
            actor=actor,
            action="auth.logout",
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"path": request.path, "session_key": session_key},
        )
        return response

    @staticmethod
    def _extract_ip(request):
        if not request:
            return None
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")


class UserManagementMixin:
    """Shared helpers for user management views."""

    def user_can_manage_users(self) -> bool:
        user = self.request.user
        return getattr(user, "role", "") == "admin" or user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_manage_users"] = self.user_can_manage_users()
        return context


class UserListView(UserManagementMixin, LoginRequiredMixin, ListView):
    """List all users with filtering capabilities."""

    model = User
    template_name = "pages/users/user_list.html"
    context_object_name = "users"
    paginate_by = 20
    required_roles = ("admin",)

    @cached_property
    def filter_form(self) -> UserFilterForm:
        return UserFilterForm(self.request.GET or None)

    def get_queryset(self):
        queryset = super().get_queryset().order_by("-date_joined")
        form = self.filter_form
        if form.is_valid():
            role = form.cleaned_data.get("role")
            if role:
                queryset = queryset.filter(role=role)
            is_active = form.cleaned_data.get("is_active")
            if is_active == "true":
                queryset = queryset.filter(is_active=True)
            elif is_active == "false":
                queryset = queryset.filter(is_active=False)
            query = form.cleaned_data.get("q")
            if query:
                queryset = queryset.filter(
                    models.Q(username__icontains=query)
                    | models.Q(email__icontains=query)
                    | models.Q(first_name__icontains=query)
                    | models.Q(last_name__icontains=query)
                )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        return context


class UserDetailView(UserManagementMixin, LoginRequiredMixin, DetailView):
    """View details of a specific user."""

    model = User
    template_name = "pages/users/user_detail.html"
    context_object_name = "user_obj"
    required_roles = ("admin",)


class UserCreateView(
    UserManagementMixin, LoginRequiredMixin, SuccessMessageMixin, CreateView
):
    """Create a new user."""

    model = User
    form_class = UserCreateForm
    template_name = "pages/users/user_form.html"
    success_message = "User created successfully."
    success_url = reverse_lazy("users:user-list")
    required_roles = ("admin",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Create User"
        context["submit_text"] = "Create User"
        return context


class UserUpdateView(
    UserManagementMixin, LoginRequiredMixin, SuccessMessageMixin, UpdateView
):
    """Update an existing user."""

    model = User
    form_class = UserUpdateForm
    template_name = "pages/users/user_form.html"
    success_message = "User updated successfully."
    success_url = reverse_lazy("users:user-list")
    required_roles = ("admin",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Edit User"
        context["submit_text"] = "Update User"
        return context
