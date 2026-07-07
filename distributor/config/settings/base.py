"""Shared settings for the distributor project."""

import os
from pathlib import Path

from django.utils.translation import gettext_lazy as _

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: list[str] | None = None) -> list[str]:
    raw = os.environ.get(name)
    if not raw:
        return default or []
    return [item.strip() for item in raw.split(",") if item.strip()]


SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-change-me")
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")

INSTALLED_APPS = [
    "modeltranslation",
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django_summernote",
    "solo",
    "colorfield",
    "apps.core",
    "apps.catalog",
    "apps.content",
    "apps.vacancies",
    "apps.contacts",
    "apps.orders",
]

# SAMEORIGIN (not the Django default DENY): the admin appearance constructor renders
# the site inside an <iframe> on the same origin for live preview.
X_FRAME_OPTIONS = "SAMEORIGIN"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.PresetAdminBrandingMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "apps.catalog.context_processors.global_nav",
                "apps.core.context_processors.page_background",
                "apps.core.context_processors.site_settings",
                "apps.orders.context_processors.cart_summary",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en"
LANGUAGES = [
    ("en", "English"),
    ("uk", "Українська"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]

MODELTRANSLATION_DEFAULT_LANGUAGE = "en"
MODELTRANSLATION_LANGUAGES = ("en", "uk")
MODELTRANSLATION_FALLBACK_LANGUAGES = ("en", "uk")
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

JAZZMIN_SETTINGS = {
    "site_title": _("Site management"),
    "site_header": _("Distributor"),
    "site_brand": _("Distributor"),
    "welcome_sign": _("Welcome to the control panel"),
    "copyright": _("Distributor LLC"),
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "auth.user": "fas fa-user",
        "auth.group": "fas fa-users",
        "catalog.brand": "fas fa-trademark",
        "catalog.category": "fas fa-tags",
        "catalog.product": "fas fa-box-open",
        "catalog.productimage": "fas fa-images",
        "content.banner": "fas fa-image",
        "content.news": "fas fa-newspaper",
        "content.promo": "fas fa-percent",
        "vacancies.vacancy": "fas fa-briefcase",
        "contacts.contactrequest": "fas fa-envelope",
        "orders.order": "fas fa-shopping-cart",
        "orders.orderitem": "fas fa-box",
        "core.pagebackground": "fas fa-image",
        "core.elementstyle": "fas fa-paint-brush",
        "core.sitesettings": "fas fa-sliders-h",
    },
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",
    "order_with_respect_to": [
        "catalog",
        "orders",
        "content",
        "vacancies",
        "contacts",
        "core",
        "auth",
    ],
}

JAZZMIN_UI_TWEAKS = {
    "navbar": "navbar-dark",
    "navbar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_fixed": True,
    "accent": "accent-primary",
    "sidebar_nav_child_indent": True,
}
