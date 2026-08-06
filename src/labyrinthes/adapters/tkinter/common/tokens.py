"""Design tokens for the "Blueprint" visual identity (Story 1.6).

Mirrors `DESIGN.md`'s `colors`/`typography`/`spacing`/`rounded` blocks as
plain data, field-for-field, values copied verbatim -- no invented hex/px.
Every widget primitive in `common/` styles itself from this module and a
construction-time `Theme`; nothing here renders anything.

`accent_on_tint`/`accent_strong_dark` are single, theme-independent
constants (see `DESIGN.md → Colors`): each is used in exactly one theme's
*component* state (light-mode `tool-btn` active text; dark-mode primary
`pill-btn` fill). `ColorTokens` carries the same literal value under both
`colors_for(Theme.LIGHT)` and `colors_for(Theme.DARK)` -- it is the
*widget* code, not this module, that decides which theme actually applies
the field.
"""

from __future__ import annotations

import tkinter.font as tkfont
from dataclasses import dataclass
from enum import Enum

__all__ = [
    "RADII",
    "SPACING",
    "TYPOGRAPHY",
    "ColorTokens",
    "FontSpec",
    "Theme",
    "TypographyTokens",
    "colors_for",
]


class Theme(Enum):
    """Which paired light/dark token set a widget renders with.

    `.value` is a plain string (`"light"`/`"dark"`) so it round-trips
    through Story 1.9's future settings persistence unchanged.
    """

    LIGHT = "light"
    DARK = "dark"


@dataclass(frozen=True)
class ColorTokens:
    """One theme's resolved set of `DESIGN.md → colors` values."""

    bg: str
    window: str
    panel: str
    border: str
    ink: str
    ink_soft: str
    accent: str
    accent_bg: str
    wall: str
    corridor: str
    entry: str
    exit: str
    ball: str
    ghost: str
    accent_on_tint: str
    accent_strong_dark: str


# AA-contrast fix tokens (see `DESIGN.md → Colors`): single literals, not
# paired per theme. Defined once here so both `ColorTokens` instances below
# reference the same value rather than repeating the hex.
_ACCENT_ON_TINT = "#1d4ed8"
_ACCENT_STRONG_DARK = "#1e40af"

_LIGHT = ColorTokens(
    bg="#eef2f7",
    window="#ffffff",
    panel="#f7f9fc",
    border="#d7dee6",
    ink="#1c2733",
    ink_soft="#5b6b7c",
    accent="#2563eb",
    accent_bg="#dbeafe",
    wall="#263445",
    corridor="#ffffff",
    entry="#16a34a",
    exit="#d97706",
    ball="#2563eb",
    ghost="#94a3b8",
    accent_on_tint=_ACCENT_ON_TINT,
    accent_strong_dark=_ACCENT_STRONG_DARK,
)

_DARK = ColorTokens(
    bg="#0a0d12",
    window="#12161d",
    panel="#171c25",
    border="#2a323d",
    ink="#eef2f7",
    ink_soft="#8b97a8",
    accent="#3b82f6",
    accent_bg="#16233d",
    wall="#3a4656",
    corridor="#05070a",
    entry="#22c55e",
    exit="#f59e0b",
    ball="#3b82f6",
    ghost="#4b5563",
    accent_on_tint=_ACCENT_ON_TINT,
    accent_strong_dark=_ACCENT_STRONG_DARK,
)


def colors_for(theme: Theme) -> ColorTokens:
    """The resolved `ColorTokens` for `theme`.

    Wall/corridor are the locked per-theme hexes above, never a mechanical
    inversion of one another (`DESIGN.md → Colors`).
    """
    return _LIGHT if theme is Theme.LIGHT else _DARK


# Tk treats a positive `size` as points (DPI-variable) and a negative size
# as pixels; DESIGN.md's sizes are already px, so `to_tk_font()` always
# passes `size=-value` to render them as specified rather than approximate.
_BOLD_WEIGHT_THRESHOLD = 600


@dataclass(frozen=True)
class FontSpec:
    """One `DESIGN.md → typography` entry.

    `family` keeps the full CSS fallback tuple as data, but `to_tk_font()`
    only ever passes the first entry -- Tk has no multi-family
    substitution. `letter-spacing`/`line-height` are recorded in
    `DESIGN.md` but have no `tkinter.font.Font` equivalent, so they are not
    represented here at all.
    """

    family: tuple[str, ...]
    size: int
    weight: str

    def to_tk_font(self) -> tkfont.Font:
        """A real `tkinter.font.Font` for this spec.

        `tkinter.font.Font` only accepts `weight="normal"`/`"bold"` (no
        numeric weights), so `DESIGN.md`'s CSS weight strings are mapped to
        the nearest of the two.
        """
        weight = "bold" if int(self.weight) >= _BOLD_WEIGHT_THRESHOLD else "normal"
        return tkfont.Font(family=self.family[0], size=-self.size, weight=weight)


_SYSTEM_STACK = (
    "-apple-system",
    "BlinkMacSystemFont",
    "Segoe UI",
    "Roboto",
    "Helvetica",
    "Arial",
    "sans-serif",
)
_MONOSPACE_STACK = ("ui-monospace", "SFMono-Regular", "Cascadia Mono", "Consolas", "monospace")
_KBD_MONOSPACE_STACK = ("ui-monospace", "SFMono-Regular", "Consolas", "monospace")


@dataclass(frozen=True)
class TypographyTokens:
    """The full `DESIGN.md → typography` block, one `FontSpec` per entry."""

    heading: FontSpec
    heading_sm: FontSpec
    body: FontSpec
    body_secondary: FontSpec
    label: FontSpec
    hud_stat: FontSpec
    kbd: FontSpec


TYPOGRAPHY = TypographyTokens(
    heading=FontSpec(family=_SYSTEM_STACK, size=20, weight="700"),
    heading_sm=FontSpec(family=_SYSTEM_STACK, size=15, weight="700"),
    body=FontSpec(family=_SYSTEM_STACK, size=13, weight="600"),
    body_secondary=FontSpec(family=_SYSTEM_STACK, size=14, weight="400"),
    label=FontSpec(family=_SYSTEM_STACK, size=10, weight="700"),
    hud_stat=FontSpec(family=_MONOSPACE_STACK, size=16, weight="700"),
    kbd=FontSpec(family=_KBD_MONOSPACE_STACK, size=10, weight="400"),
)

# `DESIGN.md → spacing`. Several keys (`"2xl"`, `"section-gap"`, ...) are not
# valid Python identifiers, so this is a plain dict keyed by the exact token
# strings rather than a dataclass.
SPACING: dict[str, int] = {
    "xs": 6,
    "sm": 8,
    "md": 10,
    "lg": 12,
    "xl": 14,
    "2xl": 16,
    "3xl": 18,
    "4xl": 20,
    "5xl": 24,
    "section-gap": 40,
    "page-margin": 64,
}

# `DESIGN.md → rounded`. Not applied by any of this story's five primitives
# (Tk's native widgets cannot render `border-radius`) -- recorded here as
# data for later canvas-drawn components (`maze-frame`, `marker`, `ball`).
# `full` is a percentage, not a pixel value, so it is kept as its literal
# `"50%"` string rather than coerced to an int like its siblings.
RADII: dict[str, int | str] = {
    "xs": 3,
    "sm": 5,
    "md": 6,
    "lg": 8,
    "xl": 10,
    "full": "50%",
}
