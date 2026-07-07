"""Element-level style overrides: the anchor registry + a pure CSS builder.

Templates mark customizable elements with ``data-el="<key>"`` and every page
sets ``data-page="<namespace:url_name>"`` on <body>.  An ElementStyle row is
(page, element, style values); this module turns those values into scoped CSS.

Pure (no Django imports) so the admin live preview and the server render share
one code path — same DRY boundary as ``services.py``.
"""
from __future__ import annotations

from dataclasses import dataclass, fields as dataclass_fields
from typing import Any, Iterable

# ---------------------------------------------------------------------------
# Registry of customizable anchors (data-el="..." in templates).
# Key -> human label (labels are translated at the model layer).
# ---------------------------------------------------------------------------
ELEMENTS: list[tuple[str, str]] = [
    ("navbar", "Navbar (header)"),
    ("navbar-brand", "Navbar — brand (logo + name)"),
    ("navbar-menu", "Navbar — menu links"),
    ("navbar-cta", "Navbar — CTA button"),
    ("hero", "Hero — whole section"),
    ("hero-eyebrow", "Hero — eyebrow (small text above title)"),
    ("hero-title", "Hero — main title"),
    ("hero-subtitle", "Hero — subtitle"),
    ("hero-actions", "Hero — action buttons"),
    ("hero-collage", "Hero — banner collage strip"),
    ("section-brands", "Home — brands section"),
    ("section-promos", "Home — promotions section"),
    ("section-featured", "Home — featured products section"),
    ("section-news", "Home — news section"),
    ("section-heading", "Section headings (h2)"),
    ("page-title", "Page title (h1 on inner pages)"),
    ("card-product", "Product card"),
    ("card-promo", "Promo card"),
    ("card-news", "News card"),
    ("filters", "Catalog — filters panel"),
    ("pagination", "Pagination"),
    ("content-body", "Main content area"),
    ("side-logos", "Side logos"),
    ("footer", "Footer"),
    ("footer-brand", "Footer — brand block"),
    ("contact-form", "Contact form"),
    ("cta-button", "All primary buttons"),
]

ELEMENT_KEYS = {key for key, _label in ELEMENTS}

SITE_KEY = "site"

TEXT_ALIGN_VALUES = ("left", "center", "right")

# effect key -> animation shorthand (keyframes live in tailus.css)
EFFECTS: dict[str, str] = {
    "float": "el-float calc(6s * var(--el-speed, 1)) ease-in-out infinite",
    "pulse": "el-pulse calc(3s * var(--el-speed, 1)) ease-in-out infinite",
    "fade-in": "el-fade-in 0.9s ease-out both",
    "slide-up": "el-slide-up 0.9s ease-out both",
}


def _int(value: Any, default: int | None = None) -> int | None:
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class ElementStyleValues:
    """Style knobs for one element; mirrors the ElementStyle model fields."""

    page_key: str = SITE_KEY
    element_key: str = ""
    text_color: str = ""
    bg_color: str = ""
    opacity: int = 100          # 0..100, whole-element opacity
    font_size: int | None = None    # px; None = keep theme size
    text_align: str = ""            # ""/left/center/right
    offset_x: int = 0               # px, CSS `translate` (safe with GSAP transforms)
    offset_y: int = 0
    scale: int = 100                # %, CSS `scale`
    max_width: int | None = None    # px
    border_radius: int | None = None  # px
    padding: int | None = None      # px
    hidden: bool = False
    effect: str = ""                # key into EFFECTS
    custom_css: str = ""            # extra declarations (validated at the form layer)

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "ElementStyleValues":
        """Build from raw strings (e.g. request.GET) — tolerant of junk."""
        return cls(
            page_key=str(data.get("page_key") or SITE_KEY),
            element_key=str(data.get("element_key") or ""),
            text_color=str(data.get("text_color") or ""),
            bg_color=str(data.get("bg_color") or ""),
            opacity=min(100, max(0, _int(data.get("opacity"), 100) or 100)),
            font_size=_int(data.get("font_size")),
            text_align=str(data.get("text_align") or ""),
            offset_x=_int(data.get("offset_x"), 0) or 0,
            offset_y=_int(data.get("offset_y"), 0) or 0,
            scale=_int(data.get("scale"), 100) or 100,
            max_width=_int(data.get("max_width")),
            border_radius=_int(data.get("border_radius")),
            padding=_int(data.get("padding")),
            hidden=str(data.get("hidden") or "") in ("1", "true", "True", "on"),
            effect=str(data.get("effect") or ""),
            custom_css=str(data.get("custom_css") or ""),
        )

    @classmethod
    def from_model(cls, obj: Any) -> "ElementStyleValues":
        kwargs = {}
        for f in dataclass_fields(cls):
            kwargs[f.name] = getattr(obj, f.name, f.default)
        return cls(**kwargs)


