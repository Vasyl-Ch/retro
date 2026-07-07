"""Reusable admin helpers shared across apps."""

from typing import Any

from django.contrib import admin, messages
from django.db.models.fields.files import ImageFieldFile
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import path, reverse

from apps.core.appearance.elements import ElementStyleValues, build_element_css
from apps.core.appearance.preview import preview_url_for
from apps.core.appearance.services import preview_vars
from django.utils.html import format_html
from django.utils.safestring import SafeString
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin
from solo.admin import SingletonModelAdmin

from .models import ElementStyle, PageBackground, SiteSettings
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

        logo_preview = image_preview_method('logo', description='Logo', height=40)
    """

    def _preview(self: Any, obj: Any) -> SafeString | str:
        return image_thumbnail(getattr(obj, field_name), **thumbnail_kwargs)

    _preview.short_description = description  # type: ignore[attr-defined]
    return _preview


@admin.register(PageBackground)
class PageBackgroundAdmin(admin.ModelAdmin):
    change_form_template = "admin/core/pagebackground/change_form.html"
    list_display = ["image_preview", "page_label", "kind", "is_active", "overlay_opacity", "updated_at"]
    list_editable = ["is_active", "overlay_opacity"]
    list_display_links = ["image_preview", "page_label"]
    list_filter = ["is_active", "kind"]
    readonly_fields = ["updated_at"]
    fieldsets = (
        (None, {
            "fields": ("page_key", "kind", "is_active", "overlay_opacity", "updated_at"),
            "description": _("Uncheck “Active” to remove the background from the page entirely."),
        }),
        (_("Image background"), {
            "fields": ("image", "position", "size"),
            "description": _("Used when the type is “Image”."),
        }),
        (_("Animated background"), {
            "fields": ("color_1", "color_2", "color_3", "speed", "custom_config"),
            "description": _(
                "Used by the animated types. Leave colours empty to inherit the theme's "
                "accent colour. The JSON config applies to the “Custom” type only."
            ),
        }),
    )

    image_preview = image_preview_method("image", description=_("Background"), height=50, width=90)

    @admin.display(description=_("Page"), ordering="page_key")
    def page_label(self, obj: PageBackground) -> str:
        return obj.get_page_key_display()

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["preview_urls"] = {
            key: preview_url_for(key) for key, _label in PageBackground.PAGE_CHOICES
        }
        return super().changeform_view(request, object_id, form_url, extra_context)


ELEMENT_STYLE_VALUE_FIELDS = [
    "text_color", "bg_color", "opacity", "font_size", "text_align",
    "offset_x", "offset_y", "scale", "max_width", "border_radius",
    "padding", "hidden", "effect", "custom_css",
]


@admin.register(ElementStyle)
class ElementStyleAdmin(admin.ModelAdmin):
    change_form_template = "admin/core/elementstyle/change_form.html"
    list_display = ["element_label", "page_label", "is_active", "updated_at"]
    list_editable = ["is_active"]
    list_filter = ["is_active", "page_key", "element_key"]
    readonly_fields = ["updated_at"]
    fieldsets = (
        (None, {"fields": ("page_key", "element_key", "is_active")}),
        (_("Colours & transparency"), {"fields": ("text_color", "bg_color", "opacity")}),
        (_("Size & position"), {
            "fields": ("scale", "font_size", "text_align",
                       "offset_x", "offset_y", "max_width", "padding", "border_radius"),
        }),
        (_("Effects"), {"fields": ("effect", "hidden", "custom_css")}),
        (None, {"fields": ("updated_at",)}),
    )

    @admin.display(description=_("Element"), ordering="element_key")
    def element_label(self, obj: ElementStyle) -> str:
        return obj.get_element_key_display()

    @admin.display(description=_("Page"), ordering="page_key")
    def page_label(self, obj: ElementStyle) -> str:
        return obj.get_page_key_display()

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "preview-css/",
                self.admin_site.admin_view(self.preview_css_view),
                name="core_elementstyle_preview_css",
            ),
        ]
        return custom + urls

    def preview_css_view(self, request):
        """Full element CSS with the (unsaved) form values swapped in.

        The saved rule for the edited (page, element) pair is excluded so the
        preview exactly matches what a save would produce.
        """
        values = ElementStyleValues.from_mapping(request.GET.dict())
        exclude_pk = request.GET.get("object_id") or None
        styles = ElementStyle.objects.filter(is_active=True)
        if exclude_pk and str(exclude_pk).isdigit():
            styles = styles.exclude(pk=int(exclude_pk))
        styles = [
            s for s in styles
            if not (s.page_key == values.page_key and s.element_key == values.element_key)
        ]
        css = build_element_css([*styles, values])
        return JsonResponse({"css": css})

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["preview_urls"] = {
            key: preview_url_for(key) for key, _label in PageBackground.PAGE_CHOICES
        }
        extra_context["object_id_for_preview"] = object_id or ""
        return super().changeform_view(request, object_id, form_url, extra_context)


PRESET_LABELS = {
    "distributor": _("Distributor"),
    "auto": _("Auto (dealership)"),
    "food": _("Restaurant / Food"),
    "shop": _("Shop (store with cart)"),
    "generic": _("Generic (universal landing)"),
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
            path(
                "preview-css/",
                self.admin_site.admin_view(self.preview_css_view),
                name="core_sitesettings_preview_css",
            ),
        ]
        return custom + urls

    def preview_css_view(self, request):
        return JsonResponse(preview_vars(
            accent=request.GET.get("accent", ""),
            chrome_bg=request.GET.get("chrome_bg", ""),
            chrome_text=request.GET.get("chrome_text", ""),
            chrome_opacity=request.GET.get("chrome_opacity", 100) or 100,
        ))

    def apply_preset_view(self, request, name):
        if name not in PRESETS:
            messages.error(request, _("Unknown preset: %s") % name)
            return HttpResponseRedirect(reverse("admin:core_sitesettings_changelist"))
        settings_obj = SiteSettings.get_solo()
        touched = apply_preset(settings_obj, name)
        messages.success(
            request,
            _("Preset “%(label)s” applied. %(n)d fields updated.")
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
        (_("General"), {
            "fields": ("preset", "theme", "brand_name", "brand_style", "tagline", "brand_logo", "favicon",
                       "meta_description", "footer_copyright", "cta_label", "cart_enabled"),
        }),
        (_("Appearance (colors & transparency)"), {
            "fields": ("custom_accent", "chrome_bg", "chrome_text", "chrome_opacity", "corner_style"),
            "description": _("Live preview updates below as you change these."),
        }),
        (_("Contacts"), {
            "fields": ("contact_phone", "contact_email", "contact_address"),
        }),
        (_("Side logos"), {
            "fields": ("side_logo_left", "side_logo_right", "side_logo_size"),
            "description": _(
                "Large logos on the sides on wide screens (fixed while scrolling); "
                "on mobile they appear in a row above the footer."
            ),
        }),
        (_("Menu — Catalog"), {"fields": ("nav_catalog_visible", "nav_catalog_label")}),
        (_("Menu — Brands"), {"fields": ("nav_brands_visible", "nav_brands_label")}),
        (_("Menu — Promotions"), {"fields": ("nav_promos_visible", "nav_promos_label")}),
        (_("Menu — News"), {"fields": ("nav_news_visible", "nav_news_label")}),
        (_("Menu — Vacancies"), {"fields": ("nav_vacancies_visible", "nav_vacancies_label")}),
        (_("Menu — Contacts"), {"fields": ("nav_contacts_visible", "nav_contacts_label")}),
        (_("Entity terms"), {
            "fields": ("term_product_singular", "term_product_plural",
                       "term_brand_singular", "term_brand_plural",
                       "term_category_singular", "term_category_plural"),
        }),
        (_("Vacancy card labels"), {
            "fields": ("vacancy_description_label", "vacancy_requirements_label",
                       "vacancy_conditions_label", "vacancy_apply_label"),
        }),
        (_("Home page (Hero)"), {
            "fields": ("home_layout", "hero_eyebrow", "hero_title", "hero_subtitle"),
        }),
        (_("Animations and effects"), {
            "fields": ("anim_page_transitions", "anim_scroll_reveal",
                       "anim_kinetic_hero", "anim_magnetic_buttons", "anim_cursor_follower"),
        }),
    )
