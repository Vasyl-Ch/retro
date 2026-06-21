"""Експонує підсумок кошика для бейджа в навбарі (read-only, без створення сесії)."""

from __future__ import annotations

from typing import Any

from django.http import HttpRequest

from .cart import Cart


def cart_summary(request: HttpRequest) -> dict[str, Any]:
    cart = Cart(request)
    return {"cart_count": len(cart)}
