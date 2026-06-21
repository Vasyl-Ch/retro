"""Template tags for wiring the Vite-built Ada bundle into Django templates."""

import json
from pathlib import Path

from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils.safestring import mark_safe

register = template.Library()

_MANIFEST_PATH = Path(settings.BASE_DIR) / "static" / "ada" / ".vite" / "manifest.json"
_ENTRY = "main.js"
_manifest_cache: dict | None = None


def _load_manifest() -> dict:
    global _manifest_cache
    if _manifest_cache is None or settings.DEBUG:
        _manifest_cache = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    return _manifest_cache


@register.simple_tag
def vite_css() -> str:
    entry = _load_manifest().get(_ENTRY, {})
    css_files = entry.get("css") or []
    if not css_files:
        return ""
    links = "\n".join(
        f'<link rel="stylesheet" href="{static("ada/" + path)}">' for path in css_files
    )
    return mark_safe(links)


@register.simple_tag
def vite_js() -> str:
    entry = _load_manifest().get(_ENTRY, {})
    file = entry.get("file")
    if not file:
        return ""
    return mark_safe(f'<script type="module" src="{static("ada/" + file)}"></script>')
