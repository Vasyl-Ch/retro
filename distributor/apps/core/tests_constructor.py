"""Tests for the visual constructor: element styles, animated backgrounds, preview."""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from apps.core.appearance.elements import (
    ElementStyleValues,
    build_element_css,
    element_declarations,
    element_selector,
)
from apps.core.appearance.preview import preview_url_for
from apps.core.models import ElementStyle, PageBackground
from apps.core.validators import validate_css_declarations, validate_json_object


class ElementCssBuilderTests(SimpleTestCase):
    def test_empty_values_produce_no_declarations(self):
        self.assertEqual(element_declarations(ElementStyleValues(element_key="navbar")), [])

    def test_color_size_position_declarations(self):
        v = ElementStyleValues(
            element_key="hero-title", text_color="#ff0000", bg_color="#00ff0080",
            opacity=80, font_size=48, text_align="center",
            offset_x=20, offset_y=-10, scale=120, max_width=600,
            border_radius=12, padding=24,
        )
        decls = element_declarations(v)
        self.assertIn("color: #ff0000 !important", decls)
        self.assertIn("background-color: #00ff0080 !important", decls)
        self.assertIn("opacity: 0.8", decls)
        self.assertIn("font-size: 48px !important", decls)
        self.assertIn("text-align: center !important", decls)
        self.assertIn("translate: 20px -10px", decls)
        self.assertIn("scale: 1.2", decls)
        self.assertIn("max-width: 600px !important", decls)
        self.assertIn("border-radius: 12px !important", decls)
        self.assertIn("padding: 24px !important", decls)

    def test_hidden_wins_over_everything(self):
        v = ElementStyleValues(element_key="footer", hidden=True, text_color="#fff")
        self.assertEqual(element_declarations(v), ["display: none !important"])

    def test_effect_emits_animation(self):
        v = ElementStyleValues(element_key="hero-title", effect="float")
        self.assertTrue(any(d.startswith("animation: el-float") for d in element_declarations(v)))

    def test_custom_css_is_sanitized(self):
        v = ElementStyleValues(
            element_key="hero-title",
            custom_css="letter-spacing: 2px; } body { color: red",
        )
        decls = element_declarations(v)
        self.assertIn("letter-spacing: 2px", decls)
        self.assertEqual(len(decls), 1)  # the escape attempt is dropped

    def test_site_selector_and_page_scoped_selector(self):
        site = ElementStyleValues(page_key="site", element_key="navbar")
        page = ElementStyleValues(page_key="content:home", element_key="navbar")
        self.assertEqual(element_selector(site), '[data-el="navbar"]')
        self.assertEqual(
            element_selector(page), 'body[data-page="content:home"] [data-el="navbar"]'
        )

    def test_selector_overrides_for_classy_elements(self):
        v = ElementStyleValues(page_key="site", element_key="cta-button")
        self.assertEqual(element_selector(v), ".btn.variant-primary")

    def test_build_orders_site_rules_before_page_rules(self):
        css = build_element_css([
            ElementStyleValues(page_key="content:home", element_key="navbar", text_color="#111111"),
            ElementStyleValues(page_key="site", element_key="navbar", text_color="#222222"),
        ])
        self.assertLess(css.index("#222222"), css.index("#111111"))

    def test_unknown_element_key_is_skipped(self):
        css = build_element_css([
            ElementStyleValues(page_key="site", element_key="nope", text_color="#123456"),
        ])
        self.assertEqual(css, "")

    def test_from_mapping_tolerates_junk(self):
        v = ElementStyleValues.from_mapping({
            "element_key": "navbar", "opacity": "abc", "offset_x": "",
            "scale": "150", "hidden": "1",
        })
        self.assertEqual(v.opacity, 100)
        self.assertEqual(v.offset_x, 0)
        self.assertEqual(v.scale, 150)
        self.assertTrue(v.hidden)


class CssDeclarationsValidatorTests(SimpleTestCase):
    def test_valid_declarations_pass(self):
        validate_css_declarations("letter-spacing: 2px; text-transform: uppercase;")

    def test_braces_rejected(self):
        with self.assertRaises(ValidationError):
            validate_css_declarations("color: red } body { color: blue")

    def test_at_rules_rejected(self):
        with self.assertRaises(ValidationError):
            validate_css_declarations("@import url(evil)")

    def test_missing_colon_rejected(self):
        with self.assertRaises(ValidationError):
            validate_css_declarations("just some words")


class ElementStyleModelTests(TestCase):
    def test_unique_per_page_and_element(self):
        ElementStyle.objects.create(page_key="site", element_key="navbar")
        with self.assertRaises(IntegrityError):
            ElementStyle.objects.create(page_key="site", element_key="navbar")

    def test_str_uses_display_labels(self):
        style = ElementStyle(page_key="site", element_key="navbar")
        self.assertIn("Navbar", str(style))


class PageBackgroundKindTests(TestCase):
    def test_image_kind_requires_image(self):
        bg = PageBackground(page_key="site", kind=PageBackground.KIND_IMAGE)
        with self.assertRaises(ValidationError):
            bg.full_clean()

    def test_animated_kind_needs_no_image(self):
        bg = PageBackground(page_key="site", kind=PageBackground.KIND_GRADIENT)
        bg.full_clean()  # must not raise

    def test_colors_property_skips_empty(self):
        bg = PageBackground(kind=PageBackground.KIND_AURORA, color_1="#ff0000", color_3="#0000ff")
        self.assertEqual(bg.colors, ["#ff0000", "#0000ff"])

    def test_custom_kind_requires_config(self):
        bg = PageBackground(page_key="site", kind=PageBackground.KIND_CUSTOM)
        with self.assertRaises(ValidationError):
            bg.full_clean()
        bg.custom_config = '{"particles": {"number": {"value": 10}}}'
        bg.full_clean()  # must not raise

    def test_particle_kinds_set(self):
        self.assertIn(PageBackground.KIND_SNOW, PageBackground.PARTICLE_KINDS)
        self.assertNotIn(PageBackground.KIND_GRADIENT, PageBackground.PARTICLE_KINDS)


