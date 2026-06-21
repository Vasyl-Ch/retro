from typing import Any

from django.http import HttpRequest

from .models import Category


def global_nav(request: HttpRequest) -> dict[str, Any]:
    return {
        "nav_categories": Category.objects.filter(is_active=True, parent=None)
        .prefetch_related("children")
        .order_by("name"),
    }
