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
            # Keep the whole chrome consistent: the brand name / footer
            # headings follow the custom text colour, hover shifts to accent.
            css["--chrome-brand"] = self.chrome_text
            css["--chrome-text-hover"] = "rgb(var(--primary-600))"
        if self.chrome_alpha is not None:
            css["--chrome-alpha"] = f"{self.chrome_alpha:g}"
        return css

    def to_css_declarations(self) -> str:
        return "\n".join(f"{name}: {value};" for name, value in self.to_css_map().items())
