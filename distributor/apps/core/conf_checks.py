"""Production configuration guards (fail fast on insecure defaults)."""

from django.core.exceptions import ImproperlyConfigured

INSECURE_SECRET_KEY = "django-insecure-change-me"


def assert_production_secret(secret_key: str | None) -> None:
    """Raise if SECRET_KEY is missing or still the insecure development default."""
    if (
        not secret_key
        or secret_key == INSECURE_SECRET_KEY
        or secret_key.startswith("django-insecure-")
    ):
        raise ImproperlyConfigured(
            "SECRET_KEY must be set to a unique secret value in production "
            "(the insecure development default is not allowed)."
        )


def assert_allowed_hosts(allowed_hosts: list[str]) -> None:
    """Raise if ALLOWED_HOSTS is empty (every host would be rejected with 400)."""
    if not allowed_hosts:
        raise ImproperlyConfigured(
            "ALLOWED_HOSTS must be set in production (received an empty list)."
        )
