import tkinter.font as tkfont

from labyrinthes.adapters.tkinter.common.tokens import (
    FOCUS_RING_THICKNESS,
    RADII,
    RESTING_RING_THICKNESS,
    SPACING,
    TYPOGRAPHY,
    Theme,
    colors_for,
)


def test_paired_colors_resolve_per_theme():
    light = colors_for(Theme.LIGHT)
    dark = colors_for(Theme.DARK)

    assert light.accent == "#2563eb"
    assert dark.accent == "#3b82f6"
    assert light.bg == "#eef2f7"
    assert dark.bg == "#0a0d12"
    assert light.window == "#ffffff"
    assert dark.window == "#12161d"
    assert light.panel == "#f7f9fc"
    assert dark.panel == "#171c25"
    assert light.border == "#d7dee6"
    assert dark.border == "#2a323d"
    assert light.ink == "#1c2733"
    assert dark.ink == "#eef2f7"
    assert light.ink_soft == "#5b6b7c"
    assert dark.ink_soft == "#8b97a8"
    assert light.accent_bg == "#dbeafe"
    assert dark.accent_bg == "#16233d"
    assert light.entry == "#16a34a"
    assert dark.entry == "#22c55e"
    assert light.exit == "#d97706"
    assert dark.exit == "#f59e0b"
    assert light.ball == "#2563eb"
    assert dark.ball == "#3b82f6"
    assert light.ghost == "#94a3b8"
    assert dark.ghost == "#4b5563"


def test_aa_fix_tokens_are_present_and_identical_regardless_of_theme():
    light = colors_for(Theme.LIGHT)
    dark = colors_for(Theme.DARK)

    assert light.accent_on_tint == "#1d4ed8"
    assert dark.accent_on_tint == "#1d4ed8"
    assert light.accent_strong_dark == "#1e40af"
    assert dark.accent_strong_dark == "#1e40af"


def test_wall_and_corridor_are_locked_per_theme_hexes_not_a_mechanical_inversion():
    light = colors_for(Theme.LIGHT)
    dark = colors_for(Theme.DARK)

    assert light.wall == "#263445"
    assert light.corridor == "#ffffff"
    assert dark.wall == "#3a4656"
    assert dark.corridor == "#05070a"
    # Not a swap of the light-mode hexes.
    assert dark.wall != light.corridor
    assert dark.corridor != light.wall


def test_spacing_has_every_design_md_token():
    assert SPACING == {
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


def test_radii_has_every_design_md_token():
    assert RADII == {
        "xs": 3,
        "sm": 5,
        "md": 6,
        "lg": 8,
        "xl": 10,
        "full": "50%",
    }


def test_typography_has_every_design_md_entry():
    for name in ("heading", "heading_sm", "body", "body_secondary", "label", "hud_stat", "kbd"):
        assert hasattr(TYPOGRAPHY, name)


def test_font_spec_to_tk_font_uses_negative_pixel_size(tk_root):
    font = TYPOGRAPHY.heading.to_tk_font()

    assert isinstance(font, tkfont.Font)
    assert font.cget("size") == -20
    assert font.cget("family") == "-apple-system"
    assert font.cget("weight") == "bold"


def test_font_spec_to_tk_font_maps_regular_weight_to_normal(tk_root):
    font = TYPOGRAPHY.body_secondary.to_tk_font()

    assert font.cget("weight") == "normal"


def test_font_spec_family_keeps_full_css_fallback_tuple_as_data():
    assert TYPOGRAPHY.heading.family == (
        "-apple-system",
        "BlinkMacSystemFont",
        "Segoe UI",
        "Roboto",
        "Helvetica",
        "Arial",
        "sans-serif",
    )


def test_focus_ring_thickness_is_thicker_than_resting_ring_thickness():
    assert RESTING_RING_THICKNESS == 1
    assert FOCUS_RING_THICKNESS == 2
    assert FOCUS_RING_THICKNESS > RESTING_RING_THICKNESS
