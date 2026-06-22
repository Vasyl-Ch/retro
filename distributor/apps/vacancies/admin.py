from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django_summernote.admin import SummernoteModelAdmin

from apps.core.admin import image_preview_method

from .models import Vacancy, VacancyImage


class VacancyImageInline(admin.TabularInline):
    model = VacancyImage
    extra = 1
    fields = ["image", "caption", "order"]
    ordering = ["order"]


@admin.register(Vacancy)
class VacancyAdmin(SummernoteModelAdmin):
    summernote_fields = ("description", "requirements", "conditions")
    inlines = [VacancyImageInline]

    list_display = ["cover_preview", "title", "city", "is_urgent", "is_active", "order", "created_at"]
    list_editable = ["is_active", "is_urgent", "order"]
    list_display_links = ["cover_preview", "title"]
    list_filter = ["city", "is_active", "is_urgent"]
    search_fields = ["title", "city", "short_tagline"]
    prepopulated_fields = {"slug": ("title",)}

    fieldsets = (
        (_("General"), {
            "fields": ("title", "slug", "city", "short_tagline", "cover_image",
                       "is_urgent", "is_active", "order"),
        }),
        (_("Description"), {"fields": ("description",)}),
        (_("Requirements"), {"fields": ("requirements",)}),
        (_("Conditions"), {"fields": ("conditions",)}),
    )

    cover_preview = image_preview_method("cover_image", description=_("Photo"), height=46, width=80)
