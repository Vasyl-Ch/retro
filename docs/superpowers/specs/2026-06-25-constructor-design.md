# Constructor (Direction 3) — Visual Appearance Editor — Design Spec

> Status: design approved (Approach A). Next: implementation plan via writing-plans.
> Date: 2026-06-25.

## Goal

Let a non-technical admin customize the site's **colors, transparency, and background
position**, with a **live preview**, without editing code — building on the existing
CSS-variable theming (`data-theme` + `--primary-*`/`--chrome-*`) and the `SiteSettings`
singleton / `PageBackground` models.

## Principles (explicit requirements)

- **DRY:** one source of truth for the colour ramp and the emitted CSS — shared by the
  server-rendered `<style>`, the live-preview endpoint, and tests.
- **SOLID:** a pure domain core (no Django) for colour math; the Django model is
  infrastructure; the admin/template are presentation. Dependencies point inward
  (presentation → application → domain); the domain depends on nothing project-specific.
- **DDD (pragmatic):** a small `appearance` bounded context (`apps/core/appearance/`) with
  **value objects** (`Palette`, `AppearanceTheme`) and a thin **application service**. No
  repositories/aggregates ceremony — the singleton model is the persistence boundary.
- **Prefer libraries over bespoke code:**
  - **coloraide** — perceptual (OKLCH) colour interpolation to derive the 50–900 ramp from a
    single accent. We do NOT hand-roll tint/shade math.
  - **django-colorfield** — `ColorField` (hex validation) + admin colour-picker widget. We do
    NOT hand-roll colour inputs or validation.
  - Live-preview iframe/`postMessage` glue is the only bespoke part (no fitting library; thin).

## Architecture (layers)

```
apps/core/appearance/                  ← bounded context "Appearance"
  palette.py        (DOMAIN, pure)     ← Palette, AppearanceTheme value objects; ramp via coloraide
  services.py       (APPLICATION)      ← build_appearance_css(settings) -> str ; preview_vars(params) -> dict
apps/core/models.py        (INFRA)     ← SiteSettings + PageBackground appearance fields (django-colorfield)
apps/core/context_processors.py (PRES) ← expose appearance_css (reuses get_solo)
templates/base.html             (PRES) ← inject override <style> + preview listener
apps/core/admin.py + change_form (PRES)← Appearance fieldset + live-preview iframe; preview endpoint
ada-frontend/assets/css/tailus.css     ← add --chrome-alpha (alpha-capable chrome); no value duplication
```

**Single source of truth:** `palette.generate_primary_ramp()` + `AppearanceTheme.to_css_declarations()`
produce the CSS var map. Both the context processor (SSR) and the preview endpoint (live) call the
**same** application service. Tests assert against the same functions.

## Domain (`apps/core/appearance/palette.py`) — pure, no Django

- `RAMP_STEPS = (50,100,200,300,400,500,600,700,800,900)`.
- `generate_primary_ramp(accent_hex: str) -> Palette`
  - Uses coloraide: take the accent colour, anchor it at step **600** (matches how the
    existing themes treat `--primary-600` as the main brand tone), and interpolate the other
    steps along a fixed **lightness curve** in **OKLCH**, preserving the accent's hue and
    (scaled) chroma. Lightness anchors are constants chosen to mirror the existing classic
    ramp's perceived range (≈97% at 50 → ≈25% at 900).
  - Output format matches tailus.css: each step is a **space-separated RGB triplet string**
    (e.g. `"37 99 235"`), so it slots into `rgb(var(--primary-600))`.
- `Palette` (frozen dataclass): `steps: dict[int,str]`; `to_css_vars(prefix="--primary") -> dict[str,str]`.
- `AppearanceTheme` (frozen dataclass) value object aggregating an optional `Palette`, optional
  chrome colour overrides, and an optional chrome alpha:
  - `to_css_declarations() -> str` → CSS lines like `--primary-600: 37 99 235;\n--chrome-alpha: 0.8;`
  - Empty when nothing is customized → callers emit nothing (fall back to `data-theme`).

These functions are unit-tested with **no database** (`SimpleTestCase`).

## Application service (`apps/core/appearance/services.py`)

- `build_appearance_css(settings_obj) -> str` — maps the SiteSettings appearance fields →
  `AppearanceTheme` → `to_css_declarations()`. Returns `""` when nothing is set.
- `preview_vars(*, accent, chrome_bg, chrome_text, chrome_opacity) -> dict[str,str]` — builds the
  same var map from raw (unsaved) values for the live endpoint. Internally shares the mapping
  logic with `build_appearance_css` (one private helper → DRY).

## Persistence (infrastructure) — model fields + migration

