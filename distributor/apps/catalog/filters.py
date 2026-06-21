"""Стратегії фільтрації каталогу.

Кожен критерій пошуку — окрема стратегія (`QueryFilter`). Щоб додати новий фільтр,
достатньо додати об'єкт у ``PRODUCT_FILTER_SET`` — в'юху чіпати не треба (Open/Closed).
``ProductFilterSet`` композує стратегії та сортування і застосовує їх до queryset.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable

from django.db.models import F, Q, QuerySet
from django.http import QueryDict
from django.utils.translation import gettext_lazy as _


class QueryFilter(ABC):
    """Базова стратегія: застосовує себе до queryset за GET-параметрами."""

    @abstractmethod
    def apply(self, qs: QuerySet, params: QueryDict) -> QuerySet:
        ...

    def active_values(self, params: QueryDict) -> dict[str, Any]:
        """Поточний стан фільтра — для відновлення форми та збереження в querystring."""
        return {}


class SearchFilter(QueryFilter):
    """Текстовий пошук ``q`` по кількох полях (OR, icontains)."""

    param = "q"

    def __init__(self, fields: Iterable[str]) -> None:
        self.fields = list(fields)

    def apply(self, qs: QuerySet, params: QueryDict) -> QuerySet:
        query = (params.get(self.param) or "").strip()
        if not query:
            return qs
        cond = Q()
        for field in self.fields:
            cond |= Q(**{f"{field}__icontains": query})
        return qs.filter(cond).distinct()

    def active_values(self, params: QueryDict) -> dict[str, Any]:
        return {self.param: (params.get(self.param) or "").strip()}


class MultiValueFilter(QueryFilter):
    """Множинний вибір ``param=a&param=b`` → ``field__in=[a, b]``.

    Покриває марку/тип кузова (по slug) та choice-поля (паливо/КПП/стан).
    """

    def __init__(self, param: str, field: str) -> None:
        self.param = param
        self.field = field

    def _values(self, params: QueryDict) -> list[str]:
        return [v for v in params.getlist(self.param) if v]

    def apply(self, qs: QuerySet, params: QueryDict) -> QuerySet:
        values = self._values(params)
        return qs.filter(**{f"{self.field}__in": values}) if values else qs

    def active_values(self, params: QueryDict) -> dict[str, Any]:
        return {self.param: self._values(params)}


class RangeFilter(QueryFilter):
    """Діапазон ``{param}_min`` / ``{param}_max`` → ``field__gte`` / ``field__lte``."""

    def __init__(self, param: str, field: str) -> None:
        self.param = param
        self.field = field
        self.min_param = f"{param}_min"
        self.max_param = f"{param}_max"

    @staticmethod
    def _num(raw: str | None) -> float | int | None:
        raw = (raw or "").strip().replace(" ", "").replace(",", ".")
        if not raw:
            return None
        try:
            return float(raw) if "." in raw else int(raw)
        except ValueError:
            return None

    def apply(self, qs: QuerySet, params: QueryDict) -> QuerySet:
        low = self._num(params.get(self.min_param))
        high = self._num(params.get(self.max_param))
        if low is not None:
            qs = qs.filter(**{f"{self.field}__gte": low})
        if high is not None:
            qs = qs.filter(**{f"{self.field}__lte": high})
        return qs

    def active_values(self, params: QueryDict) -> dict[str, Any]:
        return {
            self.min_param: (params.get(self.min_param) or "").strip(),
            self.max_param: (params.get(self.max_param) or "").strip(),
        }


class IContainsFilter(QueryFilter):
    """Частковий збіг по одному полю (напр., місто/локація)."""

    def __init__(self, param: str, field: str) -> None:
        self.param = param
        self.field = field

    def apply(self, qs: QuerySet, params: QueryDict) -> QuerySet:
        value = (params.get(self.param) or "").strip()
        return qs.filter(**{f"{self.field}__icontains": value}) if value else qs

    def active_values(self, params: QueryDict) -> dict[str, Any]:
        return {self.param: (params.get(self.param) or "").strip()}


# Сортування: ключ ``sort`` → вираз для order_by (NULL-и завжди в кінці).
SORT_OPTIONS: dict[str, list] = {
    "price": [F("price").asc(nulls_last=True)],
    "-price": [F("price").desc(nulls_last=True)],
    "year": [F("vehicle__year").asc(nulls_last=True)],
    "-year": [F("vehicle__year").desc(nulls_last=True)],
    "mileage": [F("vehicle__mileage").asc(nulls_last=True)],
    "-mileage": [F("vehicle__mileage").desc(nulls_last=True)],
    "new": ["-created_at"],
}

# (ключ, мітка) для <select> сортування. Ключі мають збігатися з SORT_OPTIONS.
SORT_CHOICES: list[tuple[str, Any]] = [
    ("", _("За замовчуванням")),
    ("-price", _("Ціна: спочатку дорожчі")),
    ("price", _("Ціна: спочатку дешевші")),
    ("-year", _("Рік: новіші")),
    ("year", _("Рік: старіші")),
    ("mileage", _("Пробіг: менший")),
    ("new", _("Спочатку нові оголошення")),
]


class ProductFilterSet:
    """Композиція стратегій фільтрації + сортування."""

    def __init__(
        self,
        filters: Iterable[QueryFilter],
        sort_options: dict[str, list] | None = None,
    ) -> None:
        self.filters = list(filters)
        self.sort_options = sort_options if sort_options is not None else SORT_OPTIONS

    def filter(self, qs: QuerySet, params: QueryDict) -> QuerySet:
        for strategy in self.filters:
            qs = strategy.apply(qs, params)
        return qs

    def sort(self, qs: QuerySet, params: QueryDict) -> tuple[QuerySet, str]:
        key = (params.get("sort") or "").strip()
        fields = self.sort_options.get(key)
        if fields:
            qs = qs.order_by(*fields)
        return qs, key

    def active_values(self, params: QueryDict) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for strategy in self.filters:
            data.update(strategy.active_values(params))
        data["sort"] = (params.get("sort") or "").strip()
        return data

    def has_active(self, params: QueryDict) -> bool:
        for value in self.active_values(params).values():
            if value:
                return True
        return False


# Реєстр фільтрів каталогу. Додати критерій = додати рядок тут.
PRODUCT_FILTER_SET = ProductFilterSet(
    [
        SearchFilter(["name", "article", "brand__name", "vehicle__vin"]),
        MultiValueFilter("brand", "brand__slug"),
        MultiValueFilter("category", "category__slug"),
        MultiValueFilter("fuel", "vehicle__fuel_type"),
        MultiValueFilter("transmission", "vehicle__transmission"),
        MultiValueFilter("condition", "vehicle__condition"),
        RangeFilter("price", "price"),
        RangeFilter("year", "vehicle__year"),
        RangeFilter("mileage", "vehicle__mileage"),
        IContainsFilter("location", "location"),
    ]
)
