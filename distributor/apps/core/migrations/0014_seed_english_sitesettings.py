from django.db import migrations

TRANSLATED = [
    "tagline", "meta_description", "footer_copyright", "cta_label",
    "nav_catalog_label", "nav_brands_label", "nav_promos_label",
    "nav_news_label", "nav_vacancies_label", "nav_contacts_label",
    "term_product_singular", "term_product_plural",
    "term_brand_singular", "term_brand_plural",
    "term_category_singular", "term_category_plural",
    "vacancy_description_label", "vacancy_requirements_label",
    "vacancy_conditions_label", "vacancy_apply_label",
    "hero_eyebrow", "hero_title", "hero_subtitle",
]


def seed_english(apps, schema_editor):
    SiteSettings = apps.get_model("core", "SiteSettings")
    obj = SiteSettings.objects.first()
    if obj is None:
        return
    for name in TRANSLATED:
        en = getattr(obj, f"{name}_en", "") or ""
        uk = getattr(obj, f"{name}_uk", "") or ""
        base = getattr(obj, name, "") or ""
        # Existing data was authored under uk-default, so base == uk value.
        if not uk:
            uk = base
        if not en:
            field = SiteSettings._meta.get_field(f"{name}_en")
            en = field.default if field.has_default() and isinstance(field.default, str) else ""
        setattr(obj, f"{name}_uk", uk)
        setattr(obj, f"{name}_en", en)
        setattr(obj, name, en)  # base mirrors default language (en)
    obj.save()


class Migration(migrations.Migration):
    dependencies = [("core", "0013_remove_sitesettings_brand_name_en_and_more")]
    operations = [migrations.RunPython(seed_english, migrations.RunPython.noop)]
