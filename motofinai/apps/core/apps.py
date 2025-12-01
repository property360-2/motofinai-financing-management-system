"""
Core application configuration for shared functionality and utilities.
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration for the core app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "motofinai.apps.core"
    verbose_name = "Core"

    def ready(self):
        """Initialize the app."""
        # Import signal handlers or other initialization code here if needed
        pass
