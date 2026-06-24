from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from apps.core.fields import SummernoteTextField
from apps.core.sanitizer import sanitize_html
from apps.core.validators import raster_image_validators


class Banner(models.Model):
    title = models.CharField(_("Title"), max_length=300)
    subtitle = models.CharField(_("Subtitle"), max_length=500, blank=True)
    background = models.ImageField(_("Background"), upload_to="banners/",
                                   validators=raster_image_validators)
    button_text = models.CharField(_("Button text"), max_length=100, blank=True)
    button_url = models.CharField(_("Button URL"), max_length=500, blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    order = models.PositiveIntegerField(_("Order"), default=0)

    class Meta:
        verbose_name = _("Banner")
        verbose_name_plural = _("Banners")
        ordering = ["order"]

    def __str__(self) -> str:
        return self.title


class News(models.Model):
    title = models.CharField(_("Title"), max_length=400)
    slug = models.SlugField("Slug", max_length=400, unique=True, blank=True)
    preview = models.TextField(_("Short description"), max_length=500)
    content = SummernoteTextField(_("Full text"))
    image = models.ImageField(_("Image"), upload_to="news/",
                              validators=raster_image_validators)
    is_active = models.BooleanField(_("Published"), default=True, db_index=True)
    published_at = models.DateTimeField(_("Published at"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("News item")
        verbose_name_plural = _("News")
        ordering = ["-published_at"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.title)
        self.content = sanitize_html(self.content)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("content:news_detail", kwargs={"slug": self.slug})


class Promo(models.Model):
    title = models.CharField(_("Title"), max_length=400)
    slug = models.SlugField("Slug", max_length=400, unique=True, blank=True)
    description = SummernoteTextField(_("Description"))
    image = models.ImageField(_("Image"), upload_to="promos/",
                              validators=raster_image_validators)
    brand = models.ForeignKey(
        "catalog.Brand",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Brand"),
    )
    date_start = models.DateField(_("Promotion start"), null=True, blank=True)
    date_end = models.DateField(_("Promotion end"), null=True, blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)

    class Meta:
        verbose_name = _("Promotion")
        verbose_name_plural = _("Promotions")
        ordering = ["-date_start"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.title)
        self.description = sanitize_html(self.description)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("content:promo_detail", kwargs={"slug": self.slug})

    @property
    def is_current(self) -> bool:
        if not self.is_active:
            return False
        today = timezone.now().date()
        if self.date_start and today < self.date_start:
            return False
        if self.date_end and today > self.date_end:
            return False
        return True
