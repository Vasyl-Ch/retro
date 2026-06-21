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

# ``data:`` is allowed for <img> (Summernote inlines pasted images as base64);
# <img> cannot execute script even with an SVG data URI. ``javascript:`` is excluded.
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
