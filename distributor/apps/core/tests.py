from django.conf import settings as dj_settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from django.test import TestCase as DBTestCase
from django.test import RequestFactory
from django.urls import ResolverMatch

from apps.core.context_processors import page_background
from apps.core.models import PageBackground
from apps.core.conf_checks import (
    INSECURE_SECRET_KEY,
    assert_allowed_hosts,
    assert_production_secret,
)
from apps.core.sanitizer import sanitize_html
from apps.core.validators import (
    MAX_IMAGE_BYTES,
    branding_image_validators,
    raster_image_validators,
    validate_image_size,
)


class ProductionSecretGuardTests(SimpleTestCase):
    def test_default_key_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            assert_production_secret(INSECURE_SECRET_KEY)

    def test_empty_key_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            assert_production_secret("")

    def test_none_key_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            assert_production_secret(None)

    def test_django_insecure_prefix_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            assert_production_secret("django-insecure-abc123randomkeygeneratedbystartproject")

    def test_valid_key_accepted(self):
        assert_production_secret("a-real-secret-key-value-xxxxxxxxxxxxxxxxxxxxxxxxxx")


class AllowedHostsGuardTests(SimpleTestCase):
    def test_empty_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            assert_allowed_hosts([])

    def test_nonempty_accepted(self):
        assert_allowed_hosts(["example.com"])


class SanitizeHtmlTests(SimpleTestCase):
    def test_script_tag_removed(self):
        out = sanitize_html("<p>hi</p><script>alert(1)</script>")
        self.assertNotIn("<script", out)
        self.assertIn("<p>hi</p>", out)

    def test_event_handler_attribute_removed(self):
        out = sanitize_html('<img src="http://x/y.png" onerror="alert(1)">')
        self.assertNotIn("onerror", out)

    def test_javascript_uri_removed(self):
        out = sanitize_html('<a href="javascript:alert(1)">x</a>')
        self.assertNotIn("javascript:", out)

    def test_allowed_formatting_preserved(self):
        out = sanitize_html("<p><strong>bold</strong> and <em>italic</em></p>")
        self.assertIn("<strong>bold</strong>", out)
        self.assertIn("<em>italic</em>", out)

    def test_empty_input(self):
        self.assertEqual(sanitize_html(""), "")
        self.assertEqual(sanitize_html(None), "")


def _run(validators, f):
    for v in validators:
        v(f)


class ImageValidatorTests(SimpleTestCase):
    def test_raster_rejects_svg(self):
        f = SimpleUploadedFile("a.svg", b"<svg></svg>", content_type="image/svg+xml")
        with self.assertRaises(ValidationError):
            _run(raster_image_validators, f)

    def test_branding_allows_svg(self):
        f = SimpleUploadedFile("a.svg", b"<svg></svg>", content_type="image/svg+xml")
        _run(branding_image_validators, f)  # must not raise

    def test_rejects_non_image_extension(self):
        f = SimpleUploadedFile("a.exe", b"MZ", content_type="application/octet-stream")
        with self.assertRaises(ValidationError):
            _run(raster_image_validators, f)

    def test_allows_png(self):
        f = SimpleUploadedFile("a.png", b"\x89PNG", content_type="image/png")
        _run(raster_image_validators, f)  # must not raise

    def test_rejects_oversize(self):
        big = SimpleUploadedFile(
            "a.png", b"x" * (MAX_IMAGE_BYTES + 1), content_type="image/png"
        )
        with self.assertRaises(ValidationError):
            validate_image_size(big)


class PageBackgroundContextTests(DBTestCase):
    def test_page_specific_overrides_site(self):
        PageBackground.objects.create(page_key="site", image="backgrounds/site.jpg")
        PageBackground.objects.create(page_key="content:home", image="backgrounds/home.jpg")
        req = RequestFactory().get("/")
        req.resolver_match = ResolverMatch(
            func=lambda r: None, args=(), kwargs={},
            url_name="home", namespaces=["content"],
        )
        ctx = page_background(req)
        self.assertEqual(ctx["page_background"], "/media/backgrounds/home.jpg")

    def test_site_fallback_when_no_match(self):
        PageBackground.objects.create(page_key="site", image="backgrounds/site.jpg", overlay_opacity=40)
        req = RequestFactory().get("/")  # no resolver_match
        ctx = page_background(req)
        self.assertEqual(ctx["page_background"], "/media/backgrounds/site.jpg")
        self.assertEqual(ctx["page_background_overlay"], 40)

    def test_query_is_single_and_narrowed(self):
        PageBackground.objects.create(page_key="site", image="backgrounds/site.jpg")
        req = RequestFactory().get("/")
        with self.assertNumQueries(1):
            page_background(req)


