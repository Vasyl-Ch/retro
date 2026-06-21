from typing import Any

from django.db.models import Q, QuerySet
from django.utils import timezone
from django.views.generic import DetailView, ListView, TemplateView

from apps.catalog.models import Brand, Product

from .models import Banner, News, Promo


class HomeView(TemplateView):
    template_name = "content/home.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        today = timezone.now().date()
        ctx["banners"] = Banner.objects.filter(is_active=True)
        ctx["brands"] = Brand.objects.filter(is_active=True)
        ctx["featured"] = Product.objects.filter(
            is_active=True, is_featured=True
        ).select_related("brand", "category")[:8]
        ctx["latest_news"] = News.objects.filter(is_active=True)[:3]
        ctx["active_promos"] = (
            Promo.objects.filter(is_active=True)
            .filter(Q(date_end__isnull=True) | Q(date_end__gte=today))
            .select_related("brand")[:4]
        )
        return ctx


class NewsListView(ListView):
    model = News
    template_name = "content/news_list.html"
    context_object_name = "news_list"
    paginate_by = 9

    def get_queryset(self) -> QuerySet:
        return News.objects.filter(is_active=True)


class NewsDetailView(DetailView):
    model = News
    template_name = "content/news_detail.html"

    def get_queryset(self) -> QuerySet:
        return News.objects.filter(is_active=True)


class PromoListView(ListView):
    model = Promo
    template_name = "content/promo_list.html"
    context_object_name = "promos"

    def get_queryset(self) -> QuerySet:
        today = timezone.now().date()
        return (
            Promo.objects.filter(is_active=True)
            .filter(Q(date_end__isnull=True) | Q(date_end__gte=today))
            .select_related("brand")
        )


class PromoDetailView(DetailView):
    model = Promo
    template_name = "content/promo_detail.html"

    def get_queryset(self) -> QuerySet:
        return Promo.objects.filter(is_active=True)
