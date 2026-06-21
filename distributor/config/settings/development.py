import os
from .base import *  # noqa: F401, F403

DEBUG = True

if os.environ.get("DB_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", "distributor"),
            "USER": os.environ.get("DB_USER", "postgres"),
            "PASSWORD": os.environ.get("DB_PASSWORD", "postgres"),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
        }
    }

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Allow CSRF (admin/login) over HTTPS tunnels (cloudflared / ngrok / localtunnel).
# Django 4.0+ supports a wildcard subdomain when a scheme is present.
CSRF_TRUSTED_ORIGINS = env_list(  # noqa: F405
    "CSRF_TRUSTED_ORIGINS",
    [
        "https://*.trycloudflare.com",
        "https://*.ngrok-free.app",
        "https://*.loca.lt",
    ],
)