class I18nDefaultsTests(SimpleTestCase):
    def test_default_language_is_english(self):
        self.assertEqual(dj_settings.LANGUAGE_CODE, "en")

    def test_modeltranslation_defaults_english(self):
        self.assertEqual(dj_settings.MODELTRANSLATION_DEFAULT_LANGUAGE, "en")
        self.assertEqual(tuple(dj_settings.MODELTRANSLATION_FALLBACK_LANGUAGES), ("en", "uk"))


from django.utils import translation
from apps.core.models import SiteSettings


class SiteSettingsI18nTests(DBTestCase):
    def test_brand_name_is_single_field(self):
        # brand_name must no longer have modeltranslation columns.
        field_names = {f.name for f in SiteSettings._meta.get_fields()}
        self.assertIn("brand_name", field_names)
        self.assertNotIn("brand_name_en", field_names)
        self.assertNotIn("brand_name_uk", field_names)

    def test_english_defaults_present(self):
        s = SiteSettings()
        self.assertEqual(s.nav_catalog_label, "Catalog")
        self.assertEqual(s.term_product_singular, "Product")

    def test_fallback_uk_empty_shows_en(self):
        s = SiteSettings.objects.create()
        s.nav_brands_label_en = "Brands"
        s.nav_brands_label_uk = ""
        s.save()
        with translation.override("uk"):
            s.refresh_from_db()
            self.assertEqual(s.nav_brands_label, "Brands")  # fell back to en


class BilingualRenderTests(SimpleTestCase):
    SAMPLES = {
        "Catalog": "Каталог",
        "Products": "Товари",
        "Contacts": "Контакти",
        "Apply": "Відгукнутися",
    }

    def test_english_is_source(self):
        with translation.override("en"):
            for en in self.SAMPLES:
                self.assertEqual(translation.gettext(en), en)

    def test_ukrainian_from_catalog(self):
        with translation.override("uk"):
            for en, uk in self.SAMPLES.items():
                self.assertEqual(translation.gettext(en), uk)


class ApplyPresetI18nTests(DBTestCase):
    def test_preset_preserves_brand_name(self):
        from apps.core.presets import apply_preset
        s = SiteSettings.objects.create(brand_name="My Custom Brand")
        apply_preset(s, "auto")
        s.refresh_from_db()
        self.assertEqual(s.brand_name, "My Custom Brand")  # site name preserved

    def test_preset_sets_english_base_for_translated_fields(self):
        from apps.core.presets import apply_preset
        s = SiteSettings.objects.create()
        apply_preset(s, "auto")
        s.refresh_from_db()
        # base mirrors the English (default-language) value, not Ukrainian
        self.assertEqual(s.nav_catalog_label, s.nav_catalog_label_en)
        self.assertEqual(s.term_product_singular, s.term_product_singular_en)
        # uk variant still populated from the preset
        self.assertTrue(s.nav_catalog_label_uk)


class SummernoteTextFieldNoneSafetyTests(SimpleTestCase):
    """Regression: the rich-text field must not crash on None.

    modeltranslation adds null=True `_en`/`_uk` copies of the rich-text
    fields. Django computes their column default via get_prep_value(None)
    (and a runtime save() of a row with an empty variant does the same),
    which the upstream SummernoteTextField.to_python feeds to bleach.clean
    -> TypeError. Our subclass guards None like Django's TextField does.
    """

    def test_to_python_and_get_prep_value_pass_none_through(self):
        from apps.core.fields import SummernoteTextField

        field = SummernoteTextField()
        self.assertIsNone(field.to_python(None))
        self.assertIsNone(field.get_prep_value(None))

    def test_str_values_are_still_sanitized(self):
        from apps.core.fields import SummernoteTextField

        field = SummernoteTextField()
        cleaned = field.to_python("<p>ok</p><script>alert(1)</script>")
        self.assertIn("<p>ok</p>", cleaned)
        self.assertNotIn("<script", cleaned)


class TranslatedAdminSmokeTests(DBTestCase):
    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth import get_user_model

        cls.admin = get_user_model().objects.create_superuser("a", "a@x.com", "pw")

    def setUp(self):
        self.client.force_login(self.admin)

    def test_add_pages_render_with_language_fields(self):
        from django.urls import reverse

        for url_name, marker in [
            ("admin:catalog_brand_add", "name_en"),
            ("admin:catalog_product_add", "name_uk"),
            ("admin:content_news_add", "content_en"),
            ("admin:content_promo_add", "description_uk"),
            ("admin:vacancies_vacancy_add", "description_en"),
        ]:
            resp = self.client.get(reverse(url_name))
            self.assertEqual(resp.status_code, 200, url_name)
            self.assertContains(resp, marker)
