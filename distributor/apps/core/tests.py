from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from apps.core.conf_checks import (
    INSECURE_SECRET_KEY,
    assert_allowed_hosts,
    assert_production_secret,
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


from apps.core.sanitizer import sanitize_html


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
