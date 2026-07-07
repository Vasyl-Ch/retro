"""Full-site crawl for every preset: no page may error in any vertical.

For each preset we apply it to the singleton, then request every public page
(list + detail, both languages, plus catalog filters and the cart) and assert
a 200. This is the regression net for "любой пресет — ни единой ошибки".
"""

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Brand, Product
from apps.content.models import News, Promo
from apps.core.models import ElementStyle, PageBackground, SiteSettings
from apps.core.presets import PRESETS, apply_preset
from apps.vacancies.models import Vacancy


class PresetCrawlTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_data", verbosity=0)
        # Exercise the constructor paths too: element styles + animated bg.
        ElementStyle.objects.create(page_key="site", element_key="navbar",
                                    text_color="#112233")
        ElementStyle.objects.create(page_key="content:home", element_key="hero-title",
                                    scale=110, offset_y=-8, effect="fade-in")
        PageBackground.objects.create(page_key="site",
                                      kind=PageBackground.KIND_AURORA, speed=80)

    def _urls(self) -> list[str]:
        urls = [
            reverse("content:home"),
            reverse("catalog:product_list"),
            reverse("catalog:product_list") + "?q=про&sort=price_asc&page=1",
            reverse("brands:brand_list"),
            reverse("content:promo_list"),
            reverse("content:news_list"),
            reverse("vacancies:list"),
            reverse("contacts:contact"),
            reverse("cart:detail"),
            "/robots.txt",
        ]
        product = Product.objects.filter(is_active=True).first()
        if product:
            urls.append(product.get_absolute_url())
        brand = Brand.objects.filter(is_active=True).first()
        if brand:
            urls.append(brand.get_absolute_url())
        promo = Promo.objects.filter(is_active=True).first()
        if promo:
            urls.append(promo.get_absolute_url())
        news = News.objects.filter(is_active=True).first()
        if news:
            urls.append(news.get_absolute_url())
        vacancy = Vacancy.objects.filter(is_active=True).first()
        if vacancy:
            urls.append(vacancy.get_absolute_url())
        return urls

    def test_every_preset_serves_every_page(self):
        for preset in PRESETS:
            with self.subTest(preset=preset):
                apply_preset(SiteSettings.get_solo(), preset)
                for lang in ("en", "uk"):
                    self.client.cookies["django_language"] = lang
                    for url in self._urls():
                        resp = self.client.get(url)
                        self.assertEqual(
                            resp.status_code, 200,
                            f"{preset}/{lang} {url} -> {resp.status_code}",
                        )

    def test_every_home_layout_renders(self):
        settings_obj = SiteSettings.get_solo()
        for layout, _label in SiteSettings.LAYOUT_CHOICES:
            with self.subTest(layout=layout):
                settings_obj.home_layout = layout
                settings_obj.save()
                self.assertEqual(self.client.get(reverse("content:home")).status_code, 200)

    def test_every_theme_and_rounding_renders(self):
        settings_obj = SiteSettings.get_solo()
        for theme, _label in SiteSettings.THEME_CHOICES:
            settings_obj.theme = theme
            settings_obj.save()
            resp = self.client.get(reverse("content:home"))
            self.assertContains(resp, f'data-theme="{theme}"')
        for rounding, _label in SiteSettings.ROUNDING_CHOICES:
            settings_obj.corner_style = rounding
            settings_obj.save()
            resp = self.client.get(reverse("content:home"))
            self.assertContains(resp, f'data-rounded="{rounding}"')

    def test_every_background_kind_renders(self):
        bg = PageBackground.objects.get(page_key="site")
        for kind, _label in PageBackground.KIND_CHOICES:
            if kind == PageBackground.KIND_IMAGE:
                continue  # image kind is covered by existing background tests
            with self.subTest(kind=kind):
                bg.kind = kind
                bg.save()
                resp = self.client.get(reverse("content:home"))
                self.assertContains(resp, f"anim-bg-{kind}")
