"""Built-in site presets — Distributor / Auto / Restaurant / Generic.

Each preset is a dict mapping SiteSettings field names → translated values keyed by language.
`apply_preset` writes them into the singleton (both base + _uk + _en variants).
"""

from __future__ import annotations

from typing import Any

# Schema:
#   {field_name: {"uk": "<UA>", "en": "<EN>"}}
# Boolean / non-translated fields take a plain value (not a dict).


DISTRIBUTOR: dict[str, Any] = {
    "preset": "distributor",
    "theme": "classic",
    "home_layout": "editorial",
    "cart_enabled": False,
    "brand_name": {"uk": "Дистриб'ютор", "en": "Distributor"},
    "tagline": {
        "uk": "Офіційний представник провідних світових брендів",
        "en": "Official representative of leading global brands",
    },
    "cta_label": {"uk": "Зв'язатися", "en": "Contact us"},
    "footer_copyright": {
        "uk": "ТОВ «Дистриб'ютор». Усі права захищено.",
        "en": "Distributor LLC. All rights reserved.",
    },
    "nav_catalog_label": {"uk": "Каталог", "en": "Catalog"},
    "nav_brands_label": {"uk": "Бренди", "en": "Brands"},
    "nav_promos_label": {"uk": "Акції", "en": "Promotions"},
    "nav_news_label": {"uk": "Новини", "en": "News"},
    "nav_vacancies_label": {"uk": "Вакансії", "en": "Careers"},
    "nav_contacts_label": {"uk": "Контакти", "en": "Contacts"},
    "nav_catalog_visible": True,
    "nav_brands_visible": True,
    "nav_promos_visible": True,
    "nav_news_visible": True,
    "nav_vacancies_visible": True,
    "nav_contacts_visible": False,
    "term_product_singular": {"uk": "Товар", "en": "Product"},
    "term_product_plural": {"uk": "Товари", "en": "Products"},
    "term_brand_singular": {"uk": "Бренд", "en": "Brand"},
    "term_brand_plural": {"uk": "Бренди", "en": "Brands"},
    "term_category_singular": {"uk": "Категорія", "en": "Category"},
    "term_category_plural": {"uk": "Категорії", "en": "Categories"},
    "vacancy_description_label": {"uk": "Опис вакансії", "en": "Description"},
    "vacancy_requirements_label": {"uk": "Вимоги", "en": "Requirements"},
    "vacancy_conditions_label": {"uk": "Умови", "en": "Benefits"},
    "vacancy_apply_label": {"uk": "Відгукнутися на вакансію", "en": "Apply for this role"},
    "hero_eyebrow": {"uk": "Офіційний дистриб'ютор · 2026", "en": "Official Distributor · 2026"},
    "hero_title": {
        "uk": "Інша **відстань** до якісних брендів.",
        "en": "A shorter **distance** to quality brands.",
    },
    "hero_subtitle": {
        "uk": "Каталог, який доносить продукт без зайвого шуму. Запит на зв'язок — у два кліки.",
        "en": "A catalog that delivers product without the noise. Get in touch in two clicks.",
    },
}


AUTO: dict[str, Any] = {
    "preset": "auto",
    "theme": "darklux",
    "home_layout": "editorial",
    "cart_enabled": False,
    "brand_name": {"uk": "Автосалон", "en": "Auto Gallery"},
    "tagline": {
        "uk": "Преміальний автопарк. Тест-драйв у зручний для вас час.",
        "en": "Premium fleet. Schedule a test drive at your convenience.",
    },
    "cta_label": {"uk": "Записатися на огляд", "en": "Book a viewing"},
    "footer_copyright": {
        "uk": "Автосалон. Усі права захищено.",
        "en": "Auto Gallery. All rights reserved.",
    },
    "nav_catalog_label": {"uk": "Автопарк", "en": "Fleet"},
    "nav_brands_label": {"uk": "Марки", "en": "Makes"},
    "nav_promos_label": {"uk": "Спецпропозиції", "en": "Special Offers"},
    "nav_news_label": {"uk": "Новини", "en": "News"},
    "nav_vacancies_label": {"uk": "Тест-драйв", "en": "Test Drive"},
    "nav_contacts_label": {"uk": "Контакти", "en": "Contacts"},
    "nav_catalog_visible": True,
    "nav_brands_visible": True,
    "nav_promos_visible": True,
    "nav_news_visible": True,
    "nav_vacancies_visible": True,
    "nav_contacts_visible": True,
    "term_product_singular": {"uk": "Авто", "en": "Vehicle"},
    "term_product_plural": {"uk": "Авто", "en": "Vehicles"},
    "term_brand_singular": {"uk": "Марка", "en": "Make"},
    "term_brand_plural": {"uk": "Марки", "en": "Makes"},
    "term_category_singular": {"uk": "Тип кузова", "en": "Body Style"},
    "term_category_plural": {"uk": "Типи кузова", "en": "Body Styles"},
    "vacancy_description_label": {"uk": "Огляд авто", "en": "Vehicle Overview"},
    "vacancy_requirements_label": {"uk": "Характеристики", "en": "Specifications"},
    "vacancy_conditions_label": {"uk": "Комплектація", "en": "Equipment"},
    "vacancy_apply_label": {"uk": "Запитати про авто", "en": "Inquire about this car"},
    "hero_eyebrow": {"uk": "Автосалон · Тест-драйви", "en": "Auto Gallery · Test Drives"},
    "hero_title": {
        "uk": "Знайдіть **свою** машину без поспіху.",
        "en": "Find **your** car without the rush.",
    },
    "hero_subtitle": {
        "uk": "Прозорі ціни, чесні характеристики, особистий менеджер на кожне авто.",
        "en": "Transparent prices, honest specs, a dedicated manager for every car.",
    },
}


