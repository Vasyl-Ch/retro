# Constructor (Direction 3) — Visual Appearance Editor — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let an admin customize site colors, header/footer transparency, and background position with a live preview, building on the existing `data-theme`/CSS-variable theming.

**Architecture:** A small `appearance` bounded context (`apps/core/appearance/`) holds a pure domain core (coloraide colour ramp + value objects) and one application service. The Django models (`SiteSettings`, `PageBackground`) are infrastructure; the context processor + `base.html` render server-side; an admin "Appearance" page drives a live `<iframe>` preview via `postMessage`. The domain service is the single source of truth for both SSR and the preview endpoint.

**Tech Stack:** Django 5.2, **coloraide** (OKLCH ramp), **django-colorfield** (ColorField + admin picker), django-solo, django-modeltranslation.

## Global Constraints

- **Spec:** `docs/superpowers/specs/2026-06-25-constructor-design.md`.
- **Branch:** `constructor` (already checked out).
- **Tests in Docker:** `MSYS_NO_PATHCONV=1 docker compose -f docker-compose.dev.yml exec -T web python manage.py <cmd> --settings=config.settings.development` (run from `d:\retro`; app labels, no `distributor.` prefix). The `MSYS_NO_PATHCONV=1` prefix is REQUIRED from Git Bash so container paths aren't mangled. Bring the stack up with `WEB_PORT=8008 DB_PORT=5438 docker compose -f docker-compose.dev.yml up -d` (Docker Desktop may need a manual start).
- **DRY/SOLID/DDD (pragmatic):** colour math lives only in `appearance/palette.py`; the CSS var map is produced once by `AppearanceTheme.to_css_map()` and reused by SSR + preview. Domain code imports no Django.
- **New deps allowed (only these):** `coloraide`, `django-colorfield`.
- **Appearance fields are NOT translated** (non-textual) — do not register them with modeltranslation.
- **Var format:** `--primary-*` are space-separated RGB triplets (e.g. `37 99 235`) to match `rgb(var(--primary-600))`; `--chrome-bg`/`--chrome-text` are full colours; `--chrome-alpha` is a 0–1 number.

---

### Task 1: Add dependencies + register colorfield

**Files:**
- Modify: `distributor/requirements.txt`
- Modify: `distributor/config/settings/base.py` (INSTALLED_APPS)

**Interfaces:**
- Produces: importable `coloraide` and `colorfield` packages in the container; `colorfield` in INSTALLED_APPS.

- [ ] **Step 1: Add the two dependencies** — append to `distributor/requirements.txt`:

```
coloraide>=4.0
django-colorfield>=0.11
```

- [ ] **Step 2: Register colorfield** — in `distributor/config/settings/base.py`, add `"colorfield",` to `INSTALLED_APPS` (with the other third-party apps, before the local `apps.*` entries).

- [ ] **Step 3: Install into the running container**

