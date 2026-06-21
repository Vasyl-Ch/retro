from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import ContactRequest


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ["name", "phone", "email", "subject", "is_read", "created_at"]
    list_filter = ["is_read", "subject"]
    list_display_links = ["name"]
    readonly_fields = ["name", "phone", "email", "subject", "message", "created_at"]
    actions = ["mark_as_read"]

    def has_add_permission(self, request) -> bool:
        return False

    @admin.action(description=_("Позначити як прочитані"))
    def mark_as_read(self, request, queryset) -> None:
        queryset.update(is_read=True)