RESTAURANT: dict[str, Any] = {
    "preset": "food",
    "theme": "nude",
    "home_layout": "editorial",
    "cart_enabled": False,
    "brand_name": {"uk": "Ресторан", "en": "Restaurant"},
    "tagline": {
        "uk": "Свіжі інгредієнти. Прості рецепти. Затишна атмосфера.",
        "en": "Fresh ingredients. Simple recipes. A space to slow down.",
    },
    "cta_label": {"uk": "Забронювати стіл", "en": "Reserve a table"},
    "footer_copyright": {
        "uk": "Ресторан. Усі права захищено.",
        "en": "Restaurant. All rights reserved.",
    },
    "nav_catalog_label": {"uk": "Меню", "en": "Menu"},
    "nav_brands_label": {"uk": "Кухня", "en": "Cuisine"},
    "nav_promos_label": {"uk": "Спецпропозиції", "en": "Specials"},
    "nav_news_label": {"uk": "Події", "en": "Events"},
    "nav_vacancies_label": {"uk": "Команда", "en": "Team"},
    "nav_contacts_label": {"uk": "Адреса", "en": "Visit us"},
    "nav_catalog_visible": True,
    "nav_brands_visible": False,
    "nav_promos_visible": True,
    "nav_news_visible": True,
    "nav_vacancies_visible": False,
    "nav_contacts_visible": True,
    "term_product_singular": {"uk": "Страва", "en": "Dish"},
    "term_product_plural": {"uk": "Страви", "en": "Dishes"},
    "term_brand_singular": {"uk": "Кухня", "en": "Cuisine"},
    "term_brand_plural": {"uk": "Кухні", "en": "Cuisines"},
    "term_category_singular": {"uk": "Розділ меню", "en": "Menu Section"},
    "term_category_plural": {"uk": "Розділи меню", "en": "Menu Sections"},
    "vacancy_description_label": {"uk": "Про вакансію", "en": "About the role"},
    "vacancy_requirements_label": {"uk": "Хто потрібен", "en": "Who we're looking for"},
    "vacancy_conditions_label": {"uk": "Що пропонуємо", "en": "What we offer"},
    "vacancy_apply_label": {"uk": "Приєднатися до команди", "en": "Join the team"},
    "hero_eyebrow": {"uk": "Ресторан · Авторська кухня", "en": "Restaurant · Chef's kitchen"},
    "hero_title": {
        "uk": "Прості страви, що **запам'ятовуються**.",
        "en": "Simple dishes that **stay with you**.",
    },
    "hero_subtitle": {
        "uk": "Сезонне меню змінюється щомісяця. Бронь столу — за один дотик.",
        "en": "Seasonal menu, refreshed monthly. Reserve your table in one tap.",
    },
}


