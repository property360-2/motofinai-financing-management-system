from django.contrib import admin

from .models import AuditLogEntry


@admin.register(AuditLogEntry)
class AuditLogEntryAdmin(admin.ModelAdmin):
    list_display = ("action", "actor", "ip_address", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("action", "actor__username", "metadata")
    autocomplete_fields = ("actor",)
    ordering = ("-created_at",)
