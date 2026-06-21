from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_summernote.fields import SummernoteTextField

from apps.core.sanitizer import sanitize_html


class Banner(models.Model):
    title = models.CharField(_("Заголовок"), max_length=300)
    subtitle = models.CharField(_("Підзаголовок"), max_length=500, blank=True)
    background = models.ImageField(_("Фон"), upload_to="banners/")
    button_text = models.CharField(_("Текст кнопки"), max_length=100, blank=True)
    button_url = models.CharField(_("Посилання кнопки"), max_length=500, blank=True)
    is_active = models.BooleanField(_("Активний"), default=True)
    order = models.PositiveIntegerField(_("Порядок"), default=0)

    class Meta:
        verbose_name = _("Банер")
        verbose_name_plural = _("Банери")
        ordering = ["order"]

    def __str__(self) -> str:
        return self.title


class News(models.Model):
    title = models.CharField(_("Заголовок"), max_length=400)
    slug = models.SlugField("Slug", max_length=400, unique=True, blank=True)
    preview = models.TextField(_("Короткий опис"), max_length=500)
    content = SummernoteTextField(_("Повний текст"))
    image = models.ImageField(_("Зображення"), upload_to="news/")
    is_active = models.BooleanField(_("Опублікована"), default=True)
    published_at = models.DateTimeField(_("Дата публікації"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Новина")
        verbose_name_plural = _("Новини")
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
    title = models.CharField(_("Заголовок"), max_length=400)
    slug = models.SlugField("Slug", max_length=400, unique=True, blank=True)
    description = SummernoteTextField(_("Опис"))
    image = models.ImageField(_("Зображення"), upload_to="promos/")
    brand = models.ForeignKey(
        "catalog.Brand",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Бренд"),
    )
    date_start = models.DateField(_("Початок акції"), null=True, blank=True)
    date_end = models.DateField(_("Кінець акції"), null=True, blank=True)
    is_active = models.BooleanField(_("Активна"), default=True)

    class Meta:
        verbose_name = _("Акція")
        verbose_name_plural = _("Акції")
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
