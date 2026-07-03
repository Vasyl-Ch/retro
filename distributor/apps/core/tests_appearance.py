import re

from django.test import SimpleTestCase

from apps.core.appearance.palette import (
    RAMP_STEPS,
    AppearanceTheme,
    generate_primary_ramp,
)


class GeneratePrimaryRampTests(SimpleTestCase):
    def test_has_all_steps_in_triplet_format(self):
        ramp = generate_primary_ramp("#2563eb")
        self.assertEqual(set(ramp.steps), set(RAMP_STEPS))
        for value in ramp.steps.values():
            self.assertRegex(value, r"^\d{1,3} \d{1,3} \d{1,3}$")

    def test_anchor_600_is_exact_accent(self):
        # #2563eb -> 37 99 235
        self.assertEqual(generate_primary_ramp("#2563eb").steps[600], "37 99 235")

    def test_lightness_decreases_from_50_to_900(self):
        ramp = generate_primary_ramp("#2563eb")
        lum = lambda t: sum(int(x) for x in t.split())
        self.assertGreater(lum(ramp.steps[50]), lum(ramp.steps[900]))

    def test_achromatic_accent_yields_gray(self):
        r, g, b = generate_primary_ramp("#808080").steps[300].split()
        self.assertEqual(r, g)
        self.assertEqual(g, b)

    def test_invalid_hex_raises(self):
        with self.assertRaises(Exception):
            generate_primary_ramp("not-a-color")


class AppearanceThemeTests(SimpleTestCase):
    def test_empty_theme_has_no_declarations(self):
        self.assertTrue(AppearanceTheme().is_empty())
        self.assertEqual(AppearanceTheme().to_css_declarations(), "")

    def test_declarations_include_primary_and_chrome(self):
        theme = AppearanceTheme(
            primary=generate_primary_ramp("#2563eb"),
            chrome_bg="#111827", chrome_text="#ffffff", chrome_alpha=0.8,
        )
        css = theme.to_css_declarations()
        self.assertIn("--primary-600: 37 99 235;", css)
        self.assertIn("--chrome-bg: #111827;", css)
        self.assertIn("--chrome-alpha: 0.8;", css)


class _StubSettings:
    custom_accent = "#2563eb"
    chrome_bg = ""
    chrome_text = ""
    chrome_opacity = 80


class _EmptySettings:
    custom_accent = ""
    chrome_bg = ""
    chrome_text = ""
    chrome_opacity = 100


class AppearanceServiceTests(SimpleTestCase):
    def test_build_css_matches_preview_vars(self):
        from apps.core.appearance.services import build_appearance_css, preview_vars

        css = build_appearance_css(_StubSettings())
        for name, value in preview_vars(accent="#2563eb", chrome_opacity=80).items():
            self.assertIn(f"{name}: {value};", css)

    def test_empty_settings_produce_no_css(self):
        from apps.core.appearance.services import build_appearance_css

        self.assertEqual(build_appearance_css(_EmptySettings()), "")

    def test_opacity_100_emits_no_alpha(self):
        from apps.core.appearance.services import preview_vars

        self.assertNotIn("--chrome-alpha", preview_vars(accent="#2563eb", chrome_opacity=100))

    def test_invalid_accent_returns_empty_map(self):
        from apps.core.appearance.services import preview_vars

        self.assertEqual(preview_vars(accent="nope"), {})


from django.test import TestCase as _DBTestCase


class AppearanceModelTests(_DBTestCase):
    def test_sitesettings_appearance_fields_exist_and_drive_css(self):
        from apps.core.appearance.services import build_appearance_css
        from apps.core.models import SiteSettings

        s = SiteSettings.get_solo()
        s.custom_accent = "#2563eb"
        s.chrome_opacity = 70
        s.save()
        css = build_appearance_css(SiteSettings.get_solo())
        self.assertIn("--primary-600: 37 99 235;", css)
        self.assertIn("--chrome-alpha: 0.7;", css)

    def test_pagebackground_position_size_defaults(self):
        from apps.core.models import PageBackground

        bg = PageBackground(page_key=PageBackground.SITE_KEY)
        self.assertEqual(bg.position, "center")
        self.assertEqual(bg.size, "cover")


class AppearanceRenderTests(_DBTestCase):
    def test_home_emits_override_style_when_accent_set(self):
        from apps.core.models import SiteSettings

        s = SiteSettings.get_solo()
        s.custom_accent = "#2563eb"
        s.save()
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "appearance-overrides")
        self.assertContains(resp, "--primary-600: 37 99 235;")

    def test_home_has_no_override_style_by_default(self):
        from apps.core.models import SiteSettings

        SiteSettings.get_solo()  # defaults: no custom appearance
        resp = self.client.get("/")
        self.assertNotContains(resp, "appearance-overrides")
