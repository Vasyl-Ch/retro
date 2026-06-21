from django.urls import path
from . import views

app_name = "content"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("news/", views.NewsListView.as_view(), name="news_list"),
    path("news/<slug:slug>/", views.NewsDetailView.as_view(), name="news_detail"),
    path("promos/", views.PromoListView.as_view(), name="promo_list"),
    path("promos/<slug:slug>/", views.PromoDetailView.as_view(), name="promo_detail"),
]
