"""HTML sanitization for rich-text (Summernote) content.

Staff-entered HTML is rendered with ``|safe`` in templates, so it must be
reduced to a strict allow-list before storage to prevent stored XSS.
"""

import bleach

ALLOWED_TAGS = [
    "p", "br", "span", "div",
    "h2", "h3", "h4",
    "strong", "b", "em", "i", "u", "s",
    "ul", "ol", "li",
    "blockquote", "hr",
    "a", "img",
    "table", "thead", "tbody", "tr", "th", "td",
]

ALLOWED_ATTRIBUTES = {
    "*": ["class"],
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "width", "height"],
    "td": ["colspan", "rowspan"],
    "th": ["colspan", "rowspan"],
}

# ``data:`` is allowed so Summernote's pasted/inline base64 images (<img src="data:...">)
# survive sanitization. bleach 4.x applies protocols globally (not per-tag), so a
# ``data:`` URI is also permitted on <a href>. Under this CMS's staff-only authoring
# model that residual phishing-style vector is accepted; ``javascript:`` is NOT in the
# list, so no script execution is possible via any attribute.
ALLOWED_PROTOCOLS = ["http", "https", "mailto", "data"]


def sanitize_html(value: str | None) -> str:
    """Return *value* reduced to the allow-list; disallowed tags are stripped."""
    if not value:
        return ""
    return bleach.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )


def sanitize_instance_html(instance, *field_names, languages=("en", "uk")):
    """Sanitize rich-text fields on `instance`, including modeltranslation
    language variants (<field>_<lang>) when those attributes exist."""
    for base in field_names:
        for name in (base, *(f"{base}_{lang}" for lang in languages)):
            if hasattr(instance, name):
                value = getattr(instance, name)
                if value:
                    setattr(instance, name, sanitize_html(value))
