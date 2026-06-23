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
        (PRESET_DISTRIBUTOR, _("Distributor")),
        (PRESET_AUTO, _("Auto dealership")),
        (PRESET_FOOD, _("Food / restaurant")),
        (PRESET_SHOP, _("Shop (cart)")),
        (PRESET_GENERIC, _("Generic landing")),
    ]

    THEME_CLASSIC = "classic"
    THEME_CYBERPUNK = "cyberpunk"
    THEME_NUDE = "nude"
    THEME_DARKLUX = "darklux"
    THEME_CHOICES = [
        (THEME_CLASSIC, _("Classic (light blue)")),
        (THEME_CYBERPUNK, _("Cyberpunk (neon)")),
        (THEME_NUDE, _("Nude (pastel)")),
        (THEME_DARKLUX, _("Dark Lux (premium dark)")),
    ]

    preset = models.CharField(
        _("Preset (vertical)"),
        max_length=20,
        choices=PRESET_CHOICES,
        default=PRESET_DISTRIBUTOR,
        help_text=_("Site type. Used by the apply_preset command to fill defaults."),
    )
    theme = models.CharField(
        _("Theme"),
        max_length=20,
        choices=THEME_CHOICES,
        default=THEME_CLASSIC,
    )

    BRAND_STYLE_PLAIN = "plain"
    BRAND_STYLE_GRADIENT = "gradient"
    BRAND_STYLE_UNDERLINE = "underline"
    BRAND_STYLE_SCRIPT = "script"
    BRAND_STYLE_CHOICES = [
        (BRAND_STYLE_PLAIN, _("Plain")),
        (BRAND_STYLE_GRADIENT, _("Gradient")),
        (BRAND_STYLE_UNDERLINE, _("Underline")),
        (BRAND_STYLE_SCRIPT, _("Script (italic)")),
    ]

    brand_name = models.CharField(_("Site name"), max_length=120, default="Distributor")
    brand_style = models.CharField(
        _("Site name style"),
        max_length=20,
        choices=BRAND_STYLE_CHOICES,
        default=BRAND_STYLE_PLAIN,
        help_text=_("Name text styling in the header/footer."),
    )
    tagline = models.CharField(_("Tagline"), max_length=300, blank=True)
    brand_logo = models.ImageField(_("Logo"), upload_to="branding/", blank=True, null=True,
                                   validators=branding_image_validators)
    favicon = models.ImageField(_("Favicon"), upload_to="branding/", blank=True, null=True,
                                validators=branding_image_validators)
    meta_description = models.CharField(_("SEO description (default)"), max_length=300, blank=True)
    footer_copyright = models.CharField(_("Footer copyright"), max_length=200, blank=True)
    cta_label = models.CharField(_("CTA button text"), max_length=80, default="Contact us")

    cart_enabled = models.BooleanField(
        _("Cart (shop mode)"),
        default=False,
        help_text=_(
            'Show prices, "Add to cart" buttons and the cart page. '
            'Enabled by the "Shop" preset. Orders arrive in the "Orders" section.'
        ),
    )

    contact_phone = models.CharField(_("Contact phone"), max_length=40, blank=True)
    contact_email = models.EmailField(_("Contact email"), blank=True)
    contact_address = models.CharField(_("Address"), max_length=200, blank=True)

    side_logo_left = models.ImageField(
        _("Side logo (left)"), upload_to="branding/", blank=True, null=True,
        validators=branding_image_validators,
        help_text=_(
            "On wide screens — pinned to the left (stays while scrolling). "
            "On mobile — below the content, before the footer."
        ),
    )
    side_logo_right = models.ImageField(
        _("Side logo (right)"), upload_to="branding/", blank=True, null=True,
        validators=branding_image_validators,
        help_text=_("Same as left, but on the right / second logo at the bottom on mobile."),
    )
    SIDE_LOGO_SM = "sm"
    SIDE_LOGO_MD = "md"
    SIDE_LOGO_LG = "lg"
    SIDE_LOGO_SIZE_CHOICES = [
        (SIDE_LOGO_SM, _("Small")),
        (SIDE_LOGO_MD, _("Medium")),
        (SIDE_LOGO_LG, _("Large")),
    ]
    side_logo_size = models.CharField(
        _("Side logo size"),
        max_length=2,
        choices=SIDE_LOGO_SIZE_CHOICES,
        default=SIDE_LOGO_MD,
        help_text=_(
            "Side logo size. On wide screens — the width of the pinned logos "
            "(constrained by the side margin so they don't overlap content); on mobile — "
            "the height of the logos in the bottom row."
        ),
    )

    nav_catalog_label = models.CharField(_("Menu: Catalog — label"), max_length=80, default="Catalog")
    nav_catalog_visible = models.BooleanField(_("Menu: Catalog — visible"), default=True)
    nav_brands_label = models.CharField(_("Menu: Brands — label"), max_length=80, default="Brands")
    nav_brands_visible = models.BooleanField(_("Menu: Brands — visible"), default=True)
    nav_promos_label = models.CharField(_("Menu: Promotions — label"), max_length=80, default="Promotions")
    nav_promos_visible = models.BooleanField(_("Menu: Promotions — show"), default=True)
    nav_news_label = models.CharField(_("Menu: News — label"), max_length=80, default="News")
    nav_news_visible = models.BooleanField(_("Menu: News — visible"), default=True)
    nav_vacancies_label = models.CharField(_("Menu: Vacancies — label"), max_length=80, default="Vacancies")
    nav_vacancies_visible = models.BooleanField(_("Menu: Vacancies — visible"), default=True)
    nav_contacts_label = models.CharField(_("Menu: Contacts — label"), max_length=80, default="Contacts")
    nav_contacts_visible = models.BooleanField(_("Menu: Contacts — show"), default=False)

    term_product_singular = models.CharField(_("Term: product (singular)"), max_length=80, default="Product")
    term_product_plural = models.CharField(_("Term: products (plural)"), max_length=80, default="Products")
    term_brand_singular = models.CharField(_("Term: brand (singular)"), max_length=80, default="Brand")
    term_brand_plural = models.CharField(_("Term: brands (plural)"), max_length=80, default="Brands")
    term_category_singular = models.CharField(_("Term: category (singular)"), max_length=80, default="Category")
    term_category_plural = models.CharField(_("Term: categories (plural)"), max_length=80, default="Categories")

    LAYOUT_CLASSIC = "classic"
    LAYOUT_EDITORIAL = "editorial"
    LAYOUT_CINEMATIC = "cinematic"
    LAYOUT_CHOICES = [
        (LAYOUT_CLASSIC, _("Classic (current)")),
        (LAYOUT_EDITORIAL, _("Editorial (magazine — large typographic hero)")),
        (LAYOUT_CINEMATIC, _("Cinematic (full-screen hero with video/photo)")),
    ]
    home_layout = models.CharField(
        _("Home layout"),
        max_length=20,
        choices=LAYOUT_CHOICES,
        default=LAYOUT_EDITORIAL,
        help_text=_("Hero section style on the home page."),
    )

    vacancy_description_label = models.CharField(
        _("Vacancy: \"Description\" section heading"), max_length=80, default="Description")
    vacancy_requirements_label = models.CharField(
        _("Vacancy: \"Requirements\" section heading"), max_length=80, default="Requirements")
    vacancy_conditions_label = models.CharField(
        _("Vacancy: \"Conditions\" section heading"), max_length=80, default="Conditions")
    vacancy_apply_label = models.CharField(
        _("Vacancy: apply button text"), max_length=80, default="Apply")

    hero_eyebrow = models.CharField(_("Hero: eyebrow"), max_length=80, blank=True,
                                    help_text=_("Small text above the large heading (e.g., \"Official distributor · 2026\")."))
    hero_title = models.CharField(_("Hero: main heading"), max_length=200, blank=True,
                                  help_text=_("Replaces the default. For the kinetic effect, emphasize a word with **word**."))
    hero_subtitle = models.CharField(_("Hero: subheading"), max_length=400, blank=True)

    anim_page_transitions = models.BooleanField(
        _("Animation: smooth page transitions"), default=True,
        help_text=_("View Transitions API. Works in Chrome/Edge/Safari; no animation in Firefox."),
    )
    anim_scroll_reveal = models.BooleanField(
        _("Animation: scroll reveal (fade-up + stagger)"), default=True,
    )
    anim_magnetic_buttons = models.BooleanField(
        _("Animation: magnetic buttons on hover"), default=True,
        help_text=_("Disabled on touch devices automatically."),
    )
    anim_cursor_follower = models.BooleanField(
        _("Animation: custom dot cursor"), default=False,
        help_text=_("Strong effect; not for every brand. Disabled automatically on touch devices."),
    )
    anim_kinetic_hero = models.BooleanField(
        _("Animation: kinetic hero title reveal"), default=True,
    )

    class Meta:
        verbose_name = _("Site settings")
        verbose_name_plural = _("Site settings")

    def __str__(self) -> str:
        return str(self._meta.verbose_name)


