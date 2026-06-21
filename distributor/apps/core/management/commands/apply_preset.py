"""Apply a built-in preset to SiteSettings.

Usage:
    python manage.py apply_preset distributor
    python manage.py apply_preset auto
    python manage.py apply_preset food
    python manage.py apply_preset generic
"""

from django.core.management.base import BaseCommand, CommandError

from apps.core.models import SiteSettings
from apps.core.presets import PRESETS, apply_preset


class Command(BaseCommand):
    help = "Apply one of the built-in site presets (distributor, auto, food, generic)."

    def add_arguments(self, parser):
        parser.add_argument("preset", choices=list(PRESETS), help="Preset name to apply")

    def handle(self, *args, **options):
        name = options["preset"]
        settings_obj = SiteSettings.get_solo()
        try:
            touched = apply_preset(settings_obj, name)
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(
            f"Applied preset '{name}'. Updated {len(touched)} fields."
        ))
