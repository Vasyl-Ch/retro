"""Reusable admin helpers shared across apps."""

from typing import Any

from django.contrib import admin, messages
from django.db.models.fields.files import ImageFieldFile
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import SafeString
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin
from solo.admin import SingletonModelAdmin

from .models import PageBackground, SiteSettings
from .presets import PRESETS, apply_preset


def image_thumbnail(
    image: ImageFieldFile | None,
    *,
    height: int = 50,
    width: int | None = None,
    object_fit: str = "cover",
    radius: int = 4,
    empty: str = "—",
) -> SafeString | str:
    """Render a safe <img> thumbnail for an admin list/detail preview.

    Returns ``empty`` when the image is missing or has no file attached.
    """
    if not image:
        return empty
    style = f"border-radius:{radius}px;object-fit:{object_fit}"
    if width is None:
        return format_html(
            '<img src="{}" height="{}" style="{}">',
            image.url,
            height,
            style,
        )
    return format_html(
        '<img src="{}" height="{}" width="{}" style="{}">',
        image.url,
        height,
        width,
        style,
    )


def image_preview_method(
    field_name: str,
    *,
    description: str,
    **thumbnail_kwargs: Any,
):
    """Build an admin display callable that renders a thumbnail for ``field_name``.

    Usage in an admin class::

        logo_preview = image_preview_method('logo', description='Лого', height=40)
    """

    def _preview(self: Any, obj: Any) -> SafeString | str:
        return image_thumbnail(getattr(obj, field_name), **thumbnail_kwargs)

    _preview.short_description = description  # type: ignore[attr-defined]
    return _preview


@admin.register(PageBackground)
class PageBackgroundAdmin(admin.ModelAdmin):
    list_display = ["image_preview", "page_label", "is_active", "overlay_opacity", "updated_at"]
    list_editable = ["is_active", "overlay_opacity"]
    list_display_links = ["image_preview", "page_label"]
    list_filter = ["is_active"]
    readonly_fields = ["updated_at"]
    fields = ["page_key", "image", "is_active", "overlay_opacity", "updated_at"]

    image_preview = image_preview_method("image", description=_("Фон"), height=50, width=90)

    @admin.display(description=_("Сторінка"), ordering="page_key")
    def page_label(self, obj: PageBackground) -> str:
        return obj.get_page_key_display()


PRESET_LABELS = {
    "distributor": _("Distributor (дистриб'ютор)"),
    "auto": _("Auto (автосалон)"),
    "food": _("Restaurant / Food (ресторан)"),
    "shop": _("Shop (магазин з кошиком)"),
    "generic": _("Generic (універсальний лендінг)"),
}


@admin.register(SiteSettings)
class SiteSettingsAdmin(SingletonModelAdmin, TranslationAdmin):
    change_form_template = "admin/core/sitesettings/change_form.html"
    group_fieldsets = False

    class Media:
        js = (
            "modeltranslation/js/force_jquery.js",
            "https://ajax.googleapis.com/ajax/libs/jqueryui/1.13.2/jquery-ui.min.js",
            "modeltranslation/js/tabbed_translation_fields.js",
        )
        css = {"screen": ("modeltranslation/css/tabbed_translation_fields.css",)}

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "apply-preset/<str:name>/",
                self.admin_site.admin_view(self.apply_preset_view),
                name="core_sitesettings_apply_preset",
            ),
        ]
        return custom + urls

    def apply_preset_view(self, request, name):
        if name not in PRESETS:
            messages.error(request, _("Невідомий пресет: %s") % name)
            return HttpResponseRedirect(reverse("admin:core_sitesettings_changelist"))
        settings_obj = SiteSettings.get_solo()
        touched = apply_preset(settings_obj, name)
        messages.success(
            request,
            _("Пресет «%(label)s» застосовано. Оновлено %(n)d полів.")
            % {"label": PRESET_LABELS.get(name, name), "n": len(touched)},
        )
        return HttpResponseRedirect(reverse("admin:core_sitesettings_changelist"))

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["preset_choices"] = [
            (key, PRESET_LABELS.get(key, key)) for key in PRESETS
        ]
        return super().changeform_view(request, object_id, form_url, extra_context)

    fieldsets = (
        (_("Загальне"), {
            "fields": ("preset", "theme", "brand_name", "brand_style", "tagline", "brand_logo", "favicon",
                       "meta_description", "footer_copyright", "cta_label", "cart_enabled"),
        }),
        (_("Контакти"), {
            "fields": ("contact_phone", "contact_email", "contact_address"),
        }),
        (_("Бокові лого"), {
            "fields": ("side_logo_left", "side_logo_right", "side_logo_size"),
            "description": _(
                "Великі лого по краях на широких екранах (фіксовані при прокручуванні); "
                "на смартфоні показуються в ряд унизу перед футером."
            ),
        }),
        (_("Меню — Каталог"), {"fields": ("nav_catalog_visible", "nav_catalog_label")}),
        (_("Меню — Бренди"), {"fields": ("nav_brands_visible", "nav_brands_label")}),
        (_("Меню — Акції"), {"fields": ("nav_promos_visible", "nav_promos_label")}),
        (_("Меню — Новини"), {"fields": ("nav_news_visible", "nav_news_label")}),
        (_("Меню — Вакансії"), {"fields": ("nav_vacancies_visible", "nav_vacancies_label")}),
        (_("Меню — Контакти"), {"fields": ("nav_contacts_visible", "nav_contacts_label")}),
        (_("Терміни сутностей"), {
            "fields": ("term_product_singular", "term_product_plural",
                       "term_brand_singular", "term_brand_plural",
                       "term_category_singular", "term_category_plural"),
        }),
        (_("Лейбли карти вакансії"), {
            "fields": ("vacancy_description_label", "vacancy_requirements_label",
                       "vacancy_conditions_label", "vacancy_apply_label"),
        }),
        (_("Головна сторінка (Hero)"), {
            "fields": ("home_layout", "hero_eyebrow", "hero_title", "hero_subtitle"),
        }),
        (_("Анімації та ефекти"), {
            "fields": ("anim_page_transitions", "anim_scroll_reveal",
                       "anim_kinetic_hero", "anim_magnetic_buttons", "anim_cursor_follower"),
        }),
    )
