from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model with role support for RBAC."""

    class Roles(models.TextChoices):
        ADMIN = "admin", "Admin"
        FINANCE = "finance", "Finance"

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.ADMIN,
        help_text="Primary access role determining permissions across modules.",
    )

    def save(self, *args, **kwargs):
        """Ensure superusers are always treated as admins."""

        if self.is_superuser and self.role != self.Roles.ADMIN:
            self.role = self.Roles.ADMIN
        return super().save(*args, **kwargs)

    @property
    def is_admin(self) -> bool:
        return self.role == self.Roles.ADMIN or self.is_superuser

    @property
    def is_finance(self) -> bool:
        return self.role == self.Roles.FINANCE
