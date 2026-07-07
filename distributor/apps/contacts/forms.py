from django import forms
from django.utils.translation import gettext_lazy as _

from apps.core.validators import validate_contactable

from .models import ContactRequest


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactRequest
        fields = ["name", "phone", "email", "subject", "message"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "input variant-outlined w-full",
                    "placeholder": _("Your name"),
                    "autocomplete": "name",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "input variant-outlined w-full",
                    "placeholder": "Your Phone Number",
                    "pattern": r"[\+\d\s\-\(\)]{7,20}",
                    "autocomplete": "tel",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "input variant-outlined w-full",
                    "placeholder": "email@example.com",
                    "autocomplete": "email",
                }
            ),
            "subject": forms.Select(
                attrs={
                    "class": "input variant-outlined w-full",
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "class": "input variant-outlined w-full",
                    "placeholder": _("Your message"),
                    "rows": 4,
                }
            ),
        }

    def clean(self) -> dict:
        cleaned = super().clean()
        validate_contactable(cleaned.get("phone"), cleaned.get("email"))
        return cleaned