# Elements addressed by an existing class/tag instead of a data-el anchor.
SELECTOR_OVERRIDES: dict[str, str] = {
    "cta-button": ".btn.variant-primary",
    "section-heading": "main section h2",
    "page-title": "main h1",
}


def element_selector(values: ElementStyleValues) -> str:
    """Scoped selector: site-wide, or narrowed to one page via body[data-page]."""
    base = SELECTOR_OVERRIDES.get(values.element_key, f'[data-el="{values.element_key}"]')
    if values.page_key and values.page_key != SITE_KEY:
        return f'body[data-page="{values.page_key}"] {base}'
    return base


def _sanitize_custom_css(custom: str) -> list[str]:
    """Keep only `prop: value` pairs; drop anything that could escape the rule."""
    decls = []
    for part in custom.split(";"):
        part = part.strip()
        if not part or ":" not in part:
            continue
        if any(ch in part for ch in "{}<>@"):
            continue
        prop, _, value = part.partition(":")
        if prop.strip().replace("-", "").isalnum() and value.strip():
            decls.append(f"{prop.strip()}: {value.strip()}")
    return decls


def element_declarations(values: ElementStyleValues) -> list[str]:
    """CSS declarations for one element (empty list = nothing customized).

    Colors/typography get ``!important`` so the constructor reliably beats the
    theme utility classes; offsets use the standalone ``translate``/``scale``
    properties so GSAP's inline ``transform`` (magnetic buttons) keeps working.
    """
    if values.hidden:
        return ["display: none !important"]
    d: list[str] = []
    if values.text_color:
        d.append(f"color: {values.text_color} !important")
    if values.bg_color:
        d.append(f"background-color: {values.bg_color} !important")
    if values.opacity != 100:
        d.append(f"opacity: {max(0, min(100, values.opacity)) / 100:g}")
    if values.font_size:
        d.append(f"font-size: {values.font_size}px !important")
    if values.text_align in TEXT_ALIGN_VALUES:
        d.append(f"text-align: {values.text_align} !important")
    if values.offset_x or values.offset_y:
        d.append(f"translate: {values.offset_x}px {values.offset_y}px")
    if values.scale != 100:
        d.append(f"scale: {max(10, min(300, values.scale)) / 100:g}")
    if values.max_width:
        d.append(f"max-width: {values.max_width}px !important")
    if values.border_radius is not None:
        d.append(f"border-radius: {values.border_radius}px !important")
    if values.padding is not None:
        d.append(f"padding: {values.padding}px !important")
    if values.effect in EFFECTS:
        d.append(f"animation: {EFFECTS[values.effect]}")
    d.extend(_sanitize_custom_css(values.custom_css))
    return d


def build_element_css(styles: Iterable[Any]) -> str:
    """Full CSS block for a set of ElementStyle rows / value objects.

    Site-wide rules are emitted before page-scoped ones so a page rule always
    wins (higher specificity *and* source order).
    """
    resolved = [
        v if isinstance(v, ElementStyleValues) else ElementStyleValues.from_model(v)
        for v in styles
    ]
    resolved = [v for v in resolved if v.element_key in ELEMENT_KEYS]
    resolved.sort(key=lambda v: (v.page_key != SITE_KEY, v.page_key, v.element_key))
    rules = []
    for v in resolved:
        decls = element_declarations(v)
        if decls:
            rules.append(f"{element_selector(v)} {{ {'; '.join(decls)}; }}")
    return "\n".join(rules)
