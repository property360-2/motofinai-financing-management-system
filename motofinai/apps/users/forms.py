from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

User = get_user_model()


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(
            attrs={
                "autofocus": True,
                "class": "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200",
                "placeholder": "Enter your username",
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200",
                "placeholder": "Enter your password",
            }
        ),
    )

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if getattr(user, "is_active", False) is False:
            raise forms.ValidationError(
                "Your account is inactive. Please contact an administrator.",
                code="inactive",
            )


INPUT_CLASS = "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"


class UserCreateForm(UserCreationForm):
    """Form for creating new users."""

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "role", "is_active", "is_staff"]
        widgets = {
            "username": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Username"}),
            "email": forms.EmailInput(attrs={"class": INPUT_CLASS, "placeholder": "user@example.com"}),
            "first_name": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "First name"}),
            "last_name": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Last name"}),
            "role": forms.Select(attrs={"class": INPUT_CLASS}),
        }

    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"class": INPUT_CLASS, "placeholder": "Password"}
        ),
        help_text="Password must be at least 8 characters.",
    )
    password2 = forms.CharField(
        label="Password confirmation",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"class": INPUT_CLASS, "placeholder": "Confirm password"}
        ),
        help_text="Enter the same password as before, for verification.",
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        label="Active",
        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
    )
    is_staff = forms.BooleanField(
        required=False,
        initial=False,
        label="Staff status",
        help_text="Designates whether the user can log into the admin site.",
    )


class UserUpdateForm(forms.ModelForm):
    """Form for updating existing users."""

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "role", "is_active", "is_staff"]
        widgets = {
            "username": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "email": forms.EmailInput(attrs={"class": INPUT_CLASS}),
            "first_name": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "last_name": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "role": forms.Select(attrs={"class": INPUT_CLASS}),
        }

    is_active = forms.BooleanField(
        required=False,
        label="Active",
        help_text="Designates whether this user should be treated as active.",
    )
    is_staff = forms.BooleanField(
        required=False,
        label="Staff status",
        help_text="Designates whether the user can log into the admin site.",
    )


class UserFilterForm(forms.Form):
    """Form for filtering user list."""

    q = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "Search by username, email, or name...",
            }
        ),
    )
    role = forms.ChoiceField(
        required=False,
        label="Role",
        choices=[("", "All roles")] + list(User.Roles.choices),
        widget=forms.Select(attrs={"class": INPUT_CLASS}),
    )
    is_active = forms.ChoiceField(
        required=False,
        label="Status",
        choices=[("", "All"), ("true", "Active"), ("false", "Inactive")],
        widget=forms.Select(attrs={"class": INPUT_CLASS}),
    )
