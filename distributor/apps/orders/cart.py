"""Сесійний кошик.

Інкапсулює всю логіку кошика (SRP): зберігає мапу ``{product_id: quantity}`` у сесії.
Читання (ітерація/лічильник/сума) НЕ створює сесію — запис у сесію роблять лише
мутуючі операції через :meth:`save`. Це уникає створення сесій для анонімних відвідувачів
лише через контекст-процесор.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Iterator

from apps.catalog.models import Product

SESSION_KEY = "cart"


class Cart:
    def __init__(self, request) -> None:
        self.session = request.session
        self.cart: dict[str, int] = self.session.get(SESSION_KEY, {})

    # --- мутації ---
    def add(self, product_id: int, quantity: int = 1, *, replace: bool = False) -> None:
        pid = str(product_id)
        current = self.cart.get(pid, 0)
        new_qty = quantity if replace else current + quantity
        if new_qty < 1:
            self.cart.pop(pid, None)
        else:
            self.cart[pid] = new_qty
        self.save()

    def set_quantity(self, product_id: int, quantity: int) -> None:
        pid = str(product_id)
        if quantity < 1:
            self.cart.pop(pid, None)
        elif pid in self.cart:
            self.cart[pid] = quantity
        self.save()

    def remove(self, product_id: int) -> None:
        self.cart.pop(str(product_id), None)
        self.save()

    def clear(self) -> None:
        self.cart = {}
        self.save()

    def save(self) -> None:
        self.session[SESSION_KEY] = self.cart
        self.session.modified = True

    # --- читання ---
    def _products(self) -> dict[int, Product]:
        ids = [int(pid) for pid in self.cart]
        qs = Product.objects.filter(id__in=ids, is_active=True).select_related("brand")
        return {p.id: p for p in qs}

    def __iter__(self) -> Iterator[dict]:
        products = self._products()
        for pid, qty in self.cart.items():
            product = products.get(int(pid))
            if product is None:  # товар деактивовано/видалено — пропускаємо
                continue
            price = product.price or Decimal("0")
            yield {"product": product, "quantity": qty, "subtotal": price * qty}

    def __len__(self) -> int:
        return sum(self.cart.values())

    @property
    def total(self) -> Decimal:
        return sum((row["subtotal"] for row in self), Decimal("0"))

    @property
    def currency_display(self) -> str:
        for row in self:
            return row["product"].get_currency_display()
        return ""
