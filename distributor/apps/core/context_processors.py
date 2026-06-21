"""Context processors shared across apps."""

from __future__ import annotations

from typing import Any

from django.db.utils import OperationalError, ProgrammingError
from django.http import HttpRequest

from .models import PageBackground, SiteSettings


def page_background(request: HttpRequest) -> dict[str, Any]:
    """Pick the active background for the current page (or the site-wide fallback).

    Resolution order:
      1. PageBackground with ``page_key`` matching the resolved url ``namespace:url_name``
      2. PageBackground with ``page_key == "site"`` (global default)
      3. None (no background)
    """
    current_key: str | None = None
    match = getattr(request, "resolver_match", None)
    if match is not None and match.url_name:
        current_key = f"{match.namespace}:{match.url_name}" if match.namespace else match.url_name

    try:
        qs = PageBackground.objects.filter(is_active=True)
        backgrounds = {bg.page_key: bg for bg in qs}
    except (OperationalError, ProgrammingError):
        return {"page_background": None, "page_background_overlay": 0}

    chosen = None
    if current_key and current_key in backgrounds:
        chosen = backgrounds[current_key]
    elif PageBackground.SITE_KEY in backgrounds:
        chosen = backgrounds[PageBackground.SITE_KEY]

    if chosen is None or not chosen.image:
        return {"page_background": None, "page_background_overlay": 0}

    return {
        "page_background": chosen.image.url,
        "page_background_overlay": max(0, min(chosen.overlay_opacity, 90)),
    }


def site_settings(request: HttpRequest) -> dict[str, Any]:
    """Expose the SiteSettings singleton in every template as ``site_settings``."""
    try:
        settings_obj = SiteSettings.get_solo()
    except (OperationalError, ProgrammingError):
        return {"site_settings": None}
    return {"site_settings": settings_obj}
