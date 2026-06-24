from modeltranslation.translator import TranslationOptions, register

from .models import Banner, News, Promo


@register(Banner)
class BannerTranslationOptions(TranslationOptions):
    fields = ("title", "subtitle", "button_text")


@register(News)
class NewsTranslationOptions(TranslationOptions):
    fields = ("title", "preview", "content")


@register(Promo)
class PromoTranslationOptions(TranslationOptions):
    fields = ("title", "description")
