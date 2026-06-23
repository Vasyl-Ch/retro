"""Preset-aware admin branding.

On requests to /admin, adjusts Jazzmin headings and section/model names to match the current
preset (reading SiteSettings). Values come from fields that already depend on the preset
(brand_name, nav_*_label, term_*), so the admin panel "re-dresses" along with the site.

Note: _meta.verbose_name and app_config.verbose_name are mutated at runtime. The value
depends only on the singleton preset, so all threads set the same value — no race conditions.
"""

from __future__ import annotations

from django.apps import apps as django_apps
from django.conf import settings
from django.contrib import admin
from django.db.utils import OperationalError, ProgrammingError
from django.utils.translation import gettext_lazy as _

from .models import SiteSettings


def _set_model_labels(model, singular, plural):
    if singular:
        model._meta.verbose_name = singular
    if plural:
        model._meta.verbose_name_plural = plural


class PresetAdminBrandingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin"):
            self._apply_branding()
        return self.get_response(request)

    def _apply_branding(self) -> None:
        try:
            s = SiteSettings.get_solo()
        except (OperationalError, ProgrammingError):
            return

        brand = s.brand_name or "Admin"

        # 1. Django core admin site
        admin.site.site_header = brand
        admin.site.site_title = brand
        admin.site.index_title = _("Site management")

        # 2. Jazzmin branding (mutate the same dict that jazzmin reads)
        jazz = getattr(settings, "JAZZMIN_SETTINGS", None)
        if isinstance(jazz, dict):
            jazz["site_title"] = brand
            jazz["site_header"] = brand
            jazz["site_brand"] = brand
            jazz["welcome_sign"] = _("Welcome — %(brand)s") % {"brand": brand}
            jazz["copyright"] = s.footer_copyright or brand

        # 3. Section/model names per vertical
        self._rename_app("catalog", s.nav_catalog_label)
        self._rename_app("vacancies", s.nav_vacancies_label)
        try:
            from apps.catalog.models import Brand, Category, Product

            _set_model_labels(Product, s.term_product_singular, s.term_product_plural)
            _set_model_labels(Brand, s.term_brand_singular, s.term_brand_plural)
            _set_model_labels(Category, s.term_category_singular, s.term_category_plural)
        except Exception:
            pass

    @staticmethod
    def _rename_app(app_label: str, label) -> None:
        if not label:
            return
        try:
            django_apps.get_app_config(app_label).verbose_name = label
        except LookupError:
            pass
