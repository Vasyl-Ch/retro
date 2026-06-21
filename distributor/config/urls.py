from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("summernote/", include("django_summernote.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    path("robots.txt", robots_txt),
    path("", include("apps.content.urls", namespace="content")),
    path("catalog/", include("apps.catalog.urls", namespace="catalog")),
    path("cart/", include("apps.orders.urls", namespace="cart")),
    path("brands/", include("apps.catalog.brands_urls", namespace="brands")),
    path("vacancies/", include("apps.vacancies.urls", namespace="vacancies")),
    path("contact/", include("apps.contacts.urls", namespace="contacts")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
