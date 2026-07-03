"""Application service mapping SiteSettings appearance fields -> CSS.

DRY boundary: both the context processor (server render) and the admin
live-preview endpoint go through here, so they can never diverge.
"""
from __future__ import annotations

from .palette import AppearanceTheme, generate_primary_ramp


def _theme(accent, chrome_bg, chrome_text, chrome_opacity) -> AppearanceTheme:
    primary = generate_primary_ramp(accent) if accent else None
    alpha = None
    if chrome_opacity is not None and int(chrome_opacity) != 100:
        alpha = max(0, min(100, int(chrome_opacity))) / 100
    return AppearanceTheme(
        primary=primary,
        chrome_bg=chrome_bg or "",
        chrome_text=chrome_text or "",
        chrome_alpha=alpha,
    )


def build_appearance_css(settings_obj) -> str:
    """CSS declarations for the SiteSettings singleton (``""`` when unset)."""
    return _theme(
        getattr(settings_obj, "custom_accent", "") or "",
        getattr(settings_obj, "chrome_bg", "") or "",
        getattr(settings_obj, "chrome_text", "") or "",
        getattr(settings_obj, "chrome_opacity", 100),
    ).to_css_declarations()


def preview_vars(*, accent="", chrome_bg="", chrome_text="", chrome_opacity=100) -> dict[str, str]:
    """CSS var map from raw (unsaved) values for the live endpoint; {} on bad input."""
    try:
        return _theme(accent, chrome_bg, chrome_text, chrome_opacity).to_css_map()
    except Exception:
        return {}
