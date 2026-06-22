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