class JsonObjectValidatorTests(SimpleTestCase):
    def test_valid_object_passes(self):
        validate_json_object('{"a": 1}')
        validate_json_object("")  # blank is allowed

    def test_invalid_json_rejected(self):
        with self.assertRaises(ValidationError):
            validate_json_object("{not json")

    def test_non_object_rejected(self):
        with self.assertRaises(ValidationError):
            validate_json_object("[1, 2, 3]")


class ConstructorRenderTests(TestCase):
    def test_element_css_is_rendered_on_page(self):
        ElementStyle.objects.create(
            page_key="site", element_key="navbar", text_color="#ab12cd"
        )
        resp = self.client.get("/")
        self.assertContains(resp, "element-overrides")
        self.assertContains(resp, "color: #ab12cd !important")

    def test_page_scoped_style_only_on_its_page(self):
        ElementStyle.objects.create(
            page_key="contacts:contact", element_key="contact-form", bg_color="#fafafa"
        )
        self.assertNotContains(self.client.get("/"), "#fafafa")
        self.assertContains(self.client.get("/contact/"), "#fafafa")

    def test_inactive_style_not_rendered(self):
        ElementStyle.objects.create(
            page_key="site", element_key="navbar", text_color="#ab12cd", is_active=False
        )
        self.assertNotContains(self.client.get("/"), "#ab12cd")

    def test_body_carries_data_page(self):
        self.assertContains(self.client.get("/"), 'data-page="content:home"')

    def test_animated_background_layer_rendered(self):
        PageBackground.objects.create(
            page_key="site", kind=PageBackground.KIND_GRADIENT,
            color_1="#ff0000", speed=150,
        )
        resp = self.client.get("/")
        self.assertContains(resp, "anim-bg-gradient")
        self.assertContains(resp, "--bg-c1: #ff0000")
        self.assertNotContains(resp, "has-page-bg")

    def test_particles_layer_has_data_attribute(self):
        PageBackground.objects.create(page_key="site", kind=PageBackground.KIND_PARTICLES)
        self.assertContains(self.client.get("/"), "data-particles")

    def test_custom_kind_embeds_config_json(self):
        PageBackground.objects.create(
            page_key="site", kind=PageBackground.KIND_CUSTOM,
            custom_config='{"particles": {"number": {"value": 7}}}',
        )
        resp = self.client.get("/")
        self.assertContains(resp, "bg-custom-config")
        self.assertContains(resp, "data-particles")

    def test_inactive_background_renders_nothing(self):
        PageBackground.objects.create(
            page_key="site", kind=PageBackground.KIND_GRADIENT, is_active=False
        )
        resp = self.client.get("/")
        self.assertNotContains(resp, "animated-bg")

    def test_same_origin_framing_allowed_for_admin_preview(self):
        self.assertEqual(self.client.get("/")["X-Frame-Options"], "SAMEORIGIN")


class PreviewUrlTests(TestCase):
    def test_site_maps_to_home(self):
        self.assertEqual(preview_url_for("site"), "/")

    def test_list_page_reverses(self):
        self.assertEqual(preview_url_for("catalog:product_list"), reverse("catalog:product_list"))

    def test_detail_without_objects_falls_back_to_list(self):
        self.assertEqual(preview_url_for("vacancies:detail"), reverse("vacancies:list"))


class ElementPreviewEndpointTests(TestCase):
    def _login_admin(self):
        admin = get_user_model().objects.create_superuser("cs", "cs@x.com", "pw")
        self.client.force_login(admin)

    def test_endpoint_returns_css_for_staff(self):
        self._login_admin()
        resp = self.client.get(
            reverse("admin:core_elementstyle_preview_css"),
            {"page_key": "site", "element_key": "navbar", "text_color": "#ff0000"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("color: #ff0000 !important", resp.json()["css"])

    def test_endpoint_merges_saved_styles_but_replaces_edited_element(self):
        self._login_admin()
        ElementStyle.objects.create(page_key="site", element_key="navbar", text_color="#111111")
        ElementStyle.objects.create(page_key="site", element_key="footer", text_color="#222222")
        resp = self.client.get(
            reverse("admin:core_elementstyle_preview_css"),
            {"page_key": "site", "element_key": "navbar", "text_color": "#333333"},
        )
        css = resp.json()["css"]
        self.assertIn("#333333", css)  # unsaved form value
        self.assertIn("#222222", css)  # untouched saved style kept
        self.assertNotIn("#111111", css)  # stale saved rule for edited element dropped

    def test_endpoint_blocks_anonymous(self):
        resp = self.client.get(reverse("admin:core_elementstyle_preview_css"))
        self.assertIn(resp.status_code, (302, 403))

    def test_change_form_renders_with_preview(self):
        self._login_admin()
        resp = self.client.get(reverse("admin:core_elementstyle_add"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "element-frame")
        self.assertContains(resp, reverse("admin:core_elementstyle_preview_css"))
