from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.core.validators import raster_image_validators


class Currency(models.TextChoices):
    UAH = "UAH", _("грн")
    USD = "USD", _("$")
    EUR = "EUR", _("€")


class Availability(models.TextChoices):
    IN_STOCK = "in_stock", _("В наявності")
    ON_ORDER = "on_order", _("Під замовлення")
    RESERVED = "reserved", _("Зарезервовано")
    SOLD = "sold", _("Продано")


class FuelType(models.TextChoices):
    PETROL = "petrol", _("Бензин")
    DIESEL = "diesel", _("Дизель")
    HYBRID = "hybrid", _("Гібрид")
    ELECTRIC = "electric", _("Електро")
    GAS = "gas", _("Газ / бензин")


class Transmission(models.TextChoices):
    MANUAL = "manual", _("Механіка")
    AUTOMATIC = "automatic", _("Автомат")
    ROBOT = "robot", _("Робот")
    CVT = "cvt", _("Варіатор")


class Condition(models.TextChoices):
    NEW = "new", _("Нове")
    USED = "used", _("Вживане")


class Brand(models.Model):
    name = models.CharField(_("Назва"), max_length=200)
    slug = models.SlugField("Slug", max_length=200, unique=True, blank=True)
    logo = models.ImageField(_("Логотип"), upload_to="brands/logos/", blank=True, null=True,
                             validators=raster_image_validators)
    description = models.TextField(_("Опис"), blank=True)
    website = models.URLField(_("Сайт бренду"), blank=True)
    is_active = models.BooleanField(_("Активний"), default=True)
    order = models.PositiveIntegerField(_("Порядок"), default=0)

    class Meta:
        verbose_name = _("Бренд")
        verbose_name_plural = _("Бренди")
        ordering = ["order", "name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("brands:brand_detail", kwargs={"slug": self.slug})


class Category(models.Model):
    name = models.CharField(_("Назва"), max_length=200)
    slug = models.SlugField("Slug", max_length=200, unique=True, blank=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
        verbose_name=_("Батьківська категорія"),
    )
    is_active = models.BooleanField(_("Активна"), default=True)

    class Meta:
        verbose_name = _("Категорія")
        verbose_name_plural = _("Категорії")

    def __str__(self) -> str:
        return f"{self.parent} → {self.name}" if self.parent else self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name=_("Бренд"),
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name=_("Категорія"),
    )
    name = models.CharField(_("Назва"), max_length=300)
    slug = models.SlugField("Slug", max_length=300, unique=True, blank=True)
    article = models.CharField(_("Артикул"), max_length=100, blank=True)
    description = models.TextField(_("Опис"), blank=True)
    image = models.ImageField(_("Фото"), upload_to="products/",
                              validators=raster_image_validators)

    # Універсальні комерційні поля (auto / shop / food).
    price = models.DecimalField(
        _("Ціна"), max_digits=12, decimal_places=2, null=True, blank=True
    )
    old_price = models.DecimalField(
        _("Стара ціна"), max_digits=12, decimal_places=2, null=True, blank=True,
        help_text=_("Заповніть, щоб показати знижку (закреслена стара ціна)."),
    )
    currency = models.CharField(
        _("Валюта"), max_length=3, choices=Currency.choices, default=Currency.UAH
    )
    availability = models.CharField(
        _("Наявність"), max_length=20, choices=Availability.choices,
        default=Availability.IN_STOCK,
    )
    location = models.CharField(_("Місто / локація"), max_length=120, blank=True)

    is_active = models.BooleanField(_("Активний"), default=True)
    is_featured = models.BooleanField(_("Рекомендований"), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveIntegerField(_("Порядок"), default=0)

    class Meta:
        verbose_name = _("Товар")
        verbose_name_plural = _("Товари")
        ordering = ["order", "name"]

    def __str__(self) -> str:
        return f"{self.brand} — {self.name}"

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("catalog:product_detail", kwargs={"slug": self.slug})

    @property
    def has_discount(self) -> bool:
        return bool(self.old_price and self.price and self.old_price > self.price)

    @property
    def vehicle_or_none(self):
        """Авто-характеристики або None — безпечний доступ до OneToOne у шаблонах."""
        try:
            return self.vehicle
        except ObjectDoesNotExist:
            return None


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("Товар"),
    )
    image = models.ImageField(_("Зображення"), upload_to="products/gallery/",
                              validators=raster_image_validators)
    order = models.PositiveIntegerField(_("Порядок"), default=0)

    class Meta:
        verbose_name = _("Фото товару")
        verbose_name_plural = _("Фото товарів")
        ordering = ["order"]

    def __str__(self) -> str:
        return f"Фото {self.product.name} #{self.order}"


class VehicleSpec(models.Model):
    """Авто-специфічні характеристики для пресета «Автосалон».

    Тримаємо окремо (OneToOne), щоб не засмічувати Product авто-колонками в інших
    вертикалях. В адмінці показується inline лише для пресета ``auto``.
    """

    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name="vehicle",
        verbose_name=_("Авто"),
    )
    year = models.PositiveIntegerField(_("Рік випуску"), null=True, blank=True)
    mileage = models.PositiveIntegerField(_("Пробіг, км"), null=True, blank=True)
    fuel_type = models.CharField(
        _("Тип палива"), max_length=20, choices=FuelType.choices, blank=True
    )
    transmission = models.CharField(
        _("Коробка передач"), max_length=20, choices=Transmission.choices, blank=True
    )
    engine_volume = models.DecimalField(
        _("Об'єм двигуна, л"), max_digits=4, decimal_places=1, null=True, blank=True
    )
    power = models.PositiveIntegerField(_("Потужність, к.с."), null=True, blank=True)
    color = models.CharField(_("Колір"), max_length=60, blank=True)
    condition = models.CharField(
        _("Стан"), max_length=10, choices=Condition.choices, default=Condition.USED
    )
    vin = models.CharField("VIN", max_length=17, blank=True)

    class Meta:
        verbose_name = _("Характеристики авто")
        verbose_name_plural = _("Характеристики авто")

    def __str__(self) -> str:
        return f"{self.product.name} — {self.get_condition_display()}"


class ProductSpec(models.Model):
    """Довільний параметр товару (key-value) — конфігуратор для будь-якої вертикалі."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="specs",
        verbose_name=_("Товар"),
    )
    label = models.CharField(_("Назва параметра"), max_length=120)
    value = models.CharField(_("Значення"), max_length=255)
    order = models.PositiveIntegerField(_("Порядок"), default=0)

    class Meta:
        verbose_name = _("Параметр")
        verbose_name_plural = _("Параметри")
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"{self.label}: {self.value}"