**SiteSettings** (new "Appearance" group; all optional, empty ⇒ use `data-theme`):
- `custom_accent = ColorField(blank=True, default="")` — overrides the primary ramp.
- `chrome_bg = ColorField(blank=True, default="")` — header/footer background override.
- `chrome_text = ColorField(blank=True, default="")` — header/footer text override.
- `chrome_opacity = PositiveSmallIntegerField(default=100, validators=[Min(0),Max(100)])` —
  header/footer transparency (→ `--chrome-alpha`).

**PageBackground** (background positioning):
- `position = CharField(choices=POSITION_CHOICES, default="center")` — maps to `background-position`
  (center / top / bottom / left / right / top-left / … — a safe enum, not free CSS).
- `size = CharField(choices=[("cover","Cover"),("contain","Contain")], default="cover")`.

One schema migration per model. **modeltranslation note:** these are appearance (non-textual)
fields — NOT registered for translation. No data migration needed (defaults are correct;
existing rows get `custom_accent=""` ⇒ unchanged appearance).

## CSS rendering (presentation)

- **tailus.css refactor (scoped, DRY):** introduce `--chrome-alpha` (default `1`) and make the
  header/footer background alpha-capable so transparency is a single variable, with the **base
  colours staying in CSS** (no Python/CSS duplication). The 4 theme palettes are otherwise
  untouched.
- **base.html:** after the `data-theme` attribute and after the theme stylesheet, inject
  `<style id="appearance-overrides">:root[data-theme][data-theme]{ {{ appearance_css }} }</style>`
  only when `appearance_css` is non-empty. The doubled attribute selector guarantees the
  override beats `:root[data-theme="classic"]` regardless of source order (verified with
  chrome-devtools in the plan).
- **context_processor:** extend the existing `site_settings` processor (reuse its `get_solo`)
  to also return `appearance_css = build_appearance_css(settings_obj)`, guarded by the same
  `OperationalError/ProgrammingError` try/except already used there.
- **PageBackground** rendering in base.html gains `background-position`/`background-size` from the
  resolved record (context processor already returns the chosen background; extend it with the
  two new values).

## Live preview (presentation, bespoke glue)

- **Admin "Appearance" page:** extend `SiteSettingsAdmin` — add the Appearance fieldset, and in
  the custom `change_form.html` add an `<iframe src="{home}?appearance_preview=1">` beside the
  colour controls.
- **Preview endpoint:** `admin:core_sitesettings_preview_css` (staff-only, via
  `admin_site.admin_view`) — GET with `accent/chrome_bg/chrome_text/chrome_opacity` query params →
  returns `JsonResponse` of the var map from `services.preview_vars` (**same domain code** as SSR).
- **Client glue:** small JS in the change_form debounces control changes → `fetch` the endpoint →
  `iframe.contentWindow.postMessage({type:'appearance', vars}, origin)`. A tiny listener in
  base.html (active only when `?appearance_preview=1` and `event.origin === location.origin`)
  applies the vars via `documentElement.style.setProperty(...)`. Saving persists the fields; the
  next full load reproduces the identical look via SSR (same service).

## Error handling

- Empty/invalid accent → service returns `""` → no override (theme stands). `ColorField`
  validates hex on input, so the domain receives well-formed values; `generate_primary_ramp`
  still guards non-hex defensively and raises a clear `ValueError` (covered by a test).
- `chrome_opacity` clamped 0–100 by validators; emitted as `alpha = opacity/100`.
- Preview endpoint validates/sanitizes params; bad values fall back to defaults, never 500.
- Context processor swallows DB-not-ready errors (consistent with existing behavior).

## Testing strategy

- **Domain (SimpleTestCase, no DB):** ramp has 10 steps; lightness monotonic dark→light; step
  600 ≈ accent; triplet output format; `to_css_declarations` format; empty theme ⇒ "".
- **Service:** `build_appearance_css` empty when unset; correct vars when set; `preview_vars`
  matches `build_appearance_css` for the same inputs (DRY guard).
- **Model/migration:** new fields exist; `makemigrations --check` clean.
- **Context processor:** `appearance_css` present/empty as expected.
- **Admin:** Appearance fields render on the change form; preview endpoint returns the expected
  JSON var map and is staff-gated (403 for anonymous).
- **Browser verification (plan step, chrome-devtools MCP):** load home with a custom accent;
  assert computed `--primary-600` equals the accent and the override wins over the theme.

## Out of scope (v1 — YAGNI)

Drag-and-drop block builder; per-component layout editing; multiple saved/named themes;
free-form CSS; font customization. These can be later sub-projects.

## Dependencies / ops

- Add to `distributor/requirements.txt`: `coloraide`, `django-colorfield`. Add `colorfield` to
  `INSTALLED_APPS`. The dev Docker image installs from requirements at build → the plan includes
  a one-time `docker compose build web` (or `pip install` in the running container) before tests.
</content>
