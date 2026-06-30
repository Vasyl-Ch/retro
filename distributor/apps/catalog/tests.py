from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse


class TranslationRegistrationTests(TestCase):
    def test_translated_fields_exist(self):
        from apps.catalog.models import Brand, Product
        fields = {f.name for f in Brand._meta.get_fields()}
        self.assertIn("name_en", fields)
        self.assertIn("name_uk", fields)
        pfields = {f.name for f in Product._meta.get_fields()}
        self.assertIn("description_en", pfields)
        self.assertIn("location_uk", pfields)

from .models import (
    Brand,
    Category,
    Condition,
    FuelType,
    Product,
    Transmission,
    VehicleSpec,
)


class ProductFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.bmw = Brand.objects.create(name="BMW", slug="bmw")
        cls.audi = Brand.objects.create(name="Audi", slug="audi")
        cls.sedan = Category.objects.create(name="Sedan", slug="sedan")
        cls.suv = Category.objects.create(name="SUV", slug="suv")

        cls.p1 = Product.objects.create(
            brand=cls.bmw, category=cls.sedan, name="BMW 520d", slug="bmw-520d",
            price=Decimal("20000"), location="Київ",
        )
        VehicleSpec.objects.create(
            product=cls.p1, year=2018, mileage=80000,
            fuel_type=FuelType.DIESEL, transmission=Transmission.AUTOMATIC,
            condition=Condition.USED, vin="WBA12345678901234",
        )
        cls.p2 = Product.objects.create(
            brand=cls.audi, category=cls.suv, name="Audi Q7", slug="audi-q7",
            price=Decimal("40000"), location="Одеса",
        )
        VehicleSpec.objects.create(
            product=cls.p2, year=2021, mileage=20000,
            fuel_type=FuelType.PETROL, transmission=Transmission.AUTOMATIC,
            condition=Condition.NEW,
        )
        cls.url = reverse("catalog:product_list")

    def _results(self, **params):
        return list(self.client.get(self.url, params).context["products"])

    def test_filter_by_brand_slug(self):
        self.assertEqual(self._results(brand="bmw"), [self.p1])

    def test_filter_by_category(self):
        self.assertEqual(self._results(category="suv"), [self.p2])

    def test_price_range(self):
        self.assertEqual(self._results(price_min="30000"), [self.p2])
        self.assertEqual(self._results(price_max="25000"), [self.p1])

    def test_year_range(self):
        self.assertEqual(self._results(year_max="2019"), [self.p1])
        self.assertEqual(self._results(year_min="2020"), [self.p2])

    def test_mileage_range(self):
        self.assertEqual(self._results(mileage_max="50000"), [self.p2])

    def test_fuel_checkbox(self):
        self.assertEqual(self._results(fuel="petrol"), [self.p2])

    def test_condition_checkbox(self):
        self.assertEqual(self._results(condition="new"), [self.p2])

    def test_search_by_name(self):
        self.assertEqual(self._results(q="Q7"), [self.p2])

    def test_search_by_vin(self):
        self.assertEqual(self._results(q="WBA12345"), [self.p1])

    def test_location_partial(self):
        self.assertEqual(self._results(location="одеса"), [self.p2])

    def test_sort_price_desc(self):
        self.assertEqual(self._results(sort="-price"), [self.p2, self.p1])

    def test_sort_price_asc(self):
        self.assertEqual(self._results(sort="price"), [self.p1, self.p2])

    def test_combined_filters(self):
        self.assertEqual(
            self._results(brand="audi", fuel="petrol", year_min="2020"), [self.p2]
        )

    def test_inactive_excluded(self):
        Product.objects.create(brand=self.bmw, name="Hidden", slug="hidden", is_active=False)
        self.assertEqual(len(self._results()), 2)


class AutocompleteTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.bmw = Brand.objects.create(name="BMW", slug="bmw")
        cls.merc = Brand.objects.create(name="Mercedes-Benz", slug="mercedes-benz")
        Product.objects.create(brand=cls.bmw, name="x", slug="x", location="Львів")
        Product.objects.create(brand=cls.merc, name="y", slug="y", location="Київ")

    def test_make_autocomplete_partial(self):
        data = self.client.get(reverse("catalog:make_autocomplete"), {"q": "mer"}).json()
        self.assertEqual(data["results"], [{"name": "Mercedes-Benz", "value": "mercedes-benz"}])

    def test_make_autocomplete_empty_query_returns_all(self):
        data = self.client.get(reverse("catalog:make_autocomplete")).json()
        self.assertEqual(len(data["results"]), 2)

    def test_city_autocomplete_partial(self):
        data = self.client.get(reverse("catalog:city_autocomplete"), {"q": "льв"}).json()
        self.assertEqual(data["results"], [{"name": "Львів", "value": "Львів"}])

    def test_city_autocomplete_distinct(self):
        Product.objects.create(brand=self.bmw, name="z", slug="z", location="Київ")
        data = self.client.get(reverse("catalog:city_autocomplete"), {"q": "ки"}).json()
        self.assertEqual(data["results"], [{"name": "Київ", "value": "Київ"}])


class ProductImageValidationTests(TestCase):
    def test_svg_rejected_for_product_image(self):
        brand = Brand.objects.create(name="B", slug="b")
        product = Product(
            brand=brand, name="P", slug="p",
            image=SimpleUploadedFile("x.svg", b"<svg></svg>", content_type="image/svg+xml"),
        )
        with self.assertRaises(ValidationError):
            product.full_clean()

    def test_png_accepted_for_product_image(self):
        brand = Brand.objects.create(name="B2", slug="b2")
        product = Product(
            brand=brand, name="P2", slug="p2",
            image=SimpleUploadedFile("x.png", b"\x89PNG", content_type="image/png"),
        )
        # full_clean must not raise on the image field (extension allowed).
        product.full_clean()


class BackfillUkTests(TestCase):
    def test_backfill_copies_base_into_uk(self):
        from django.db import connection

        from apps.catalog.migrations import _bilingua_backfill  # created in Task 2 Step 3
        from apps.catalog.models import Brand

        b = Brand.objects.create(name="Acme", slug="acme")
        # Simulate legacy data: base column set, both translations empty.
        with connection.cursor() as cur:
            cur.execute(
                "UPDATE catalog_brand SET name='Сила', name_en=NULL, name_uk=NULL WHERE id=%s",
                [b.id],
            )
        _bilingua_backfill.backfill(connection, [("catalog_brand", ["name"])])
        with connection.cursor() as cur:
            cur.execute("SELECT name_uk, name_en FROM catalog_brand WHERE id=%s", [b.id])
            name_uk, name_en = cur.fetchone()
        self.assertEqual(name_uk, "Сила")
        self.assertIsNone(name_en)


class ContentFallbackTests(TestCase):
    def test_uk_only_content_falls_back_under_english(self):
        from django.utils import translation

        from apps.catalog.models import Brand

        b = Brand.objects.create(slug="b1")
        b.name_uk = "Сила"
        b.name_en = ""
        b.save()
        b.refresh_from_db()
        with translation.override("uk"):
            self.assertEqual(b.name, "Сила")
        with translation.override("en"):
            self.assertEqual(b.name, "Сила")  # en empty → fallback to uk

    def test_english_value_wins_under_english(self):
        from django.utils import translation

        from apps.catalog.models import Brand

        b = Brand.objects.create(slug="b2")
        b.name_uk = "Сила"
        b.name_en = "Power"
        b.save()
        b.refresh_from_db()
        with translation.override("en"):
            self.assertEqual(b.name, "Power")
        with translation.override("uk"):
            self.assertEqual(b.name, "Сила")
