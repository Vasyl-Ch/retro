# Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close confirmed security, correctness, and cheap-performance issues in the `distributor` Django project without deep data-model changes or large refactors.

**Architecture:** Add two small reusable utilities in `apps/core` (an HTML sanitizer and image-upload validators), wire them into existing models, add a production-config guard, paginate the vacancy list, and add DB indexes. Behavioral changes are test-first (TDD). Migrations are additive and reversible.

**Tech Stack:** Django 5.2, PostgreSQL, `bleach<5.0` (already in `requirements.txt` and installed in the image), `django-modeltranslation`, `django-summernote`, `django-solo`.

## Global Constraints

- **Python/Django:** Django `>=5.2,<5.3`. Match existing code style (type hints, `gettext_lazy as _` for model strings).
- **Dependencies:** Do NOT add new packages. `bleach<5.0` is already declared/installed — use it as-is (4.x API: `bleach.clean(text, tags=[...], attributes={...}, protocols=[...], strip=True)`).
- **Settings:** Run management commands and tests with `--settings=config.settings.development`. Inside Docker the env var is already set; the host equivalent is:
  `docker compose -f docker-compose.dev.yml exec web python manage.py <cmd>`
  Plan steps below show the bare `python manage.py ...` form — prefix with the Docker wrapper if not running inside the container.
- **modeltranslation:** `SiteSettings` is registered for translation. Do not remove/rename its translated fields. The sanitizer and validators must not break translated columns (the content models touched here are not yet translated).
- **Commits:** One commit per task (after its tests pass). Conventional-commit prefixes (`feat:`, `fix:`, `perf:`, `test:`, `chore:`).
- **Test runner:** `python manage.py test <app.path> --settings=config.settings.development`.

**Current latest migrations (for reference):** content `0002`, vacancies `0004`, catalog `0003`, core `0010`. `apps/core` has **no** `tests.py` yet — Task 1 creates it.

---

### Task 1: Production config guard (SECRET_KEY / ALLOWED_HOSTS)

**Files:**
- Create: `apps/core/conf_checks.py`
- Create: `apps/core/tests.py`
- Modify: `config/settings/production.py`

**Interfaces:**
- Produces: `apps.core.conf_checks.assert_production_secret(secret_key: str | None) -> None`, `assert_allowed_hosts(allowed_hosts: list[str]) -> None`, constant `INSECURE_SECRET_KEY: str`.

- [ ] **Step 1: Write the failing test** — create `apps/core/tests.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.core.tests.ProductionSecretGuardTests --settings=config.settings.development`
Expected: FAIL — `ModuleNotFoundError`/`ImportError: cannot import name ... from apps.core.conf_checks`.

- [ ] **Step 3: Write minimal implementation** — create `apps/core/conf_checks.py`:

```python
"""Production configuration guards (fail fast on insecure defaults)."""

from django.core.exceptions import ImproperlyConfigured

INSECURE_SECRET_KEY = "django-insecure-change-me"


def assert_production_secret(secret_key: str | None) -> None:
    """Raise if SECRET_KEY is missing or still the insecure development default."""
    if not secret_key or secret_key == INSECURE_SECRET_KEY:
        raise ImproperlyConfigured(
            "SECRET_KEY must be set to a unique secret value in production "
            "(the insecure development default is not allowed)."
        )


def assert_allowed_hosts(allowed_hosts: list[str]) -> None:
    """Raise if ALLOWED_HOSTS is empty (every host would be rejected with 400)."""
    if not allowed_hosts:
        raise ImproperlyConfigured(
            "ALLOWED_HOSTS must be set in production (received an empty list)."
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python manage.py test apps.core.tests --settings=config.settings.development`
Expected: PASS (6 tests).

- [ ] **Step 5: Wire guards into production settings** — append to `config/settings/production.py` (after the security block, end of file):

```python
from apps.core.conf_checks import (  # noqa: E402
    assert_allowed_hosts,
    assert_production_secret,
)

assert_production_secret(SECRET_KEY)  # noqa: F405
assert_allowed_hosts(ALLOWED_HOSTS)  # noqa: F405
```

- [ ] **Step 6: Verify dev settings still load**

Run: `python manage.py check --settings=config.settings.development`
Expected: `System check identified no issues`.

- [ ] **Step 7: Commit**

