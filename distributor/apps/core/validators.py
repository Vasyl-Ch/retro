"""Спільні валідатори форм."""

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _


def validate_contactable(phone: str | None, email: str | None) -> None:
    """Вимагає хоча б один спосіб зв’язку — телефон або email.

    Використовується у формах контактів і оформлення замовлення (DRY).
    """
    if not (phone or "").strip() and not (email or "").strip():
        raise ValidationError(
            _("Вкажіть хоча б один спосіб зв’язку: телефон або email.")
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
            _("Файл завеликий (%(size)s). Максимум — %(max)s."),
            params={"size": filesizeformat(size), "max": filesizeformat(MAX_IMAGE_BYTES)},
        )


raster_image_validators = [
    FileExtensionValidator(allowed_extensions=RASTER_EXTENSIONS),
    validate_image_size,
]
branding_image_validators = [
    FileExtensionValidator(allowed_extensions=BRANDING_EXTENSIONS),
    validate_image_size,
]
