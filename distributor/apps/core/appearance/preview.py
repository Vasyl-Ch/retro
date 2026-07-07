"""Helpers for the admin constructor's live-preview iframe."""

from __future__ import annotations

from django.urls import NoReverseMatch, reverse

# Detail pages need a real object; map each detail key to a sampler returning
# the first active instance (imported lazily to avoid app-loading cycles).
_DETAIL_FALLBACK_LIST = {
    "catalog:product_detail": "catalog:product_list",
    "brands:brand_detail": "brands:brand_list",
    "content:promo_detail": "content:promo_list",
    "content:news_detail": "content:news_list",
    "vacancies:detail": "vacancies:list",
}


def _first_object(page_key: str):
    if page_key == "catalog:product_detail":
        from apps.catalog.models import Product
        return Product.objects.filter(is_active=True).first()
    if page_key == "brands:brand_detail":
        from apps.catalog.models import Brand
        return Brand.objects.filter(is_active=True).first()
    if page_key == "content:promo_detail":
        from apps.content.models import Promo
        return Promo.objects.filter(is_active=True).first()
    if page_key == "content:news_detail":
        from apps.content.models import News
        return News.objects.filter(is_active=True).first()
    if page_key == "vacancies:detail":
        from apps.vacancies.models import Vacancy
        return Vacancy.objects.filter(is_active=True).first()
    return None


def preview_url_for(page_key: str) -> str:
    """URL to show in the constructor preview iframe for the given page key.

    List pages reverse directly; detail pages use the first active object and
    fall back to their list page (then to the home page) when there is none.
    """
    if not page_key or page_key == "site":
        return "/"
    if page_key in _DETAIL_FALLBACK_LIST:
        obj = _first_object(page_key)
        if obj is not None:
            try:
                return obj.get_absolute_url()
            except NoReverseMatch:  # pragma: no cover — defensive
                pass
        page_key = _DETAIL_FALLBACK_LIST[page_key]
    try:
        return reverse(page_key)
    except NoReverseMatch:
        return "/"