```bash
git add apps/core/conf_checks.py apps/core/tests.py config/settings/production.py
git commit -m "fix: fail fast on insecure SECRET_KEY / empty ALLOWED_HOSTS in production"
```

---

### Task 2: HTML sanitizer utility

**Files:**
- Create: `apps/core/sanitizer.py`
- Modify: `apps/core/tests.py`

**Interfaces:**
- Produces: `apps.core.sanitizer.sanitize_html(value: str | None) -> str`, plus module constants `ALLOWED_TAGS`, `ALLOWED_ATTRIBUTES`, `ALLOWED_PROTOCOLS`.

- [ ] **Step 1: Write the failing test** — add to `apps/core/tests.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.core.tests.SanitizeHtmlTests --settings=config.settings.development`
Expected: FAIL — `ImportError: cannot import name 'sanitize_html'`.

- [ ] **Step 3: Write minimal implementation** — create `apps/core/sanitizer.py`:

```python
"""HTML sanitization for rich-text (Summernote) content.

Staff-entered HTML is rendered with ``|safe`` in templates, so it must be
reduced to a strict allow-list before storage to prevent stored XSS.
"""

import bleach

ALLOWED_TAGS = [
    "p", "br", "span", "div",
    "h2", "h3", "h4",
    "strong", "b", "em", "i", "u", "s",
    "ul", "ol", "li",
    "blockquote", "hr",
    "a", "img",
    "table", "thead", "tbody", "tr", "th", "td",
]

ALLOWED_ATTRIBUTES = {
    "*": ["class"],
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "width", "height"],
    "td": ["colspan", "rowspan"],
    "th": ["colspan", "rowspan"],
}

# ``data:`` is allowed for <img> (Summernote inlines pasted images as base64);
# <img> cannot execute script even with an SVG data URI. ``javascript:`` is excluded.
ALLOWED_PROTOCOLS = ["http", "https", "mailto", "data"]


def sanitize_html(value: str | None) -> str:
    """Return *value* reduced to the allow-list; disallowed tags are stripped."""
    if not value:
        return ""
    return bleach.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python manage.py test apps.core.tests.SanitizeHtmlTests --settings=config.settings.development`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add apps/core/sanitizer.py apps/core/tests.py
git commit -m "feat: add bleach-based HTML sanitizer for rich-text content"
```

---

### Task 3: Sanitize News/Promo content on save + backfill existing rows

**Files:**
- Modify: `apps/content/models.py` (News.save ~45-48, Promo.save ~78-81)
- Modify: `apps/content/tests.py`
- Create (via `makemigrations --empty`): `apps/content/migrations/0003_sanitize_existing_html.py`

**Interfaces:**
- Consumes: `apps.core.sanitizer.sanitize_html` (Task 2).

- [ ] **Step 1: Write the failing test** — replace the stub `apps/content/tests.py` with:

```python
from django.test import TestCase
from django.utils import timezone

from .models import News, Promo


class NewsSanitizationTests(TestCase):
    def test_script_stripped_on_save(self):
        news = News.objects.create(
            title="T", preview="p",
            content="<p>ok</p><script>alert(1)</script>",
            published_at=timezone.now(),
        )
        news.refresh_from_db()
        self.assertNotIn("<script", news.content)
        self.assertIn("<p>ok</p>", news.content)


class PromoSanitizationTests(TestCase):
    def test_script_stripped_on_save(self):
        promo = Promo.objects.create(
            title="T", description="<p>ok</p><script>alert(1)</script>",
        )
        promo.refresh_from_db()
        self.assertNotIn("<script", promo.description)
        self.assertIn("<p>ok</p>", promo.description)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.content --settings=config.settings.development`
Expected: FAIL — `<script` still present in saved content.

- [ ] **Step 3: Implement save-time sanitization** — in `apps/content/models.py` add the import near the top:

```python
from apps.core.sanitizer import sanitize_html
```

Update `News.save`:

```python
    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.title)
        self.content = sanitize_html(self.content)
        super().save(*args, **kwargs)
```

Update `Promo.save`:

```python
    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.title)
        self.description = sanitize_html(self.description)
        super().save(*args, **kwargs)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python manage.py test apps.content --settings=config.settings.development`
Expected: PASS.

- [ ] **Step 5: Create the backfill data migration**

Run: `python manage.py makemigrations content --empty --name sanitize_existing_html --settings=config.settings.development`

Then replace the generated file body with:

```python
from django.db import migrations


