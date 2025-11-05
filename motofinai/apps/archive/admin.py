from django.contrib import admin

from .models import Archive


@admin.register(Archive)
class ArchiveAdmin(admin.ModelAdmin):
    list_display = ["module", "record_id", "status", "archived_by", "created_at"]
    list_filter = ["status", "module", "created_at"]
    search_fields = ["module", "record_id", "reason"]
    readonly_fields = ["created_at", "restored_at"]
    date_hierarchy = "created_at"