GENERIC: dict[str, Any] = {
    "preset": "generic",
    "theme": "classic",
    "home_layout": "editorial",
    "cart_enabled": False,
    "brand_name": {"uk": "Бренд", "en": "Brand"},
    "tagline": {"uk": "Опис компанії одним рядком.", "en": "Company tagline in a single line."},
    "cta_label": {"uk": "Зв'язатися", "en": "Contact us"},
    "footer_copyright": {"uk": "Компанія. Усі права захищено.", "en": "Company. All rights reserved."},
    "nav_catalog_label": {"uk": "Каталог", "en": "Catalog"},
    "nav_brands_label": {"uk": "Бренди", "en": "Brands"},
    "nav_promos_label": {"uk": "Акції", "en": "Promotions"},
    "nav_news_label": {"uk": "Новини", "en": "News"},
    "nav_vacancies_label": {"uk": "Вакансії", "en": "Careers"},
    "nav_contacts_label": {"uk": "Контакти", "en": "Contacts"},
    "nav_catalog_visible": True,
    "nav_brands_visible": False,
    "nav_promos_visible": False,
    "nav_news_visible": True,
    "nav_vacancies_visible": False,
    "nav_contacts_visible": True,
    "term_product_singular": {"uk": "Товар", "en": "Item"},
    "term_product_plural": {"uk": "Товари", "en": "Items"},
    "term_brand_singular": {"uk": "Бренд", "en": "Brand"},
    "term_brand_plural": {"uk": "Бренди", "en": "Brands"},
    "term_category_singular": {"uk": "Категорія", "en": "Category"},
    "term_category_plural": {"uk": "Категорії", "en": "Categories"},
    "vacancy_description_label": {"uk": "Опис", "en": "Description"},
    "vacancy_requirements_label": {"uk": "Вимоги", "en": "Requirements"},
    "vacancy_conditions_label": {"uk": "Умови", "en": "Conditions"},
    "vacancy_apply_label": {"uk": "Відгукнутися", "en": "Apply"},
    "hero_eyebrow": {"uk": "Компанія · 2026", "en": "Company · 2026"},
    "hero_title": {
        "uk": "Опис ключової **переваги** одним реченням.",
        "en": "Your key **value** in one sentence.",
    },
    "hero_subtitle": {
        "uk": "Підпідзаголовок з конкретикою. Прибирати або редагувати в адмінці.",
        "en": "Subheading with concrete detail. Edit or remove in the admin.",
    },
}


SHOP: dict[str, Any] = {
    "preset": "shop",
    "theme": "classic",
    "home_layout": "editorial",
    "cart_enabled": True,
    "brand_name": {"uk": "Майстерня 3D-друку", "en": "3D Print Studio"},
    "tagline": {
        "uk": "Готові вироби та друк на замовлення.",
        "en": "Ready-made items and custom prints.",
    },
    "cta_label": {"uk": "Замовити", "en": "Order"},
    "footer_copyright": {
        "uk": "Магазин. Усі права захищено.",
        "en": "Shop. All rights reserved.",
    },
    "nav_catalog_label": {"uk": "Товари", "en": "Products"},
    "nav_brands_label": {"uk": "Матеріали", "en": "Materials"},
    "nav_promos_label": {"uk": "Знижки", "en": "Deals"},
    "nav_news_label": {"uk": "Новини", "en": "News"},
    "nav_vacancies_label": {"uk": "Команда", "en": "Team"},
    "nav_contacts_label": {"uk": "Контакти", "en": "Contacts"},
    "nav_catalog_visible": True,
    "nav_brands_visible": False,
    "nav_promos_visible": True,
    "nav_news_visible": False,
    "nav_vacancies_visible": False,
    "nav_contacts_visible": True,
    "term_product_singular": {"uk": "Товар", "en": "Product"},
    "term_product_plural": {"uk": "Товари", "en": "Products"},
    "term_brand_singular": {"uk": "Матеріал", "en": "Material"},
    "term_brand_plural": {"uk": "Матеріали", "en": "Materials"},
    "term_category_singular": {"uk": "Категорія", "en": "Category"},
    "term_category_plural": {"uk": "Категорії", "en": "Categories"},
    "vacancy_description_label": {"uk": "Опис", "en": "Description"},
    "vacancy_requirements_label": {"uk": "Вимоги", "en": "Requirements"},
    "vacancy_conditions_label": {"uk": "Умови", "en": "Conditions"},
    "vacancy_apply_label": {"uk": "Відгукнутися", "en": "Apply"},
    "hero_eyebrow": {"uk": "Магазин · 3D-друк", "en": "Shop · 3D printing"},
    "hero_title": {
        "uk": "Друкуємо **ідеї** у деталях.",
        "en": "We print **ideas** in detail.",
    },
    "hero_subtitle": {
        "uk": "Каталог готових виробів і друк на замовлення. Додайте в кошик — ми зв'яжемося.",
        "en": "Ready-made items and custom prints. Add to cart — we'll get in touch.",
    },
}


PRESETS: dict[str, dict[str, Any]] = {
    "distributor": DISTRIBUTOR,
    "auto": AUTO,
    "food": RESTAURANT,
    "shop": SHOP,
    "generic": GENERIC,
}


def apply_preset(settings_obj, preset_name: str) -> list[str]:
    """Overwrite SiteSettings fields with values from the preset.

    Returns the list of fields actually written, for logging/feedback.
    """
    data = PRESETS.get(preset_name)
    if not data:
        raise ValueError(f"Unknown preset: {preset_name}. Choices: {list(PRESETS)}")

    touched: list[str] = []
    for field, value in data.items():
        if isinstance(value, dict):
            # Translated field — write base + each language variant.
            uk = value.get("uk", "")
            en = value.get("en", uk)
            setattr(settings_obj, field, uk)
            setattr(settings_obj, f"{field}_uk", uk)
            setattr(settings_obj, f"{field}_en", en)
            touched.append(field)
        else:
            setattr(settings_obj, field, value)
            touched.append(field)
    settings_obj.save()
    return touched
