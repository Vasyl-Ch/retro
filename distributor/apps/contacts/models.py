from django.db import models
from django.utils.translation import gettext_lazy as _


class ContactRequest(models.Model):
    SUBJECT_CHOICES = [
        ("general", _("General inquiry")),
        ("product", _("Product inquiry")),
        ("partnership", _("Partnership")),
        ("vacancy", _("Vacancy")),
    ]
    name = models.CharField(_("Name"), max_length=200)
    phone = models.CharField(_("Phone"), max_length=30, blank=True)
    email = models.EmailField("Email", blank=True)
    subject = models.CharField(
        _("Subject"),
        max_length=20,
        choices=SUBJECT_CHOICES,
        default="general",
    )
    message = models.TextField(_("Message"))
    is_read = models.BooleanField(_("Read"), default=False)
    created_at = models.DateTimeField(_("Date"), auto_now_add=True)

    class Meta:
        verbose_name = _("Inquiries")
        verbose_name_plural = _("Inquiries")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} — {self.get_subject_display()}"
