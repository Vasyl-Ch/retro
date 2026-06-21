"""Auto-fill empty translations on SiteSettings to avoid blank EN fallbacks showing UK text."""

from django.conf import settings
from django.db.models.signals import pre_save
from django.dispatch import receiver
from modeltranslation.translator import NotRegistered, translator

from .models import SiteSettings


@receiver(pre_save, sender=SiteSettings)
def mirror_empty_translations(sender, instance: SiteSettings, **kwargs) -> None:
    try:
        opts = translator.get_options_for_model(sender)
    except NotRegistered:
        return

    languages = [code for code, _label in settings.LANGUAGES]
    for field_name in opts.fields:
        values = {lang: (getattr(instance, f"{field_name}_{lang}", None) or "").strip()
                  for lang in languages}
        donors = [v for v in values.values() if v]
        if not donors:
            continue
        fallback = donors[0]
        for lang, value in values.items():
            if not value:
                setattr(instance, f"{field_name}_{lang}", fallback)
