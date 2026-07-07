"""Shared form validators."""

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _


def validate_contactable(phone: str | None, email: str | None) -> None:
    """Require at least one contact method — phone or email.

    Used in the contact and checkout forms (DRY).
    """
    if not (phone or "").strip() and not (email or "").strip():
        raise ValidationError(
            _("Please provide at least one contact method: phone or email.")
        )


MAX_IMAGE_MB = 5
MAX_IMAGE_BYTES = MAX_IMAGE_MB * 1024 * 1024

RASTER_EXTENSIONS = ["jpg", "jpeg", "png", "webp", "gif"]
BRANDING_EXTENSIONS = RASTER_EXTENSIONS + ["svg"]


def validate_image_size(file) -> None:
    """Reject uploads larger than MAX_IMAGE_BYTES."""
    size = getattr(file, "size", None)
    if size and size > MAX_IMAGE_BYTES:
        raise ValidationError(
            _("File is too large (%(size)s). Maximum is %(max)s."),
            params={"size": filesizeformat(size), "max": filesizeformat(MAX_IMAGE_BYTES)},
        )


def validate_json_object(value: str) -> None:
    """Require the value to be a JSON *object* (used for custom background configs)."""
    if not value:
        return
    import json

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValidationError(
            _("Invalid JSON: %(error)s"), params={"error": exc.msg}
        ) from exc
    if not isinstance(parsed, dict):
        raise ValidationError(_("The config must be a JSON object: { ... }"))


def validate_css_declarations(value: str) -> None:
    """Allow only plain `prop: value;` pairs — no braces/at-rules/markup.

    Used for the constructor's "extra CSS" field so an admin typo cannot break
    out of the generated rule or inject markup.
    """
    if not value:
        return
    if any(ch in value for ch in "{}<>@"):
        raise ValidationError(
            _("Only simple declarations are allowed, e.g. “letter-spacing: 2px;” "
              "(no braces, @-rules or HTML).")
        )
    for part in value.split(";"):
        part = part.strip()
        if part and ":" not in part:
            raise ValidationError(
                _("Each declaration must look like “property: value;” — check “%(part)s”."),
                params={"part": part},
            )


raster_image_validators = [
    FileExtensionValidator(allowed_extensions=RASTER_EXTENSIONS),
    validate_image_size,
]
branding_image_validators = [
    FileExtensionValidator(allowed_extensions=BRANDING_EXTENSIONS),
    validate_image_size,
]
