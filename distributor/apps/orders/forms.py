from django import forms
from django.utils.translation import gettext_lazy as _

from apps.core.validators import validate_contactable

from .models import Order

_INPUT = "input variant-outlined sz-md w-full"
_TEXTAREA = "textarea variant-outlined sz-md w-full"


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["name", "phone", "email", "comment"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": _INPUT, "placeholder": _("Your name")}
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": _INPUT,
                    "placeholder": "Your Phone Number",
                    "pattern": r"[\+\d\s\-\(\)]{7,20}",
                }
            ),
            "email": forms.EmailInput(
                attrs={"class": _INPUT, "placeholder": "email@example.com"}
            ),
            "comment": forms.Textarea(
                attrs={"class": _TEXTAREA, "placeholder": _("Order comment"), "rows": 3}
            ),
        }

    def clean(self) -> dict:
        cleaned = super().clean()
        validate_contactable(cleaned.get("phone"), cleaned.get("email"))
        return cleaned
