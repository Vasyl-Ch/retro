from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_summernote.fields import SummernoteTextField

from apps.core.sanitizer import sanitize_html


class Vacancy(models.Model):
    title = models.CharField(_("Заголовок"), max_length=300)
    slug = models.SlugField("Slug", max_length=300, unique=True, blank=True)
    city = models.CharField(_("Локація"), max_length=100, blank=True)
    short_tagline = models.CharField(
        _("Короткий підпис"), max_length=200, blank=True,
        help_text=_("Один рядок під заголовком."),
    )
    cover_image = models.ImageField(
        _("Головне фото"), upload_to="vacancies/", blank=True, null=True,
        help_text=_("Велике зображення зверху картки і сторінки. Опціонально."),
    )
    description = SummernoteTextField(_("Опис"))
    requirements = SummernoteTextField(_("Вимоги"), blank=True)
    conditions = SummernoteTextField(_("Умови"), blank=True)
    is_active = models.BooleanField(_("Активна"), default=True)
    is_urgent = models.BooleanField(_("Виділити"), default=False)
    order = models.PositiveIntegerField(_("Порядок"), default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Вакансія")
        verbose_name_plural = _("Вакансії")
        ordering = ["order", "-is_urgent", "-created_at"]

    def __str__(self) -> str:
        return f"{self.title} — {self.city}"

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.title)
        self.description = sanitize_html(self.description)
        self.requirements = sanitize_html(self.requirements)
        self.conditions = sanitize_html(self.conditions)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("vacancies:detail", kwargs={"slug": self.slug})


class VacancyImage(models.Model):
    """Додаткові фото для картки (галерея)."""

    vacancy = models.ForeignKey(
        Vacancy, on_delete=models.CASCADE, related_name="images",
        verbose_name=_("Вакансія / Товар"),
    )
    image = models.ImageField(_("Зображення"), upload_to="vacancies/gallery/")
    caption = models.CharField(_("Підпис"), max_length=200, blank=True)
    order = models.PositiveIntegerField(_("Порядок"), default=0)

    class Meta:
        verbose_name = _("Фото вакансії")
        verbose_name_plural = _("Фото вакансій")
        ordering = ["order"]

    def __str__(self) -> str:
        return self.caption or f"Фото #{self.order}"