def sanitize_existing(apps, schema_editor):
    from apps.core.sanitizer import sanitize_html

    News = apps.get_model("content", "News")
    Promo = apps.get_model("content", "Promo")
    for obj in News.objects.all():
        cleaned = sanitize_html(obj.content)
        if cleaned != obj.content:
            obj.content = cleaned
            obj.save(update_fields=["content"])
    for obj in Promo.objects.all():
        cleaned = sanitize_html(obj.description)
        if cleaned != obj.description:
            obj.description = cleaned
            obj.save(update_fields=["description"])


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0002_alter_banner_options_alter_news_options_and_more"),
    ]
    operations = [
        migrations.RunPython(sanitize_existing, migrations.RunPython.noop),
    ]
```

(Keep the `dependencies` value that `makemigrations` generated — it should match the latest content migration.)

- [ ] **Step 6: Apply and verify migrations**

Run: `python manage.py migrate content --settings=config.settings.development`
Expected: applies `0003_sanitize_existing_html` with no error.

- [ ] **Step 7: Commit**

```bash
git add apps/content/models.py apps/content/tests.py apps/content/migrations/0003_sanitize_existing_html.py
git commit -m "fix: sanitize News/Promo HTML on save and backfill existing rows"
```

---

### Task 4: Sanitize Vacancy rich-text on save + backfill existing rows

**Files:**
- Modify: `apps/vacancies/models.py` (Vacancy.save ~36-39)
- Modify: `apps/vacancies/tests.py`
- Create (via `makemigrations --empty`): `apps/vacancies/migrations/0005_sanitize_existing_html.py`

**Interfaces:**
- Consumes: `apps.core.sanitizer.sanitize_html` (Task 2).

- [ ] **Step 1: Write the failing test** — replace the stub `apps/vacancies/tests.py` with:

```python
from django.test import TestCase

from .models import Vacancy


class VacancySanitizationTests(TestCase):
    def test_script_and_handlers_stripped_on_save(self):
        v = Vacancy.objects.create(
            title="Dev",
            description="<p>job</p><script>alert(1)</script>",
            requirements='<ul><li>x</li></ul><img src="http://a/b.png" onerror="alert(1)">',
            conditions="<p>nice</p>",
        )
        v.refresh_from_db()
        self.assertNotIn("<script", v.description)
        self.assertNotIn("onerror", v.requirements)
        self.assertIn("<li>x</li>", v.requirements)
        self.assertIn("<p>nice</p>", v.conditions)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.vacancies --settings=config.settings.development`
Expected: FAIL — `<script`/`onerror` still present.

- [ ] **Step 3: Implement save-time sanitization** — in `apps/vacancies/models.py` add import near the top:

```python
from apps.core.sanitizer import sanitize_html
```

Update `Vacancy.save`:

```python
    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.title)
        self.description = sanitize_html(self.description)
        self.requirements = sanitize_html(self.requirements)
        self.conditions = sanitize_html(self.conditions)
        super().save(*args, **kwargs)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python manage.py test apps.vacancies --settings=config.settings.development`
Expected: PASS.

- [ ] **Step 5: Create the backfill data migration**

Run: `python manage.py makemigrations vacancies --empty --name sanitize_existing_html --settings=config.settings.development`

Replace the generated file body with:

```python
from django.db import migrations


def sanitize_existing(apps, schema_editor):
    from apps.core.sanitizer import sanitize_html

    Vacancy = apps.get_model("vacancies", "Vacancy")
    for obj in Vacancy.objects.all():
        changed = False
        for field in ("description", "requirements", "conditions"):
            cleaned = sanitize_html(getattr(obj, field))
            if cleaned != getattr(obj, field):
                setattr(obj, field, cleaned)
                changed = True
        if changed:
            obj.save(update_fields=["description", "requirements", "conditions"])


class Migration(migrations.Migration):
    dependencies = [
        ("vacancies", "0004_alter_vacancy_city_alter_vacancy_conditions_and_more"),
    ]
    operations = [
        migrations.RunPython(sanitize_existing, migrations.RunPython.noop),
    ]
