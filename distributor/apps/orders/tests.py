from decimal import Decimal
from importlib import import_module

from django.conf import settings
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.catalog.models import Brand, Product

from .cart import Cart
from .models import Order


def _request_with_session():
    request = RequestFactory().get("/")
    engine = import_module(settings.SESSION_ENGINE)
    request.session = engine.SessionStore()
    return request


class CartUnitTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.brand = Brand.objects.create(name="B", slug="b")
        cls.p1 = Product.objects.create(brand=cls.brand, name="P1", slug="p1", price=Decimal("100"))
        cls.p2 = Product.objects.create(brand=cls.brand, name="P2", slug="p2", price=Decimal("50"))

    def test_add_accumulates_and_counts(self):
        cart = Cart(_request_with_session())
        cart.add(self.p1.id, 1)
        cart.add(self.p1.id, 2)
        cart.add(self.p2.id, 1)
        self.assertEqual(len(cart), 4)
        self.assertEqual(cart.total, Decimal("350"))

    def test_set_quantity_and_remove(self):
        cart = Cart(_request_with_session())
        cart.add(self.p1.id, 3)
        cart.set_quantity(self.p1.id, 1)
        self.assertEqual(len(cart), 1)
        cart.set_quantity(self.p1.id, 0)  # 0 → видаляє
        self.assertEqual(len(cart), 0)

    def test_inactive_product_skipped_in_iteration(self):
        cart = Cart(_request_with_session())
        cart.add(self.p1.id, 1)
        self.p1.is_active = False
        self.p1.save(update_fields=["is_active"])
        self.assertEqual(list(cart), [])
        self.assertEqual(cart.total, Decimal("0"))

    def test_empty_cart_does_not_write_session(self):
        request = _request_with_session()
        Cart(request)  # лише читання
        self.assertNotIn("cart", request.session)


class CartViewTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.brand = Brand.objects.create(name="B", slug="b")
        cls.p1 = Product.objects.create(brand=cls.brand, name="P1", slug="p1", price=Decimal("100"))
        cls.p2 = Product.objects.create(brand=cls.brand, name="P2", slug="p2", price=Decimal("50"))

    def _add(self, product, qty=1):
        return self.client.post(
            reverse("cart:add", args=[product.id]),
            {"quantity": qty},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

    def test_add_ajax_returns_count(self):
        r = self._add(self.p1, 2)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["count"], 2)

    def test_update_quantity(self):
        self._add(self.p1, 1)
        r = self.client.post(
            reverse("cart:update", args=[self.p1.id]),
            {"quantity": 5},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(r.json()["count"], 5)
        self.assertEqual(r.json()["item_subtotal"], "500")

    def test_remove(self):
        self._add(self.p1, 1)
        r = self.client.post(
            reverse("cart:remove", args=[self.p1.id]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(r.json()["count"], 0)

    def test_checkout_creates_order_and_clears_cart(self):
        self._add(self.p1, 2)
        self._add(self.p2, 1)
        r = self.client.post(
            reverse("cart:checkout"),
            {"name": "Іван", "phone": "+380501112233", "email": "", "comment": "швидше"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.get()
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.total, Decimal("250"))
        self.assertEqual(order.items.first().product_name, "P1")  # знімок назви
        # кошик очищено
        detail = self.client.get(reverse("cart:detail"))
        self.assertEqual(len(detail.context["cart"]), 0)

    def test_checkout_requires_contact_method(self):
        self._add(self.p1, 1)
        r = self.client.post(
            reverse("cart:checkout"),
            {"name": "Іван", "phone": "", "email": "", "comment": ""},
        )
        self.assertEqual(r.status_code, 200)  # форма повернулась з помилкою
        self.assertEqual(Order.objects.count(), 0)

    def test_checkout_empty_cart_redirects(self):
        r = self.client.post(
            reverse("cart:checkout"), {"name": "Іван", "phone": "+380501112233"}
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Order.objects.count(), 0)