Run: `MSYS_NO_PATHCONV=1 docker compose -f docker-compose.dev.yml exec -T web pip install "coloraide>=4.0" "django-colorfield>=0.11"`
Expected: both install successfully.
(Note: the image's requirements are baked at build; this `pip install` makes them available now. A later `docker compose build web` will pick them up from requirements.txt for fresh builds.)

- [ ] **Step 4: Verify imports + system check**

Run: `MSYS_NO_PATHCONV=1 docker compose -f docker-compose.dev.yml exec -T web python -c "import coloraide, colorfield; print('ok')"`
Expected: `ok`.
Run: `MSYS_NO_PATHCONV=1 docker compose -f docker-compose.dev.yml exec -T web python manage.py check --settings=config.settings.development`
Expected: `System check identified no issues`.

- [ ] **Step 5: Commit**

```bash
git add distributor/requirements.txt distributor/config/settings/base.py
git commit -m "build(constructor): add coloraide + django-colorfield deps"
```

---

### Task 2: Domain — colour ramp + value objects (pure)

**Files:**
- Create: `distributor/apps/core/appearance/__init__.py` (empty)
- Create: `distributor/apps/core/appearance/palette.py`
- Test: `distributor/apps/core/tests_appearance.py`

**Interfaces:**
- Produces:
  - `RAMP_STEPS: tuple[int,...]`
  - `Palette(steps: dict[int,str])` with `.to_css_vars(prefix="--primary") -> dict[str,str]`
  - `generate_primary_ramp(accent_hex: str) -> Palette`
  - `AppearanceTheme(primary: Palette|None=None, chrome_bg: str="", chrome_text: str="", chrome_alpha: float|None=None)` with `.is_empty() -> bool`, `.to_css_map() -> dict[str,str]`, `.to_css_declarations() -> str`

- [ ] **Step 1: Write the failing tests** — create `distributor/apps/core/tests_appearance.py`:

```python
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `MSYS_NO_PATHCONV=1 docker compose -f docker-compose.dev.yml exec -T web python manage.py test apps.core.tests_appearance --settings=config.settings.development`
Expected: FAIL — `ModuleNotFoundError: apps.core.appearance`.

- [ ] **Step 3: Create the package** — create empty `distributor/apps/core/appearance/__init__.py`.

- [ ] **Step 4: Create `distributor/apps/core/appearance/palette.py`:**

```python
"""Appearance domain: derive a colour ramp + CSS variables from admin choices.

Pure (no Django). Colour math via coloraide (OKLCH) so we do not hand-roll
tint/shade curves. Single source of truth for the CSS the site emits.
"""
from __future__ import annotations

from dataclasses import dataclass

from coloraide import Color

RAMP_STEPS = (50, 100, 200, 300, 400, 500, 600, 700, 800, 900)

# (OKLCH lightness, chroma scale) per step. 600 is the brand anchor (replaced
# with the exact accent below). Mirrors the perceived range of the built-in ramps.
_CURVE = {
    50: (0.971, 0.18), 100: (0.936, 0.30), 200: (0.885, 0.50),
    300: (0.808, 0.70), 400: (0.715, 0.90), 500: (0.637, 1.00),
    600: (0.553, 1.00), 700: (0.470, 0.95), 800: (0.395, 0.85),
    900: (0.322, 0.70),
}


def _triplet(color: Color) -> str:
    srgb = color.convert("srgb").fit()
    r, g, b = (max(0, min(255, round(c * 255))) for c in srgb.coords())
    return f"{r} {g} {b}"


@dataclass(frozen=True)
class Palette:
    steps: dict[int, str]

    def to_css_vars(self, prefix: str = "--primary") -> dict[str, str]:
        return {f"{prefix}-{step}": value for step, value in self.steps.items()}


def generate_primary_ramp(accent_hex: str) -> Palette:
    accent = Color(accent_hex)
    oklch = accent.convert("oklch")
    achromatic = accent.convert("srgb").is_achromatic()
    hue = 0.0 if achromatic else oklch["hue"]
    chroma = 0.0 if achromatic else oklch["chroma"]
    steps: dict[int, str] = {}
    for step in RAMP_STEPS:
        lightness, cscale = _CURVE[step]
        steps[step] = _triplet(Color("oklch", [lightness, chroma * cscale, hue]))
    steps[600] = _triplet(accent)  # exact brand colour at the anchor
    return Palette(steps)


@dataclass(frozen=True)
class AppearanceTheme:
    primary: Palette | None = None
    chrome_bg: str = ""
    chrome_text: str = ""
    chrome_alpha: float | None = None

    def is_empty(self) -> bool:
        return (
            self.primary is None
            and not self.chrome_bg
            and not self.chrome_text
            and self.chrome_alpha is None
        )

    def to_css_map(self) -> dict[str, str]:
        css: dict[str, str] = {}
        if self.primary is not None:
            css.update(self.primary.to_css_vars())
        if self.chrome_bg:
            css["--chrome-bg"] = self.chrome_bg
        if self.chrome_text:
            css["--chrome-text"] = self.chrome_text
        if self.chrome_alpha is not None:
            css["--chrome-alpha"] = f"{self.chrome_alpha:g}"
        return css

    def to_css_declarations(self) -> str:
        return "\n".join(f"{name}: {value};" for name, value in self.to_css_map().items())
```

- [ ] **Step 5: Run to verify it passes**

Run: `MSYS_NO_PATHCONV=1 docker compose -f docker-compose.dev.yml exec -T web python manage.py test apps.core.tests_appearance --settings=config.settings.development`
Expected: PASS (7 tests). If `oklch["hue"]` raises a KeyError on your coloraide version, use `oklch["oklch.hue"]`/`oklch.get("hue")` — confirm via the test.

- [ ] **Step 6: Commit**

```bash
git add distributor/apps/core/appearance/__init__.py distributor/apps/core/appearance/palette.py distributor/apps/core/tests_appearance.py
git commit -m "feat(constructor): appearance domain — coloraide colour ramp + value objects"
```

---

### Task 3: Application service (SSR + preview share one source)

**Files:**
- Create: `distributor/apps/core/appearance/services.py`
- Test: `distributor/apps/core/tests_appearance.py`

**Interfaces:**
- Consumes: `palette.AppearanceTheme`, `palette.generate_primary_ramp`.
- Produces:
  - `build_appearance_css(settings_obj) -> str`
  - `preview_vars(*, accent="", chrome_bg="", chrome_text="", chrome_opacity=100) -> dict[str,str]`

- [ ] **Step 1: Add failing tests** — append to `distributor/apps/core/tests_appearance.py`:

```python
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `MSYS_NO_PATHCONV=1 docker compose -f docker-compose.dev.yml exec -T web python manage.py test apps.core.tests_appearance.AppearanceServiceTests --settings=config.settings.development`
Expected: FAIL — `ModuleNotFoundError: apps.core.appearance.services`.

- [ ] **Step 3: Create `distributor/apps/core/appearance/services.py`:**

```python
"""Application service mapping SiteSettings appearance fields -> CSS.

DRY boundary: both the context processor (server render) and the admin
live-preview endpoint go through here, so they can never diverge.
"""
from __future__ import annotations

from .palette import AppearanceTheme, generate_primary_ramp


def _theme(accent, chrome_bg, chrome_text, chrome_opacity) -> AppearanceTheme:
    primary = generate_primary_ramp(accent) if accent else None
    alpha = None
    if chrome_opacity is not None and int(chrome_opacity) != 100:
        alpha = max(0, min(100, int(chrome_opacity))) / 100
    return AppearanceTheme(
        primary=primary,
        chrome_bg=chrome_bg or "",
        chrome_text=chrome_text or "",
        chrome_alpha=alpha,
    )


def build_appearance_css(settings_obj) -> str:
    """CSS declarations for the SiteSettings singleton (``""`` when unset)."""
    return _theme(
        getattr(settings_obj, "custom_accent", "") or "",
        getattr(settings_obj, "chrome_bg", "") or "",
        getattr(settings_obj, "chrome_text", "") or "",
        getattr(settings_obj, "chrome_opacity", 100),
    ).to_css_declarations()


def preview_vars(*, accent="", chrome_bg="", chrome_text="", chrome_opacity=100) -> dict[str, str]:
    """CSS var map from raw (unsaved) values for the live endpoint; {} on bad input."""
    try:
        return _theme(accent, chrome_bg, chrome_text, chrome_opacity).to_css_map()
    except Exception:
        return {}
```

- [ ] **Step 4: Run to verify it passes**

Run: `MSYS_NO_PATHCONV=1 docker compose -f docker-compose.dev.yml exec -T web python manage.py test apps.core.tests_appearance.AppearanceServiceTests --settings=config.settings.development`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add distributor/apps/core/appearance/services.py distributor/apps/core/tests_appearance.py
git commit -m "feat(constructor): appearance application service (SSR + preview source)"
```

---

### Task 4: Model fields + migration

**Files:**
- Modify: `distributor/apps/core/models.py` (SiteSettings + PageBackground)
- Create (generated): `distributor/apps/core/migrations/000X_appearance_fields.py`
- Test: `distributor/apps/core/tests_appearance.py`

**Interfaces:**
- Consumes: `colorfield.fields.ColorField`.
- Produces: `SiteSettings.custom_accent/chrome_bg/chrome_text/chrome_opacity`; `PageBackground.position/size`.

- [ ] **Step 1: Add failing test** — append to `distributor/apps/core/tests_appearance.py`:

```python
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `MSYS_NO_PATHCONV=1 docker compose -f docker-compose.dev.yml exec -T web python manage.py test apps.core.tests_appearance.AppearanceModelTests --settings=config.settings.development`
Expected: FAIL — `AttributeError`/field errors (fields don't exist).

- [ ] **Step 3: Add imports + fields** — in `distributor/apps/core/models.py`:

At the top, add after the existing imports:

```python
from colorfield.fields import ColorField
from django.core.validators import MaxValueValidator, MinValueValidator
```

Inside `SiteSettings`, add an appearance block (e.g. right after the `theme` field):

```python
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
```

Inside `PageBackground`, add (after `overlay_opacity`):

```python
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
```

- [ ] **Step 4: Generate + apply the migration**

Run: `MSYS_NO_PATHCONV=1 docker compose -f docker-compose.dev.yml exec -T web python manage.py makemigrations core --settings=config.settings.development`
Expected: one migration adding the 6 fields.
Run: `MSYS_NO_PATHCONV=1 docker compose -f docker-compose.dev.yml exec -T web python manage.py migrate --settings=config.settings.development`
Expected: applies cleanly.

- [ ] **Step 5: Run tests + dry-run check**

Run: `MSYS_NO_PATHCONV=1 docker compose -f docker-compose.dev.yml exec -T web python manage.py test apps.core.tests_appearance.AppearanceModelTests --settings=config.settings.development` → PASS.
Run: `MSYS_NO_PATHCONV=1 docker compose -f docker-compose.dev.yml exec -T web python manage.py makemigrations --check --dry-run core --settings=config.settings.development` → `No changes detected`.

- [ ] **Step 6: Commit**

```bash
git add distributor/apps/core/models.py distributor/apps/core/migrations/*appearance*.py distributor/apps/core/tests_appearance.py
git commit -m "feat(constructor): appearance fields on SiteSettings + PageBackground position/size"
```

---

### Task 5: Server-side render (context processors + base.html + tailus.css)

**Files:**
- Modify: `distributor/apps/core/context_processors.py` (`site_settings`, `page_background`)
- Modify: `distributor/templates/base.html`
- Modify: `ada-frontend/assets/css/tailus.css`
- Test: `distributor/apps/core/tests_appearance.py`

**Interfaces:**
- Consumes: `apps.core.appearance.services.build_appearance_css`.
- Produces: template context `appearance_css: str`, `page_background_position: str`, `page_background_size: str`; CSS var `--chrome-alpha` (default 1).

- [ ] **Step 1: Add failing test** — append to `distributor/apps/core/tests_appearance.py`:

```python
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `MSYS_NO_PATHCONV=1 docker compose -f docker-compose.dev.yml exec -T web python manage.py test apps.core.tests_appearance.AppearanceRenderTests --settings=config.settings.development`
Expected: FAIL — no `appearance-overrides` in the response.

- [ ] **Step 3: Extend the context processors** — in `distributor/apps/core/context_processors.py`:

In `site_settings`, change the success return to include the CSS:

```python
def site_settings(request: HttpRequest) -> dict[str, Any]:
    """Expose the SiteSettings singleton + computed appearance CSS in every template."""
    from apps.core.appearance.services import build_appearance_css
    try:
        settings_obj = SiteSettings.get_solo()
    except (OperationalError, ProgrammingError):
        return {"site_settings": None, "appearance_css": ""}
    return {
        "site_settings": settings_obj,
        "appearance_css": build_appearance_css(settings_obj),
    }
```

In `page_background`, add position/size to BOTH return branches. Replace the final `return {...}` with:

```python
    return {
        "page_background": chosen.image.url,
        "page_background_overlay": max(0, min(chosen.overlay_opacity, 90)),
        "page_background_position": chosen.position,
        "page_background_size": chosen.size,
    }
```

And the three early `return {"page_background": None, ...}` lines become:

```python
        return {"page_background": None, "page_background_overlay": 0,
                "page_background_position": "center", "page_background_size": "cover"}
```

- [ ] **Step 4: Inject the override `<style>`** — in `distributor/templates/base.html`, immediately after `{% vite_css %}` (line ~29), add:

```html
    {% if appearance_css %}
    <style id="appearance-overrides">:root[data-theme][data-theme]{ {{ appearance_css }} }</style>
    {% endif %}
```

Then parametrize the background block: replace the two hardcoded lines

```html
        background-size: cover;
        background-position: center;
```

with

```html
        background-size: {{ page_background_size|default:'cover' }};
        background-position: {{ page_background_position|default:'center' }};
```

- [ ] **Step 5: Make chrome alpha-capable** — in `ada-frontend/assets/css/tailus.css`:

Add a base default near the top of the chrome block (just before `.site-nav {` at line ~105):

```css
:root { --chrome-alpha: 1; }
```

Change `.site-nav` `background-color` (line ~106) and `.site-footer` `background-color` (line ~121) to:

```css
    background-color: color-mix(in srgb, var(--chrome-bg), transparent calc((1 - var(--chrome-alpha)) * 100%));
```

(Base colour stays in the theme palettes — only alpha crosses the Python boundary.)

- [ ] **Step 6: Run tests**

Run: `MSYS_NO_PATHCONV=1 docker compose -f docker-compose.dev.yml exec -T web python manage.py test apps.core.tests_appearance.AppearanceRenderTests --settings=config.settings.development`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add distributor/apps/core/context_processors.py distributor/templates/base.html ada-frontend/assets/css/tailus.css distributor/apps/core/tests_appearance.py
git commit -m "feat(constructor): render appearance CSS + background position; alpha-capable chrome"
```

---

### Task 6: Admin Appearance fieldset + live-preview endpoint + JS

**Files:**
- Modify: `distributor/apps/core/admin.py` (SiteSettingsAdmin: fieldset, url, view)
- Modify: `distributor/templates/admin/core/sitesettings/change_form.html` (iframe + controls JS)
- Modify: `distributor/templates/base.html` (preview `postMessage` listener)
- Test: `distributor/apps/core/tests_appearance.py`

**Interfaces:**
- Consumes: `apps.core.appearance.services.preview_vars`.
- Produces: admin URL name `admin:core_sitesettings_preview_css` returning a JSON var map.

- [ ] **Step 1: Add failing tests** — append to `distributor/apps/core/tests_appearance.py`:

```python
from django.contrib.auth import get_user_model
from django.urls import reverse


class AppearancePreviewEndpointTests(_DBTestCase):
    def test_preview_endpoint_returns_var_map_for_staff(self):
        admin = get_user_model().objects.create_superuser("ap", "ap@x.com", "pw")
        self.client.force_login(admin)
        url = reverse("admin:core_sitesettings_preview_css")
        resp = self.client.get(url, {"accent": "#2563eb", "chrome_opacity": "80"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["--primary-600"], "37 99 235")
        self.assertEqual(data["--chrome-alpha"], "0.8")

    def test_preview_endpoint_blocks_anonymous(self):
        url = reverse("admin:core_sitesettings_preview_css")
        resp = self.client.get(url, {"accent": "#2563eb"})
        self.assertIn(resp.status_code, (302, 403))


class AppearanceAdminFormTests(_DBTestCase):
    def test_change_form_shows_appearance_fields(self):
        admin = get_user_model().objects.create_superuser("ap2", "ap2@x.com", "pw")
        self.client.force_login(admin)
        resp = self.client.get(reverse("admin:core_sitesettings_change", args=[1]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "custom_accent")
        self.assertContains(resp, "chrome_opacity")
```

- [ ] **Step 2: Run to verify it fails**

Run: `MSYS_NO_PATHCONV=1 docker compose -f docker-compose.dev.yml exec -T web python manage.py test apps.core.tests_appearance.AppearancePreviewEndpointTests apps.core.tests_appearance.AppearanceAdminFormTests --settings=config.settings.development`
Expected: FAIL — `NoReverseMatch` for `core_sitesettings_preview_css` / fields absent.

- [ ] **Step 3: Add the Appearance fieldset + endpoint** — in `distributor/apps/core/admin.py`:

Add to the top imports:

```python
from django.http import JsonResponse
from apps.core.appearance.services import preview_vars
```

In `SiteSettingsAdmin.get_urls`, add the preview path to `custom`:

```python
            path(
                "preview-css/",
                self.admin_site.admin_view(self.preview_css_view),
                name="core_sitesettings_preview_css",
            ),
```

Add the view method to `SiteSettingsAdmin`:

```python
    def preview_css_view(self, request):
        return JsonResponse(preview_vars(
            accent=request.GET.get("accent", ""),
            chrome_bg=request.GET.get("chrome_bg", ""),
            chrome_text=request.GET.get("chrome_text", ""),
            chrome_opacity=request.GET.get("chrome_opacity", 100) or 100,
        ))
```

Add an Appearance fieldset to `SiteSettingsAdmin.fieldsets` (right after the `General` tuple):

```python
        (_("Appearance (colors & transparency)"), {
            "fields": ("custom_accent", "chrome_bg", "chrome_text", "chrome_opacity"),
            "description": _("Live preview updates below as you change these."),
        }),
```

- [ ] **Step 4: Add the iframe + controls JS** — append to `distributor/templates/admin/core/sitesettings/change_form.html` (inside the page, after the existing preset UI; use `{% block %}` consistent with the file — if it extends the admin change_form, append within its content block):

```html
<div id="appearance-preview" style="margin-top:1rem">
  <h3>{% trans "Live preview" %}</h3>
  <iframe id="appearance-frame" src="/?appearance_preview=1"
          style="width:100%;height:520px;border:1px solid #ccc;border-radius:8px"></iframe>
</div>
<script>
(function () {
  var frame = document.getElementById("appearance-frame");
  var ids = ["id_custom_accent", "id_chrome_bg", "id_chrome_text", "id_chrome_opacity"];
  var timer = null;
  function push() {
    var params = new URLSearchParams({
      accent: (document.getElementById("id_custom_accent") || {}).value || "",
      chrome_bg: (document.getElementById("id_chrome_bg") || {}).value || "",
      chrome_text: (document.getElementById("id_chrome_text") || {}).value || "",
      chrome_opacity: (document.getElementById("id_chrome_opacity") || {}).value || "100",
    });
    fetch("preview-css/?" + params.toString(), {credentials: "same-origin"})
      .then(function (r) { return r.json(); })
      .then(function (vars) {
        if (frame.contentWindow) {
          frame.contentWindow.postMessage({type: "appearance", vars: vars}, location.origin);
        }
      });
  }
  function debounced() { clearTimeout(timer); timer = setTimeout(push, 200); }
  ids.forEach(function (id) {
    var el = document.getElementById(id);
    if (el) { el.addEventListener("input", debounced); el.addEventListener("change", debounced); }
  });
  frame.addEventListener("load", push);
})();
</script>
```

- [ ] **Step 5: Add the preview listener** — in `distributor/templates/base.html`, before `</body>` (end of file), add:

```html
{% if request.GET.appearance_preview %}
<script>
window.addEventListener("message", function (e) {
  if (e.origin !== location.origin) return;
  var d = e.data || {};
  if (d.type !== "appearance" || !d.vars) return;
  var root = document.documentElement;
  Object.keys(d.vars).forEach(function (k) { root.style.setProperty(k, d.vars[k]); });
});
</script>
{% endif %}
```

- [ ] **Step 6: Run tests**

Run: `MSYS_NO_PATHCONV=1 docker compose -f docker-compose.dev.yml exec -T web python manage.py test apps.core.tests_appearance.AppearancePreviewEndpointTests apps.core.tests_appearance.AppearanceAdminFormTests --settings=config.settings.development`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add distributor/apps/core/admin.py distributor/templates/admin/core/sitesettings/change_form.html distributor/templates/base.html distributor/apps/core/tests_appearance.py
git commit -m "feat(constructor): admin Appearance fieldset + live iframe preview endpoint"
```

---

### Task 7: End-to-end verification

**Files:** none (verification only).

- [ ] **Step 1: Full regression gate**

Run:
```
MSYS_NO_PATHCONV=1 docker compose -f docker-compose.dev.yml exec -T web python manage.py test --settings=config.settings.development
MSYS_NO_PATHCONV=1 docker compose -f docker-compose.dev.yml exec -T web python manage.py check --settings=config.settings.development
MSYS_NO_PATHCONV=1 docker compose -f docker-compose.dev.yml exec -T web python manage.py makemigrations --check --dry-run core --settings=config.settings.development
```
Expected: all tests PASS; no check issues; `No changes detected`.

- [ ] **Step 2: Browser verification (chrome-devtools MCP)**

Using the chrome-devtools MCP tools: set a `custom_accent` (e.g. `#16a34a`) on SiteSettings (admin or shell), open `http://localhost:8008/`, and evaluate
`getComputedStyle(document.documentElement).getPropertyValue('--primary-600').trim()`.
Expected: `22 163 74` (the override wins over the theme). Also open `/admin/core/sitesettings/` and confirm the iframe preview updates when the accent colour input changes.

- [ ] **Step 3: Rebuild note**

Confirm `coloraide`/`django-colorfield` are in `distributor/requirements.txt` (Task 1) so a fresh `docker compose build web` includes them. No commit needed if already present.

---

## Self-Review notes (author)

- **Spec coverage:** colours (custom accent → ramp) → Tasks 2/4/5; transparency (`--chrome-alpha`) → Tasks 4/5; background position/size → Tasks 4/5; live preview (iframe + postMessage + endpoint) → Task 6; SSR/preview single source → Task 3 (`preview_vars`/`build_appearance_css` share `AppearanceTheme.to_css_map`); libraries (coloraide, django-colorfield) → Task 1; DDD layering (domain/app/infra/presentation) → Tasks 2/3 vs 4 vs 5/6; tests incl. browser verify → all tasks + Task 7.
- **Type consistency:** `Palette`, `AppearanceTheme`, `generate_primary_ramp`, `to_css_map`, `to_css_declarations`, `build_appearance_css`, `preview_vars`, context keys `appearance_css`/`page_background_position`/`page_background_size`, URL `admin:core_sitesettings_preview_css` — used identically across tasks.
- **Risks flagged inline:** coloraide channel-access API (Task 2 Step 5 fallback); `color-mix` browser support (modern evergreen — fine for this admin-driven site); override specificity via doubled attribute selector (verified in Task 7 browser step).
- **Out of scope (per spec):** drag-drop blocks, multiple saved themes, fonts.
