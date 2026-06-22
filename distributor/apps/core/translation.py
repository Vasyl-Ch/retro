"""Multilingual field registration for SiteSettings."""

from modeltranslation.translator import TranslationOptions, register

from .models import SiteSettings


@register(SiteSettings)
class SiteSettingsTranslationOptions(TranslationOptions):
    fields = (
        "tagline",
        "meta_description",
        "footer_copyright",
        "cta_label",
        "nav_catalog_label",
        "nav_brands_label",
        "nav_promos_label",
        "nav_news_label",
        "nav_vacancies_label",
        "nav_contacts_label",
        "term_product_singular",
        "term_product_plural",
        "term_brand_singular",
        "term_brand_plural",
        "term_category_singular",
        "term_category_plural",
        "vacancy_description_label",
        "vacancy_requirements_label",
        "vacancy_conditions_label",
        "vacancy_apply_label",
        "hero_eyebrow",
        "hero_title",
        "hero_subtitle",
    )
