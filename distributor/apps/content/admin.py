from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_summernote.admin import SummernoteModelAdmin

from apps.core.admin import image_preview_method

from .models import Banner, News, Promo


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ["bg_preview", "title", "is_active", "order"]
    list_editable = ["is_active", "order"]
    list_display_links = ["title"]

    bg_preview = image_preview_method(
        "background", description=_("Background"), height=50, width=90
    )


@admin.register(News)
class NewsAdmin(SummernoteModelAdmin):
    summernote_fields = ("content",)
    list_display = ["image_preview", "title", "published_at", "is_active"]
    list_editable = ["is_active"]
    list_display_links = ["title"]
    search_fields = ["title"]
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"

    image_preview = image_preview_method("image", description=_("Photo"), height=50)


@admin.register(Promo)
class PromoAdmin(SummernoteModelAdmin):
    summernote_fields = ("description",)
    list_display = [
        "image_preview",
        "title",
        "brand",
        "status_badge",
        "date_start",
        "date_end",
    ]
    list_filter = ["is_active", "brand"]
    list_display_links = ["title"]
    search_fields = ["title"]
    prepopulated_fields = {"slug": ("title",)}

    image_preview = image_preview_method("image", description=_("Photo"), height=50)

    @admin.display(description=_("Status"))
    def status_badge(self, obj: Promo) -> str:
        if obj.is_current:
            return format_html(
                '<span style="color:green;font-weight:600">● {}</span>',
                _("Active"),
            )
        return format_html(
            '<span style="color:gray">● {}</span>', _("Ended")
        )
