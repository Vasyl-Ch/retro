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
