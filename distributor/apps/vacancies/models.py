from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from apps.core.fields import SummernoteTextField
from apps.core.sanitizer import sanitize_html
from apps.core.validators import raster_image_validators


class Vacancy(models.Model):
    title = models.CharField(_("Title"), max_length=300)
    slug = models.SlugField("Slug", max_length=300, unique=True, blank=True)
    city = models.CharField(_("Location"), max_length=100, blank=True)
    short_tagline = models.CharField(
        _("Short caption"), max_length=200, blank=True,
        help_text=_("A single line under the heading."),
    )
    cover_image = models.ImageField(
        _("Main photo"), upload_to="vacancies/", blank=True, null=True,
        validators=raster_image_validators,
        help_text=_("Large image at the top of the card and page. Optional."),
    )
    description = SummernoteTextField(_("Description"))
    requirements = SummernoteTextField(_("Requirements"), blank=True)
    conditions = SummernoteTextField(_("Conditions"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    is_urgent = models.BooleanField(_("Highlight"), default=False)
    order = models.PositiveIntegerField(_("Order"), default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Vacancy")
        verbose_name_plural = _("Vacancies")
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
        verbose_name=_("Vacancy / Product"),
    )
    image = models.ImageField(_("Image"), upload_to="vacancies/gallery/",
                              validators=raster_image_validators)
    caption = models.CharField(_("Caption"), max_length=200, blank=True)
    order = models.PositiveIntegerField(_("Order"), default=0)

    class Meta:
        verbose_name = _("Vacancy photo")
        verbose_name_plural = _("Vacancy photos")
        ordering = ["order"]

    def __str__(self) -> str:
        return self.caption or f"Фото #{self.order}"
