from django.db import models
from django.utils.translation import gettext_lazy as _


class ContactRequest(models.Model):
    SUBJECT_CHOICES = [
        ("general", _("Загальне питання")),
        ("product", _("Питання щодо товару")),
        ("partnership", _("Партнерство")),
        ("vacancy", _("Вакансія")),
    ]
    name = models.CharField(_("Ім’я"), max_length=200)
    phone = models.CharField(_("Телефон"), max_length=30, blank=True)
    email = models.EmailField("Email", blank=True)
    subject = models.CharField(
        _("Тема"),
        max_length=20,
        choices=SUBJECT_CHOICES,
        default="general",
    )
    message = models.TextField(_("Повідомлення"))
    is_read = models.BooleanField(_("Прочитано"), default=False)
    created_at = models.DateTimeField(_("Дата"), auto_now_add=True)

    class Meta:
        verbose_name = _("Звернення")
        verbose_name_plural = _("Звернення")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} — {self.get_subject_display()}"
