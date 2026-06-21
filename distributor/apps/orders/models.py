from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.catalog.models import Currency, Product


class Order(models.Model):
    """Замовлення з кошика. Без онлайн-оплати — обробляється продавцем в адмінці."""

    class Status(models.TextChoices):
        NEW = "new", _("Нове")
        PROCESSING = "processing", _("В обробці")
        DONE = "done", _("Виконано")
        CANCELLED = "cancelled", _("Скасовано")

    name = models.CharField(_("Ім'я покупця"), max_length=200)
    phone = models.CharField(_("Телефон"), max_length=30, blank=True)
    email = models.EmailField(_("Email"), blank=True)
    comment = models.TextField(_("Коментар"), blank=True)
    status = models.CharField(
        _("Статус"), max_length=20, choices=Status.choices, default=Status.NEW
    )
    created_at = models.DateTimeField(_("Створено"), auto_now_add=True)

    class Meta:
        verbose_name = _("Замовлення")
        verbose_name_plural = _("Замовлення")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"#{self.pk} — {self.name}"

    @property
    def total(self) -> Decimal:
        return sum((item.subtotal for item in self.items.all()), Decimal("0"))

    @property
    def total_quantity(self) -> int:
        return sum(item.quantity for item in self.items.all())


class OrderItem(models.Model):
    """Позиція замовлення зі знімком назви та ціни (стабільна, навіть якщо товар змінять)."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items", verbose_name=_("Замовлення")
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        verbose_name=_("Товар"),
    )
    product_name = models.CharField(_("Назва (знімок)"), max_length=300)
    price = models.DecimalField(
        _("Ціна за од."), max_digits=12, decimal_places=2, default=Decimal("0")
    )
    currency = models.CharField(
        _("Валюта"), max_length=3, choices=Currency.choices, default=Currency.UAH
    )
    quantity = models.PositiveIntegerField(_("Кількість"), default=1)

    class Meta:
        verbose_name = _("Позиція замовлення")
        verbose_name_plural = _("Позиції замовлення")

    def __str__(self) -> str:
        return f"{self.product_name} × {self.quantity}"

    @property
    def subtotal(self) -> Decimal:
        return (self.price or Decimal("0")) * self.quantity
