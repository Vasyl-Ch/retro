"""Context processors shared across apps."""

from __future__ import annotations

from typing import Any

from django.db.utils import OperationalError, ProgrammingError
from django.http import HttpRequest

from .models import ElementStyle, PageBackground, SiteSettings

_NO_BACKGROUND: dict[str, Any] = {
    "page_background": None,
    "page_background_kind": "",
    "page_background_overlay": 0,
    "page_background_position": "center",
    "page_background_size": "cover",
    "page_background_colors": [],
    "page_background_speed": 100,
    "page_background_is_particles": False,
    "page_background_config": "",
}


def current_page_key(request: HttpRequest) -> str | None:
    """Resolved ``namespace:url_name`` of the current page (None outside urlconf)."""
    match = getattr(request, "resolver_match", None)
    if match is not None and match.url_name:
        return f"{match.namespace}:{match.url_name}" if match.namespace else match.url_name
    return None


def page_background(request: HttpRequest) -> dict[str, Any]:
    """Pick the active background for the current page (or the site-wide fallback).

    Resolution order:
      1. PageBackground with ``page_key`` matching the resolved url ``namespace:url_name``
      2. PageBackground with ``page_key == "site"`` (global default)
      3. None (no background)
    """
    current_key = current_page_key(request)

    keys = [PageBackground.SITE_KEY]
    if current_key:
        keys.append(current_key)

    try:
        qs = PageBackground.objects.filter(is_active=True, page_key__in=keys)
        backgrounds = {bg.page_key: bg for bg in qs}
    except (OperationalError, ProgrammingError):
        return {**_NO_BACKGROUND, "page_key": current_key}

    chosen = None
    if current_key and current_key in backgrounds:
        chosen = backgrounds[current_key]
    elif PageBackground.SITE_KEY in backgrounds:
        chosen = backgrounds[PageBackground.SITE_KEY]

    if chosen is None or (chosen.kind == PageBackground.KIND_IMAGE and not chosen.image):
        return {**_NO_BACKGROUND, "page_key": current_key}

    return {
        "page_key": current_key,
        "page_background": chosen.image.url if chosen.image else None,
        "page_background_kind": chosen.kind,
        "page_background_overlay": max(0, min(chosen.overlay_opacity, 90)),
        "page_background_position": chosen.position,
        "page_background_size": chosen.size,
        "page_background_colors": chosen.colors,
        "page_background_speed": max(10, min(chosen.speed, 300)),
        "page_background_is_particles": chosen.kind in PageBackground.PARTICLE_KINDS,
        "page_background_config": chosen.custom_config or "",
    }


def site_settings(request: HttpRequest) -> dict[str, Any]:
    """Expose the SiteSettings singleton + computed appearance CSS in every template."""
    from apps.core.appearance.elements import build_element_css
    from apps.core.appearance.services import build_appearance_css

    try:
        settings_obj = SiteSettings.get_solo()
    except (OperationalError, ProgrammingError):
        return {"site_settings": None, "appearance_css": "", "element_styles_css": ""}

    current_key = current_page_key(request)
    keys = [PageBackground.SITE_KEY]
    if current_key:
        keys.append(current_key)
    try:
        styles = list(
            ElementStyle.objects.filter(is_active=True, page_key__in=keys)
        )
    except (OperationalError, ProgrammingError):
        styles = []

    return {
        "site_settings": settings_obj,
        "appearance_css": build_appearance_css(settings_obj),
        "element_styles_css": build_element_css(styles),
    }
