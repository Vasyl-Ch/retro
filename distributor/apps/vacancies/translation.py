from modeltranslation.translator import TranslationOptions, register

from .models import Vacancy, VacancyImage


@register(Vacancy)
class VacancyTranslationOptions(TranslationOptions):
    fields = ("title", "city", "short_tagline", "description", "requirements", "conditions")


@register(VacancyImage)
class VacancyImageTranslationOptions(TranslationOptions):
    fields = ("caption",)
