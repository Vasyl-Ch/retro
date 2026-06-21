from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.ProductListView.as_view(), name="product_list"),
    path("autocomplete/makes/", views.make_autocomplete, name="make_autocomplete"),
    path("autocomplete/cities/", views.city_autocomplete, name="city_autocomplete"),
    path("<slug:slug>/", views.ProductDetailView.as_view(), name="product_detail"),
]
