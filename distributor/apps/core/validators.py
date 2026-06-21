"""Спільні валідатори форм."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_contactable(phone: str | None, email: str | None) -> None:
    """Вимагає хоча б один спосіб зв'язку — телефон або email.

    Використовується у формах контактів і оформлення замовлення (DRY).
    """
    if not (phone or "").strip() and not (email or "").strip():
        raise ValidationError(
            _("Вкажіть хоча б один спосіб зв’язку: телефон або email.")
        )
