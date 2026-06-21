from typing import Any

from django.db.models import QuerySet
from django.http import HttpRequest, JsonResponse
from django.views.generic import DetailView, ListView

from .filters import PRODUCT_FILTER_SET, SORT_CHOICES
from .models import Brand, Category, Condition, FuelType, Product, Transmission


class BrandListView(ListView):
    model = Brand
    template_name = "catalog/brands.html"
    context_object_name = "brands"

    def get_queryset(self) -> QuerySet:
        return Brand.objects.filter(is_active=True)


class BrandDetailView(DetailView):
    model = Brand
    template_name = "catalog/brand_detail.html"

    def get_queryset(self) -> QuerySet:
        return Brand.objects.filter(is_active=True)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["products"] = self.object.products.filter(is_active=True).select_related(
            "category"
        )
        ctx["categories"] = Category.objects.filter(
            products__brand=self.object, is_active=True
        ).distinct()
        return ctx


class ProductListView(ListView):
    model = Product
    template_name = "catalog/products.html"
    context_object_name = "products"
    paginate_by = 16

    def get_queryset(self) -> QuerySet:
        qs = Product.objects.filter(is_active=True).select_related(
            "brand", "category", "vehicle"
        )
        qs = PRODUCT_FILTER_SET.filter(qs, self.request.GET)
        qs, _key = PRODUCT_FILTER_SET.sort(qs, self.request.GET)
        return qs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        params = self.request.GET
        ctx["brands"] = Brand.objects.filter(is_active=True)
        categories = Category.objects.filter(is_active=True)
        ctx["categories"] = categories
        ctx["category_chips"] = [(c.slug, c.name) for c in categories]
        ctx["fuel_choices"] = FuelType.choices
        ctx["transmission_choices"] = Transmission.choices
        ctx["condition_choices"] = Condition.choices
        ctx["sort_choices"] = SORT_CHOICES
        active = PRODUCT_FILTER_SET.active_values(params)
        ctx["filters"] = active
        ctx["has_active_filters"] = PRODUCT_FILTER_SET.has_active(params)
        # Назва обраної марки — щоб показати її у полі автокомпліту після перезавантаження.
        ctx["current_make"] = (
            Brand.objects.filter(slug__in=active.get("brand") or []).first()
        )
        return ctx


class ProductDetailView(DetailView):
    model = Product
    template_name = "catalog/product_detail.html"

    def get_queryset(self) -> QuerySet:
        return (
            Product.objects.filter(is_active=True)
            .select_related("brand", "category", "vehicle")
            .prefetch_related("specs", "images")
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["related"] = (
            Product.objects.filter(brand=self.object.brand, is_active=True)
            .exclude(pk=self.object.pk)
            .select_related("brand", "vehicle")[:4]
        )
        ctx["gallery"] = self.object.images.all()
        ctx["specs"] = self.object.specs.all()
        ctx["vehicle"] = self.object.vehicle_or_none
        return ctx


def _autocomplete_payload(items: list[dict[str, str]]) -> JsonResponse:
    return JsonResponse({"results": items})


def make_autocomplete(request: HttpRequest) -> JsonResponse:
    """JSON-підказки по марках (Brand) для поля пошуку — частковий збіг по назві."""
    query = (request.GET.get("q") or "").strip()
    qs = Brand.objects.filter(is_active=True)
    if query:
        qs = qs.filter(name__icontains=query)
    items = [{"name": b.name, "value": b.slug} for b in qs[:20]]
    return _autocomplete_payload(items)


def city_autocomplete(request: HttpRequest) -> JsonResponse:
    """JSON-підказки по містах (унікальні значення Product.location)."""
    query = (request.GET.get("q") or "").strip()
    qs = (
        Product.objects.filter(is_active=True)
        .exclude(location="")
        .values_list("location", flat=True)
    )
    if query:
        qs = qs.filter(location__icontains=query)
    cities = sorted(set(qs))[:20]
    items = [{"name": c, "value": c} for c in cities]
    return _autocomplete_payload(items)
