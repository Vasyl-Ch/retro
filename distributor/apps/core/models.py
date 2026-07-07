from colorfield.fields import ColorField
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from solo.models import SingletonModel

from apps.core.appearance.elements import ELEMENTS
from apps.core.validators import (
    branding_image_validators,
    raster_image_validators,
    validate_css_declarations,
    validate_json_object,
)


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

    custom_accent = ColorField(
        _("Custom accent colour"), blank=True, default="",
        help_text=_("Overrides the theme's primary colour. Empty = use the selected theme."),
    )
    chrome_bg = ColorField(
        _("Header/footer background"), blank=True, default="",
        help_text=_("Overrides the header & footer background. Empty = theme default."),
    )
    chrome_text = ColorField(
        _("Header/footer text"), blank=True, default="",
    )
    chrome_opacity = models.PositiveSmallIntegerField(
        _("Header/footer opacity, %"), default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("100 = solid, lower = more transparent."),
    )

    ROUNDING_CHOICES = [
        ("none", _("None (sharp corners)")),
        ("small", _("Small")),
        ("medium", _("Medium")),
        ("large", _("Large")),
        ("xlarge", _("Extra large")),
        ("2xlarge", _("2× extra large")),
        ("3xlarge", _("3× extra large (default)")),
        ("full", _("Full (pill buttons)")),
    ]
    corner_style = models.CharField(
        _("Corner rounding"),
        max_length=10,
        choices=ROUNDING_CHOICES,
        default="3xlarge",
        help_text=_("Roundness of cards, buttons and inputs across the site."),
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

    KIND_IMAGE = "image"
    KIND_GRADIENT = "gradient"
    KIND_AURORA = "aurora"
    KIND_WAVES = "waves"
    KIND_PARTICLES = "particles"
    KIND_BUBBLES = "bubbles"
    KIND_SNOW = "snow"
    KIND_STARS = "stars"
    KIND_CUSTOM = "custom"
    KIND_CHOICES = [
        (KIND_IMAGE, _("Image (static photo)")),
        (KIND_GRADIENT, _("Animated gradient")),
        (KIND_AURORA, _("Aurora (soft drifting glow)")),
        (KIND_WAVES, _("Waves (flowing bands)")),
        (KIND_PARTICLES, _("Particles (interactive network)")),
        (KIND_BUBBLES, _("Bubbles (floating up)")),
        (KIND_SNOW, _("Snow (falling flakes)")),
        (KIND_STARS, _("Stars (twinkling)")),
        (KIND_CUSTOM, _("Custom (own tsparticles JSON config)")),
    ]
    # Kinds rendered by the tsparticles engine (need the JS module).
    PARTICLE_KINDS = {KIND_PARTICLES, KIND_BUBBLES, KIND_SNOW, KIND_STARS, KIND_CUSTOM}

    page_key = models.CharField(
        _("Page"),
        max_length=64,
        unique=True,
        choices=PAGE_CHOICES,
        default=SITE_KEY,
    )
    kind = models.CharField(
        _("Background type"),
        max_length=12,
        choices=KIND_CHOICES,
        default=KIND_IMAGE,
        help_text=_("Animated types use the colours below (empty = the theme's accent)."),
    )
    image = models.ImageField(_("Image"), upload_to="backgrounds/", blank=True,
                              validators=raster_image_validators,
                              help_text=_("Required for the “Image” type; ignored otherwise."))
    # NB: unchecking "Active" removes the background from the page entirely.
    color_1 = ColorField(_("Colour 1"), blank=True, default="", format="hexa")
    color_2 = ColorField(_("Colour 2"), blank=True, default="", format="hexa")
    color_3 = ColorField(_("Colour 3"), blank=True, default="", format="hexa")
    speed = models.PositiveSmallIntegerField(
        _("Animation speed, %"),
        default=100,
        validators=[MinValueValidator(10), MaxValueValidator(300)],
        help_text=_("100 = normal. Lower is slower and calmer, higher is faster."),
    )
    custom_config = models.TextField(
        _("Custom background config (JSON)"), blank=True, default="",
        validators=[validate_json_object],
        help_text=_(
            "For the “Custom” type: a tsparticles options object (JSON). "
            "See https://particles.js.org for examples — paste any preset here."
        ),
    )
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    overlay_opacity = models.PositiveSmallIntegerField(
        _("Overlay, %"),
        default=40,
        help_text=_("Opacity of the overlay above the background (0–90) to keep text readable."),
    )
    POSITION_CHOICES = [
        ("center", _("Center")), ("top", _("Top")), ("bottom", _("Bottom")),
        ("left", _("Left")), ("right", _("Right")),
        ("top left", _("Top-left")), ("top right", _("Top-right")),
        ("bottom left", _("Bottom-left")), ("bottom right", _("Bottom-right")),
    ]
    SIZE_CHOICES = [("cover", _("Cover (fill)")), ("contain", _("Contain (fit)"))]

    position = models.CharField(
        _("Background position"), max_length=20, choices=POSITION_CHOICES, default="center",
    )
    size = models.CharField(
        _("Background size"), max_length=10, choices=SIZE_CHOICES, default="cover",
    )
    updated_at = models.DateTimeField(_("Updated"), auto_now=True)

    class Meta:
        verbose_name = _("Page background")
        verbose_name_plural = _("Page backgrounds")
        ordering = ["page_key"]

    def __str__(self) -> str:
        return self.get_page_key_display()

    def clean(self) -> None:
        if self.kind == self.KIND_IMAGE and not self.image:
            raise ValidationError({"image": _("Upload an image or pick an animated background type.")})
        if self.kind == self.KIND_CUSTOM and not (self.custom_config or "").strip():
            raise ValidationError({"custom_config": _(
                "The “Custom” type needs a tsparticles JSON config (or pick a built-in type)."
            )})

    @property
    def colors(self) -> list[str]:
        """Non-empty custom colours in order (may be empty → theme accent is used)."""
        return [c for c in (self.color_1, self.color_2, self.color_3) if c]


class ElementStyle(models.Model):
    """Стиль конкретного елемента сторінки, керований з конструктора в адмінці.

    Прив'язка — до якоря ``data-el`` у шаблонах; область дії — весь сайт
    (``page_key = "site"``) або одна сторінка. CSS генерує
    ``apps.core.appearance.elements.build_element_css``.
    """

    ELEMENT_CHOICES = [(key, _(label)) for key, label in ELEMENTS]
    ALIGN_CHOICES = [
        ("", _("Theme default")),
        ("left", _("Left")),
        ("center", _("Center")),
        ("right", _("Right")),
    ]
    EFFECT_CHOICES = [
        ("", _("None")),
        ("float", _("Float (gentle up/down)")),
        ("pulse", _("Pulse (breathing)")),
        ("fade-in", _("Fade in on load")),
        ("slide-up", _("Slide up on load")),
    ]

    page_key = models.CharField(
        _("Page"),
        max_length=64,
        choices=PageBackground.PAGE_CHOICES,
        default=PageBackground.SITE_KEY,
        help_text=_("“Whole site” applies everywhere; a page-specific style overrides it."),
    )
    element_key = models.CharField(_("Element"), max_length=40, choices=ELEMENT_CHOICES)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)

    text_color = ColorField(_("Text colour"), blank=True, default="", format="hexa")
    bg_color = ColorField(_("Background colour"), blank=True, default="", format="hexa")
    opacity = models.PositiveSmallIntegerField(
        _("Opacity, %"), default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    font_size = models.PositiveSmallIntegerField(
        _("Font size, px"), null=True, blank=True,
        validators=[MinValueValidator(8), MaxValueValidator(200)],
        help_text=_("Empty = theme size."),
    )
    text_align = models.CharField(_("Text alignment"), max_length=6, blank=True,
                                  choices=ALIGN_CHOICES, default="")
    offset_x = models.SmallIntegerField(
        _("Shift right/left, px"), default=0,
        validators=[MinValueValidator(-500), MaxValueValidator(500)],
        help_text=_("Positive = right, negative = left."),
    )
    offset_y = models.SmallIntegerField(
        _("Shift down/up, px"), default=0,
        validators=[MinValueValidator(-500), MaxValueValidator(500)],
        help_text=_("Positive = down, negative = up."),
    )
    scale = models.PositiveSmallIntegerField(
        _("Size (scale), %"), default=100,
        validators=[MinValueValidator(10), MaxValueValidator(300)],
        help_text=_("Visual zoom of the element. 100 = normal size."),
    )
    max_width = models.PositiveSmallIntegerField(
        _("Max width, px"), null=True, blank=True,
        validators=[MinValueValidator(40), MaxValueValidator(3000)],
    )
    border_radius = models.PositiveSmallIntegerField(
        _("Corner radius, px"), null=True, blank=True,
        validators=[MaxValueValidator(200)],
    )
    padding = models.PositiveSmallIntegerField(
        _("Inner padding, px"), null=True, blank=True,
        validators=[MaxValueValidator(300)],
    )
    hidden = models.BooleanField(
        _("Hide element"), default=False,
        help_text=_("Removes the element from the page entirely."),
    )
    effect = models.CharField(_("Animation"), max_length=10, blank=True,
                              choices=EFFECT_CHOICES, default="")
    custom_css = models.TextField(
        _("Extra CSS (advanced)"), blank=True, default="",
        validators=[validate_css_declarations],
        help_text=_("Extra CSS declarations, e.g. “letter-spacing: 2px; text-transform: uppercase;”"),
    )
    updated_at = models.DateTimeField(_("Updated"), auto_now=True)

    class Meta:
        verbose_name = _("Element style")
        verbose_name_plural = _("Element styles (constructor)")
        ordering = ["page_key", "element_key"]
        constraints = [
            models.UniqueConstraint(fields=["page_key", "element_key"],
                                    name="unique_elementstyle_per_page_element"),
        ]

    def __str__(self) -> str:
        return f"{self.get_element_key_display()} — {self.get_page_key_display()}"