class PageBackground(models.Model):
    """Фонове зображення сайту або конкретної сторінки.

    Запис з ``page_key = "site"`` діє як фон за замовчуванням для всіх сторінок;
    інші записи перевизначають фон для конкретної сторінки (url name).
    """

    SITE_KEY = "site"

    PAGE_CHOICES = [
        (SITE_KEY, _("Whole site (default)")),
        ("content:home", _("Home")),
        ("catalog:product_list", _("Catalog — product list")),
        ("catalog:product_detail", _("Catalog — product page")),
        ("brands:brand_list", _("Brands — list")),
        ("brands:brand_detail", _("Brands — brand page")),
        ("content:promo_list", _("Promotions — list")),
        ("content:promo_detail", _("Promotions — promotion page")),
        ("content:news_list", _("News — list")),
        ("content:news_detail", _("News — article page")),
        ("vacancies:list", _("Vacancies — list")),
        ("vacancies:detail", _("Vacancies — vacancy page")),
        ("contacts:contact", _("Contacts")),
    ]

    page_key = models.CharField(
        _("Page"),
        max_length=64,
        unique=True,
        choices=PAGE_CHOICES,
        default=SITE_KEY,
    )
    image = models.ImageField(_("Image"), upload_to="backgrounds/",
                              validators=raster_image_validators)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    overlay_opacity = models.PositiveSmallIntegerField(
        _("Overlay, %"),
        default=40,
        help_text=_("Opacity of the overlay above the background (0–90) to keep text readable."),
    )
    updated_at = models.DateTimeField(_("Updated"), auto_now=True)

    class Meta:
        verbose_name = _("Page background")
        verbose_name_plural = _("Page backgrounds")
        ordering = ["page_key"]

    def __str__(self) -> str:
        return self.get_page_key_display()
