from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.core.validators import raster_image_validators


class Currency(models.TextChoices):
    UAH = "UAH", _("UAH")
    USD = "USD", _("$")
    EUR = "EUR", _("€")


class Availability(models.TextChoices):
    IN_STOCK = "in_stock", _("In stock")
    ON_ORDER = "on_order", _("On order")
    RESERVED = "reserved", _("Reserved")
    SOLD = "sold", _("Sold")


class FuelType(models.TextChoices):
    PETROL = "petrol", _("Petrol")
    DIESEL = "diesel", _("Diesel")
    HYBRID = "hybrid", _("Hybrid")
    ELECTRIC = "electric", _("Electric")
    GAS = "gas", _("LPG / petrol")


class Transmission(models.TextChoices):
    MANUAL = "manual", _("Manual")
    AUTOMATIC = "automatic", _("Automatic")
    ROBOT = "robot", _("Automated (AMT)")
    CVT = "cvt", _("CVT")


class Condition(models.TextChoices):
    NEW = "new", _("New")
    USED = "used", _("Used")


class Brand(models.Model):
    name = models.CharField(_("Name"), max_length=200)
    slug = models.SlugField("Slug", max_length=200, unique=True, blank=True)
    logo = models.ImageField(_("Logo"), upload_to="brands/logos/", blank=True, null=True,
                             validators=raster_image_validators)
    description = models.TextField(_("Description"), blank=True)
    website = models.URLField(_("Brand website"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    order = models.PositiveIntegerField(_("Order"), default=0)

    class Meta:
        verbose_name = _("Brand")
        verbose_name_plural = _("Brands")
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
    name = models.CharField(_("Name"), max_length=200)
    slug = models.SlugField("Slug", max_length=200, unique=True, blank=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
        verbose_name=_("Parent category"),
    )
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

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
        verbose_name=_("Brand"),
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name=_("Category"),
    )
    name = models.CharField(_("Name"), max_length=300)
    slug = models.SlugField("Slug", max_length=300, unique=True, blank=True)
    article = models.CharField(_("SKU"), max_length=100, blank=True)
    description = models.TextField(_("Description"), blank=True)
    image = models.ImageField(_("Photo"), upload_to="products/",
                              validators=raster_image_validators)

    # Універсальні комерційні поля (auto / shop / food).
    price = models.DecimalField(
        _("Price"), max_digits=12, decimal_places=2, null=True, blank=True
    )
    old_price = models.DecimalField(
        _("Old price"), max_digits=12, decimal_places=2, null=True, blank=True,
        help_text=_("Fill in to show a discount (the old price is struck through)."),
    )
    currency = models.CharField(
        _("Currency"), max_length=3, choices=Currency.choices, default=Currency.UAH
    )
    availability = models.CharField(
        _("Availability"), max_length=20, choices=Availability.choices,
        default=Availability.IN_STOCK,
    )
    location = models.CharField(_("City / location"), max_length=120, blank=True)

    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    is_featured = models.BooleanField(_("Featured"), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveIntegerField(_("Order"), default=0)

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
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
        verbose_name=_("Product"),
    )
    image = models.ImageField(_("Image"), upload_to="products/gallery/",
                              validators=raster_image_validators)
    order = models.PositiveIntegerField(_("Order"), default=0)

    class Meta:
        verbose_name = _("Product photo")
        verbose_name_plural = _("Product photos")
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
        verbose_name=_("Vehicle"),
    )
    year = models.PositiveIntegerField(_("Year"), null=True, blank=True)
    mileage = models.PositiveIntegerField(_("Mileage, km"), null=True, blank=True)
    fuel_type = models.CharField(
        _("Fuel type"), max_length=20, choices=FuelType.choices, blank=True
    )
    transmission = models.CharField(
        _("Transmission"), max_length=20, choices=Transmission.choices, blank=True
    )
    engine_volume = models.DecimalField(
        _("Engine, L"), max_digits=4, decimal_places=1, null=True, blank=True
    )
    power = models.PositiveIntegerField(_("Power, hp"), null=True, blank=True)
    color = models.CharField(_("Color"), max_length=60, blank=True)
    condition = models.CharField(
        _("Condition"), max_length=10, choices=Condition.choices, default=Condition.USED
    )
    vin = models.CharField("VIN", max_length=17, blank=True)

    class Meta:
        verbose_name = _("Vehicle specs")
        verbose_name_plural = _("Vehicle specs")

    def __str__(self) -> str:
        return f"{self.product.name} — {self.get_condition_display()}"


class ProductSpec(models.Model):
    """Довільний параметр товару (key-value) — конфігуратор для будь-якої вертикалі."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="specs",
        verbose_name=_("Product"),
    )
    label = models.CharField(_("Parameter name"), max_length=120)
    value = models.CharField(_("Value"), max_length=255)
    order = models.PositiveIntegerField(_("Order"), default=0)

    class Meta:
        verbose_name = _("Parameter")
        verbose_name_plural = _("Parameters")
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"{self.label}: {self.value}"
