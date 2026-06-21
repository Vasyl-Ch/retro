from django.db import models
from django.utils.translation import gettext_lazy as _
from solo.models import SingletonModel

from apps.core.validators import branding_image_validators, raster_image_validators


class SiteSettings(SingletonModel):
    """Глобальні налаштування сайту (singleton) — лейбли, тема, видимість блоків."""

    PRESET_DISTRIBUTOR = "distributor"
    PRESET_AUTO = "auto"
    PRESET_FOOD = "food"
    PRESET_SHOP = "shop"
    PRESET_GENERIC = "generic"
    PRESET_CHOICES = [
        (PRESET_DISTRIBUTOR, _("Дистриб'ютор")),
        (PRESET_AUTO, _("Автосалон")),
        (PRESET_FOOD, _("Їжа / ресторан")),
        (PRESET_SHOP, _("Магазин (кошик)")),
        (PRESET_GENERIC, _("Універсальний лендінг")),
    ]

    THEME_CLASSIC = "classic"
    THEME_CYBERPUNK = "cyberpunk"
    THEME_NUDE = "nude"
    THEME_DARKLUX = "darklux"
    THEME_CHOICES = [
        (THEME_CLASSIC, _("Classic (світло-синя)")),
        (THEME_CYBERPUNK, _("Cyberpunk (неон)")),
        (THEME_NUDE, _("Nude (пастель)")),
        (THEME_DARKLUX, _("Dark Lux (преміум темна)")),
    ]

    preset = models.CharField(
        _("Пресет (вертикаль)"),
        max_length=20,
        choices=PRESET_CHOICES,
        default=PRESET_DISTRIBUTOR,
        help_text=_("Тип сайту. Використовується командою apply_preset для заповнення дефолтів."),
    )
    theme = models.CharField(
        _("Тема"),
        max_length=20,
        choices=THEME_CHOICES,
        default=THEME_CLASSIC,
    )

    BRAND_STYLE_PLAIN = "plain"
    BRAND_STYLE_GRADIENT = "gradient"
    BRAND_STYLE_UNDERLINE = "underline"
    BRAND_STYLE_SCRIPT = "script"
    BRAND_STYLE_CHOICES = [
        (BRAND_STYLE_PLAIN, _("Звичайний")),
        (BRAND_STYLE_GRADIENT, _("Градієнт")),
        (BRAND_STYLE_UNDERLINE, _("З підкресленням")),
        (BRAND_STYLE_SCRIPT, _("Розписний (курсив)")),
    ]

    brand_name = models.CharField(_("Назва сайту"), max_length=120, default="Дистриб'ютор")
    brand_style = models.CharField(
        _("Стиль назви сайту"),
        max_length=20,
        choices=BRAND_STYLE_CHOICES,
        default=BRAND_STYLE_PLAIN,
        help_text=_("Оформлення тексту назви в шапці/футері."),
    )
    tagline = models.CharField(_("Слоган"), max_length=300, blank=True)
    brand_logo = models.ImageField(_("Логотип"), upload_to="branding/", blank=True, null=True,
                                   validators=branding_image_validators)
    favicon = models.ImageField(_("Favicon"), upload_to="branding/", blank=True, null=True,
                                validators=branding_image_validators)
    meta_description = models.CharField(_("SEO-опис (за замовчуванням)"), max_length=300, blank=True)
    footer_copyright = models.CharField(_("Копірайт у футері"), max_length=200, blank=True)
    cta_label = models.CharField(_("Текст кнопки CTA"), max_length=80, default="Зв’язатись")

    cart_enabled = models.BooleanField(
        _("Кошик (режим магазину)"),
        default=False,
        help_text=_(
            "Показувати ціни, кнопки «У кошик» і сторінку кошика. "
            "Вмикається пресетом «Магазин». Замовлення надходять у розділ «Замовлення»."
        ),
    )

    contact_phone = models.CharField(_("Контактний телефон"), max_length=40, blank=True)
    contact_email = models.EmailField(_("Контактний email"), blank=True)
    contact_address = models.CharField(_("Адреса"), max_length=200, blank=True)

    side_logo_left = models.ImageField(
        _("Бокове лого (ліворуч)"), upload_to="branding/", blank=True, null=True,
        validators=branding_image_validators,
        help_text=_(
            "На широких екранах — закріплене ліворуч (тримається при прокручуванні). "
            "На смартфоні — внизу перед футером."
        ),
    )
    side_logo_right = models.ImageField(
        _("Бокове лого (праворуч)"), upload_to="branding/", blank=True, null=True,
        validators=branding_image_validators,
        help_text=_("Те саме, але праворуч / друге лого внизу на смартфоні."),
    )
    SIDE_LOGO_SM = "sm"
    SIDE_LOGO_MD = "md"
    SIDE_LOGO_LG = "lg"
    SIDE_LOGO_SIZE_CHOICES = [
        (SIDE_LOGO_SM, _("Маленький")),
        (SIDE_LOGO_MD, _("Середній")),
        (SIDE_LOGO_LG, _("Великий")),
    ]
    side_logo_size = models.CharField(
        _("Розмір бокових лого"),
        max_length=2,
        choices=SIDE_LOGO_SIZE_CHOICES,
        default=SIDE_LOGO_MD,
        help_text=_(
            "Розмір бокових лого. На широких екранах — ширина закріплених лого "
            "(обмежена бічним полем, щоб не перекривати контент); на смартфоні — висота "
            "лого в ряду внизу."
        ),
    )

    nav_catalog_label = models.CharField(_("Меню: Каталог — назва"), max_length=80, default="Каталог")
    nav_catalog_visible = models.BooleanField(_("Меню: Каталог — показувати"), default=True)
    nav_brands_label = models.CharField(_("Меню: Бренди — назва"), max_length=80, default="Бренди")
    nav_brands_visible = models.BooleanField(_("Меню: Бренди — показувати"), default=True)
    nav_promos_label = models.CharField(_("Меню: Акції — назва"), max_length=80, default="Акції")
    nav_promos_visible = models.BooleanField(_("Меню: Акції — показувати"), default=True)
    nav_news_label = models.CharField(_("Меню: Новини — назва"), max_length=80, default="Новини")
    nav_news_visible = models.BooleanField(_("Меню: Новини — показувати"), default=True)
    nav_vacancies_label = models.CharField(_("Меню: Вакансії — назва"), max_length=80, default="Вакансії")
    nav_vacancies_visible = models.BooleanField(_("Меню: Вакансії — показувати"), default=True)
    nav_contacts_label = models.CharField(_("Меню: Контакти — назва"), max_length=80, default="Контакти")
    nav_contacts_visible = models.BooleanField(_("Меню: Контакти — показувати"), default=False)

    term_product_singular = models.CharField(_("Термін: товар (однина)"), max_length=80, default="Товар")
    term_product_plural = models.CharField(_("Термін: товари (множина)"), max_length=80, default="Товари")
    term_brand_singular = models.CharField(_("Термін: бренд (однина)"), max_length=80, default="Бренд")
    term_brand_plural = models.CharField(_("Термін: бренди (множина)"), max_length=80, default="Бренди")
    term_category_singular = models.CharField(_("Термін: категорія (однина)"), max_length=80, default="Категорія")
    term_category_plural = models.CharField(_("Термін: категорії (множина)"), max_length=80, default="Категорії")

    LAYOUT_CLASSIC = "classic"
    LAYOUT_EDITORIAL = "editorial"
    LAYOUT_CINEMATIC = "cinematic"
    LAYOUT_CHOICES = [
        (LAYOUT_CLASSIC, _("Classic (текуща)")),
        (LAYOUT_EDITORIAL, _("Editorial (журнальний — великий типографічний hero)")),
        (LAYOUT_CINEMATIC, _("Cinematic (повноекранний hero з відео/фото)")),
    ]
    home_layout = models.CharField(
        _("Макет головної"),
        max_length=20,
        choices=LAYOUT_CHOICES,
        default=LAYOUT_EDITORIAL,
        help_text=_("Стиль hero-секції на головній сторінці."),
    )

    vacancy_description_label = models.CharField(
        _("Вакансія: заголовок секції \"Опис\""), max_length=80, default="Опис")
    vacancy_requirements_label = models.CharField(
        _("Вакансія: заголовок секції \"Вимоги\""), max_length=80, default="Вимоги")
    vacancy_conditions_label = models.CharField(
        _("Вакансія: заголовок секції \"Умови\""), max_length=80, default="Умови")
    vacancy_apply_label = models.CharField(
        _("Вакансія: текст кнопки відгуку"), max_length=80, default="Відгукнутися")

    hero_eyebrow = models.CharField(_("Hero: верхня плашка"), max_length=80, blank=True,
                                    help_text=_("Малий текст над великим заголовком (напр., \"Офіційний дистриб'ютор · 2026\")."))
    hero_title = models.CharField(_("Hero: великий заголовок"), max_length=200, blank=True,
                                  help_text=_("Замінює дефолтний. Для kinetic-ефекту можна підкреслити слово через **слово**."))
    hero_subtitle = models.CharField(_("Hero: підзаголовок"), max_length=400, blank=True)

    anim_page_transitions = models.BooleanField(
        _("Анімація: плавні переходи між сторінками"), default=True,
        help_text=_("View Transitions API. Працює в Chrome/Edge/Safari; у Firefox без анімації."),
    )
    anim_scroll_reveal = models.BooleanField(
        _("Анімація: появи блоків при прокручуванні (fade-up + stagger)"), default=True,
    )
    anim_magnetic_buttons = models.BooleanField(
        _("Анімація: \"магнітні\" кнопки на hover"), default=True,
        help_text=_("Вимикається на тач-пристроях автоматично."),
    )
    anim_cursor_follower = models.BooleanField(
        _("Анімація: кастомний кругляк-курсор"), default=False,
        help_text=_("Сильний ефект; не для всіх брендів. Вимикається на тач-пристроях автоматично."),
    )
    anim_kinetic_hero = models.BooleanField(
        _("Анімація: \"кінетичне\" появлення hero-заголовка"), default=True,
    )

    class Meta:
        verbose_name = _("Налаштування сайту")
        verbose_name_plural = _("Налаштування сайту")

    def __str__(self) -> str:
        return str(self._meta.verbose_name)