```

(Keep the `dependencies` value `makemigrations` generated.)

- [ ] **Step 6: Apply and verify migrations**

Run: `python manage.py migrate vacancies --settings=config.settings.development`
Expected: applies `0005_sanitize_existing_html` with no error.

- [ ] **Step 7: Commit**

```bash
git add apps/vacancies/models.py apps/vacancies/tests.py apps/vacancies/migrations/0005_sanitize_existing_html.py
git commit -m "fix: sanitize Vacancy rich-text on save and backfill existing rows"
```

---

### Task 5: Image upload validators utility

**Files:**
- Modify: `apps/core/validators.py`
- Modify: `apps/core/tests.py`

**Interfaces:**
- Produces: `validate_image_size(file) -> None`, lists `raster_image_validators`, `branding_image_validators`, constants `MAX_IMAGE_MB`, `MAX_IMAGE_BYTES`, `RASTER_EXTENSIONS`, `BRANDING_EXTENSIONS`.

- [ ] **Step 1: Write the failing test** — add to `apps/core/tests.py`:

```python
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.core.validators import (
    MAX_IMAGE_BYTES,
    branding_image_validators,
    raster_image_validators,
    validate_image_size,
)


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.core.tests.ImageValidatorTests --settings=config.settings.development`
Expected: FAIL — `ImportError` for the new names.

- [ ] **Step 3: Implement validators** — `apps/core/validators.py` currently contains only `validate_contactable`. Add the new imports at the top and append the new code (keep `validate_contactable` intact):

```python
from django.core.validators import FileExtensionValidator
from django.template.defaultfilters import filesizeformat
```

```python
MAX_IMAGE_MB = 5
MAX_IMAGE_BYTES = MAX_IMAGE_MB * 1024 * 1024

RASTER_EXTENSIONS = ["jpg", "jpeg", "png", "webp", "gif"]
BRANDING_EXTENSIONS = RASTER_EXTENSIONS + ["svg"]


def validate_image_size(file) -> None:
    """Reject uploads larger than MAX_IMAGE_BYTES."""
    size = getattr(file, "size", None)
    if size and size > MAX_IMAGE_BYTES:
        raise ValidationError(
            _("Файл завеликий (%(size)s). Максимум — %(max)s.")
            % {"size": filesizeformat(size), "max": filesizeformat(MAX_IMAGE_BYTES)}
        )


