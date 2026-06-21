from decimal import Decimal

from django.contrib import messages
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.catalog.models import Product

from .cart import Cart
from .forms import CheckoutForm
from .models import OrderItem


def _is_ajax(request: HttpRequest) -> bool:
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def _cart_state(cart: Cart) -> dict:
    return {
        "count": len(cart),
        "total": f"{cart.total:.0f}",
        "currency": cart.currency_display,
    }


def _parse_qty(raw, default: int = 1) -> int:
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


@require_POST
def cart_add(request: HttpRequest, product_id: int) -> HttpResponse:
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart = Cart(request)
    cart.add(product.id, max(1, _parse_qty(request.POST.get("quantity"))))
    if _is_ajax(request):
        return JsonResponse({"ok": True, **_cart_state(cart)})
    return redirect("cart:detail")


@require_POST
def cart_update(request: HttpRequest, product_id: int) -> HttpResponse:
    cart = Cart(request)
    cart.set_quantity(product_id, _parse_qty(request.POST.get("quantity")))
    if _is_ajax(request):
        subtotal = next(
            (f"{row['subtotal']:.0f}" for row in cart if row["product"].id == product_id),
            None,
        )
        return JsonResponse({"ok": True, "item_subtotal": subtotal, **_cart_state(cart)})
    return redirect("cart:detail")


@require_POST
def cart_remove(request: HttpRequest, product_id: int) -> HttpResponse:
    cart = Cart(request)
    cart.remove(product_id)
    if _is_ajax(request):
        return JsonResponse({"ok": True, **_cart_state(cart)})
    return redirect("cart:detail")


def cart_detail(request: HttpRequest) -> HttpResponse:
    return render(
        request, "cart/detail.html", {"cart": Cart(request), "form": CheckoutForm()}
    )


@require_POST
def cart_checkout(request: HttpRequest) -> HttpResponse:
    cart = Cart(request)
    rows = list(cart)
    if not rows:
        messages.error(request, _("Кошик порожній."))
        return redirect("cart:detail")

    form = CheckoutForm(request.POST)
    if not form.is_valid():
        return render(request, "cart/detail.html", {"cart": cart, "form": form})

    order = form.save()
    OrderItem.objects.bulk_create(
        [
            OrderItem(
                order=order,
                product=row["product"],
                product_name=row["product"].name,
                price=row["product"].price or Decimal("0"),
                currency=row["product"].currency,
                quantity=row["quantity"],
            )
            for row in rows
        ]
    )
    cart.clear()
    messages.success(
        request,
        _("Дякуємо! Замовлення №%(id)s прийнято — ми зв’яжемося з вами.")
        % {"id": order.pk},
    )
    return redirect("cart:detail")