class PageBackground(models.Model):
    """Фонове зображення сайту або конкретної сторінки.

    Запис з ``page_key = "site"`` діє як фон за замовчуванням для всіх сторінок;
    інші записи перевизначають фон для конкретної сторінки (url name).
    """

    SITE_KEY = "site"

    PAGE_CHOICES = [
        (SITE_KEY, _("Увесь сайт (за замовчуванням)")),
        ("content:home", _("Головна")),
        ("catalog:product_list", _("Каталог — список товарів")),
        ("catalog:product_detail", _("Каталог — картка товару")),
        ("brands:brand_list", _("Бренди — список")),
        ("brands:brand_detail", _("Бренди — сторінка бренду")),
        ("content:promo_list", _("Акції — список")),
        ("content:promo_detail", _("Акції — сторінка акції")),
        ("content:news_list", _("Новини — список")),
        ("content:news_detail", _("Новини — сторінка новини")),
        ("vacancies:list", _("Вакансії — список")),
        ("vacancies:detail", _("Вакансії — сторінка вакансії")),
        ("contacts:contact", _("Контакти")),
    ]

    page_key = models.CharField(
        _("Сторінка"),
        max_length=64,
        unique=True,
        choices=PAGE_CHOICES,
        default=SITE_KEY,
    )
    image = models.ImageField(_("Зображення"), upload_to="backgrounds/",
                              validators=raster_image_validators)
    is_active = models.BooleanField(_("Активний"), default=True)
    overlay_opacity = models.PositiveSmallIntegerField(
        _("Затемнення, %"),
        default=40,
        help_text=_("Прозорість підкладки поверх фону (0–90), щоб текст залишався читабельним."),
    )
    updated_at = models.DateTimeField(_("Оновлено"), auto_now=True)

    class Meta:
        verbose_name = _("Фон сторінки")
        verbose_name_plural = _("Фони сторінок")
        ordering = ["page_key"]

    def __str__(self) -> str:
        return self.get_page_key_display()