raster_image_validators = [
    FileExtensionValidator(allowed_extensions=RASTER_EXTENSIONS),
    validate_image_size,
]
branding_image_validators = [
    FileExtensionValidator(allowed_extensions=BRANDING_EXTENSIONS),
    validate_image_size,
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python manage.py test apps.core.tests.ImageValidatorTests --settings=config.settings.development`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add apps/core/validators.py apps/core/tests.py
git commit -m "feat: add image upload validators (extension allow-list + size cap)"
```

---

### Task 6: Wire image validators into model fields

**Files:**
- Modify: `apps/core/models.py` (brand_logo, favicon, side_logo_left, side_logo_right → branding; PageBackground.image → raster)
- Modify: `apps/content/models.py` (Banner.background, News.image, Promo.image → raster)
- Modify: `apps/catalog/models.py` (Brand.logo, Product.image, ProductImage.image → raster)
- Modify: `apps/vacancies/models.py` (Vacancy.cover_image, VacancyImage.image → raster)
- Modify: `apps/catalog/tests.py`
- Create (via `makemigrations`): one migration per app (core/content/catalog/vacancies).

**Interfaces:**
- Consumes: `raster_image_validators`, `branding_image_validators` (Task 5).

- [ ] **Step 1: Write the failing test** — add to `apps/catalog/tests.py`:

```python
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .models import Brand, Product


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.catalog.tests.ProductImageValidationTests --settings=config.settings.development`
Expected: FAIL — `test_svg_rejected_for_product_image` does not raise (no validators yet).

- [ ] **Step 3: Wire validators into fields**

Add import to the top of `apps/core/models.py`, `apps/content/models.py`, `apps/catalog/models.py`, `apps/vacancies/models.py`:

```python
from apps.core.validators import branding_image_validators, raster_image_validators
```

(For files that only use one set, import only that name.)

Then add `validators=...` to each `ImageField`:

- `apps/core/models.py`:
  - `brand_logo` → `validators=branding_image_validators`
  - `favicon` → `validators=branding_image_validators`
  - `side_logo_left` → `validators=branding_image_validators`
  - `side_logo_right` → `validators=branding_image_validators`
  - `PageBackground.image` → `validators=raster_image_validators`
- `apps/content/models.py`: `Banner.background`, `News.image`, `Promo.image` → `validators=raster_image_validators`
- `apps/catalog/models.py`: `Brand.logo`, `Product.image`, `ProductImage.image` → `validators=raster_image_validators`
- `apps/vacancies/models.py`: `Vacancy.cover_image`, `VacancyImage.image` → `validators=raster_image_validators`

Example (core branding field):

```python
    brand_logo = models.ImageField(
        _("Логотип"), upload_to="branding/", blank=True, null=True,
        validators=branding_image_validators,
    )
```

Example (catalog raster field):

```python
    image = models.ImageField(
        _("Фото"), upload_to="products/", validators=raster_image_validators
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python manage.py test apps.catalog.tests.ProductImageValidationTests --settings=config.settings.development`
Expected: PASS (2 tests).

- [ ] **Step 5: Generate and apply migrations**

Run: `python manage.py makemigrations core content catalog vacancies --settings=config.settings.development`
Expected: one `alter` migration per app (validator change only — no DB-level SQL beyond field state).

Run: `python manage.py migrate --settings=config.settings.development`
Expected: applies cleanly.

- [ ] **Step 6: Verify no stray migrations remain**

Run: `python manage.py makemigrations --check --dry-run --settings=config.settings.development`
Expected: `No changes detected`.

- [ ] **Step 7: Commit**

```bash
git add apps/core/models.py apps/content/models.py apps/catalog/models.py apps/vacancies/models.py apps/catalog/tests.py apps/*/migrations/*.py
git commit -m "fix: validate image uploads (raster everywhere, SVG only for branding)"
```

---

### Task 7: Paginate the vacancy list

**Files:**
- Modify: `apps/vacancies/views.py:6-12`
- Modify: `templates/vacancies/list.html` (add pagination include after the grid, ~line 56)
- Modify: `apps/vacancies/tests.py`

- [ ] **Step 1: Write the failing test** — add to `apps/vacancies/tests.py`:

```python
from django.urls import reverse


class VacancyListPaginationTests(TestCase):
    def test_list_paginates_at_12(self):
        for i in range(15):
            Vacancy.objects.create(title=f"V{i}", description="<p>d</p>")
        resp = self.client.get(reverse("vacancies:list"))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["is_paginated"])
        self.assertEqual(len(resp.context["vacancies"]), 12)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.vacancies.tests.VacancyListPaginationTests --settings=config.settings.development`
Expected: FAIL — `is_paginated` is `False` / 15 items returned.

- [ ] **Step 3: Add `paginate_by`** — in `apps/vacancies/views.py`:

```python
class VacancyListView(ListView):
    model = Vacancy
    template_name = "vacancies/list.html"
    context_object_name = "vacancies"
    paginate_by = 12

    def get_queryset(self) -> QuerySet:
        return Vacancy.objects.filter(is_active=True)
```

- [ ] **Step 4: Add the pagination control to the template** — in `templates/vacancies/list.html`, insert the include between the closing `</div>` of the grid (line 56) and the `{% else %}` (line 57):

```django
    </div>
    {% include 'partials/_pagination.html' %}
    {% else %}
```

(The existing grid loop already iterates `vacancies`, which becomes the current page's slice once `paginate_by` is set. `_pagination.html` reads `page_obj`/`paginator` from context automatically.)

- [ ] **Step 5: Run test to verify it passes**

Run: `python manage.py test apps.vacancies.tests.VacancyListPaginationTests --settings=config.settings.development`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/vacancies/views.py templates/vacancies/list.html apps/vacancies/tests.py
git commit -m "fix: paginate vacancy list (12 per page)"
```

---

### Task 8: Add db_index to is_active fields

**Files:**
- Modify: `apps/catalog/models.py:47,78,131`, `apps/content/models.py:15,33,68`, `apps/vacancies/models.py:23`, `apps/core/models.py:228`
- Create (via `makemigrations`): one migration per app.

- [ ] **Step 1: Add `db_index=True` to each `is_active` field**

Edit each field to add `db_index=True`:

```python
# catalog: Brand, Category, Product
is_active = models.BooleanField(_("Активний"), default=True, db_index=True)   # Brand
is_active = models.BooleanField(_("Активна"), default=True, db_index=True)    # Category
is_active = models.BooleanField(_("Активний"), default=True, db_index=True)   # Product

# content: Banner, News (verbose "Опублікована"), Promo
is_active = models.BooleanField(_("Активний"), default=True, db_index=True)   # Banner
is_active = models.BooleanField(_("Опублікована"), default=True, db_index=True)  # News
is_active = models.BooleanField(_("Активна"), default=True, db_index=True)    # Promo

# vacancies: Vacancy
is_active = models.BooleanField(_("Активна"), default=True, db_index=True)

# core: PageBackground
is_active = models.BooleanField(_("Активний"), default=True, db_index=True)
```

(Keep each field's existing verbose_name string exactly as-is; only append `db_index=True`.)

- [ ] **Step 2: Generate migrations**

Run: `python manage.py makemigrations catalog content vacancies core --settings=config.settings.development`
Expected: one `alter_field` migration per app adding the index.

- [ ] **Step 3: Apply migrations**

Run: `python manage.py migrate --settings=config.settings.development`
Expected: applies cleanly (`CREATE INDEX` per field).

- [ ] **Step 4: Verify no stray migrations remain**

Run: `python manage.py makemigrations --check --dry-run --settings=config.settings.development`
Expected: `No changes detected`.

- [ ] **Step 5: Run the full suite to confirm nothing broke**

Run: `python manage.py test --settings=config.settings.development`
Expected: PASS (all tests).

- [ ] **Step 6: Commit**

```bash
git add apps/catalog/models.py apps/content/models.py apps/vacancies/models.py apps/core/models.py apps/*/migrations/*.py
git commit -m "perf: index is_active on Brand/Category/Product/Banner/News/Promo/Vacancy/PageBackground"
```

---

### Task 9: Narrow the page_background query

**Files:**
- Modify: `apps/core/context_processors.py:26-30`
- Modify: `apps/core/tests.py`

- [ ] **Step 1: Write the failing test** — add to `apps/core/tests.py`:

```python
from django.test import TestCase as DBTestCase
from django.urls import ResolverMatch
from django.test import RequestFactory

from apps.core.context_processors import page_background
from apps.core.models import PageBackground


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
```

- [ ] **Step 2: Run test to verify it fails or passes**

Run: `python manage.py test apps.core.tests.PageBackgroundContextTests --settings=config.settings.development`
Expected: these pass against current code too (behavior is unchanged) — they are a **regression guard** for the optimization. If any fail, fix the test setup before refactoring.

- [ ] **Step 3: Narrow the query** — in `apps/core/context_processors.py`, replace the `try` block (lines ~26-30):

```python
    keys = [PageBackground.SITE_KEY]
    if current_key:
        keys.append(current_key)

    try:
        qs = PageBackground.objects.filter(is_active=True, page_key__in=keys)
        backgrounds = {bg.page_key: bg for bg in qs}
    except (OperationalError, ProgrammingError):
        return {"page_background": None, "page_background_overlay": 0}
```

(Leave the selection logic below it — current_key → SITE_KEY → none — unchanged.)

- [ ] **Step 4: Run test to verify it still passes**

Run: `python manage.py test apps.core.tests.PageBackgroundContextTests --settings=config.settings.development`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add apps/core/context_processors.py apps/core/tests.py
git commit -m "perf: fetch only the current + site page backgrounds, not all rows"
```

---

## Final Verification

- [ ] Run the whole suite: `python manage.py test --settings=config.settings.development` → all PASS.
- [ ] `python manage.py check --settings=config.settings.development` → no issues.
- [ ] `python manage.py makemigrations --check --dry-run --settings=config.settings.development` → `No changes detected`.
- [ ] Manual smoke (optional): open `/admin/`, upload a `.txt` as a product image → rejected; paste `<script>` into a News body → stripped after save; open `/vacancies/` with 13+ vacancies → pagination control shows.

## Self-Review notes (author)

- **Spec coverage:** S1→Task 1, S2→Tasks 2-4, S3→Tasks 5-6, C1→Task 7, P1→Task 8, P2→Task 9. All spec items mapped.
- **Type consistency:** `sanitize_html`, `raster_image_validators`, `branding_image_validators`, `validate_image_size`, `assert_production_secret`, `assert_allowed_hosts`, `INSECURE_SECRET_KEY`, `MAX_IMAGE_BYTES` used identically across producing and consuming tasks.
- **No placeholders:** every code/command step is concrete. Data-migration `dependencies` are auto-filled by `makemigrations --empty`; the example values match the current latest migrations.
