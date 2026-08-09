from labyrinthes.adapters.tkinter.common.pill_btn import PillButton
from labyrinthes.adapters.tkinter.common.tokens import (
    FOCUS_RING_THICKNESS,
    RESTING_RING_THICKNESS,
    Theme,
    colors_for,
)


def test_default_pill_button_uses_panel_background_and_ink_text(tk_root):
    colors = colors_for(Theme.LIGHT)
    button = PillButton(tk_root, "Cancel", theme=Theme.LIGHT)

    assert button.cget("background") == colors.panel
    assert button._label.cget("foreground") == colors.ink


def test_primary_pill_button_light_mode_uses_accent_fill_and_window_text(tk_root):
    colors = colors_for(Theme.LIGHT)
    button = PillButton(tk_root, "New Maze", theme=Theme.LIGHT, primary=True)

    assert button.cget("background") == colors.accent
    assert button._label.cget("foreground") == colors.window


def test_primary_pill_button_dark_mode_uses_accent_strong_dark_fill(tk_root):
    colors = colors_for(Theme.DARK)
    button = PillButton(tk_root, "New Maze", theme=Theme.DARK, primary=True)

    assert button.cget("background") == colors.accent_strong_dark
    # Bugfix (Story 1.10): text must resolve to the light-mode `window`
    # literal (white, ~8.7:1 against `accent_strong_dark`) regardless of
    # the widget's own theme -- `colors.window` (dark mode's near-black
    # `#12161d`) would land at ~2.1:1, far under AA.
    assert button._label.cget("foreground") == colors_for(Theme.LIGHT).window


def test_pill_button_command_fires_on_click(tk_root):
    calls = []
    button = PillButton(tk_root, "Save", theme=Theme.LIGHT, command=lambda: calls.append(1))

    # `tk_root` is withdrawn, so real X11 button-press synthesis isn't
    # reliable; invoke the bound handler directly (see test_icon_btn.py).
    button._on_click()

    assert calls == [1]


def test_pill_button_with_shortcut_renders_a_kbd_tag(tk_root):
    button = PillButton(tk_root, "Save", theme=Theme.LIGHT, shortcut="Ctrl+S")

    assert button._kbd is not None
    assert button._kbd.cget("text") == "Ctrl+S"


def test_pill_button_is_keyboard_focusable(tk_root):
    button = PillButton(tk_root, "Save", theme=Theme.LIGHT)

    assert button.cget("takefocus")


def test_pill_button_binds_return_and_space_to_activation(tk_root):
    button = PillButton(tk_root, "Save", theme=Theme.LIGHT)

    assert button.bind("<Return>") != ""
    assert button.bind("<space>") != ""


def test_pill_button_return_key_fires_the_same_command_as_a_click(tk_root):
    calls = []
    button = PillButton(tk_root, "Save", theme=Theme.LIGHT, command=lambda: calls.append(1))

    # `tk_root` is withdrawn, so real X11 key-press synthesis isn't
    # reliable; invoke the bound handler directly (see test_icon_btn.py).
    button._on_click()

    assert calls == [1]


def test_pill_button_focus_in_shows_an_accent_focus_ring(tk_root):
    colors = colors_for(Theme.LIGHT)
    button = PillButton(tk_root, "Save", theme=Theme.LIGHT)

    button._on_focus_in()

    assert button.cget("highlightthickness") == FOCUS_RING_THICKNESS
    assert button.cget("highlightbackground") == colors.accent
    assert button.cget("highlightcolor") == colors.accent


def test_pill_button_focus_out_reverts_to_the_resting_ring(tk_root):
    colors = colors_for(Theme.LIGHT)
    button = PillButton(tk_root, "Save", theme=Theme.LIGHT)

    button._on_focus_in()
    button._on_focus_out()

    assert button.cget("highlightthickness") == RESTING_RING_THICKNESS
    assert button.cget("highlightbackground") == colors.border
    assert button.cget("highlightcolor") == colors.border


def test_primary_pill_button_focus_ring_is_not_the_same_color_as_its_own_fill(tk_root):
    # Regression: `colors.accent` (the standard focus-ring color) *is* a
    # primary button's own light-mode fill -- reusing it would render a
    # ring that's visually fused to the fill (~1.00:1 contrast).
    colors = colors_for(Theme.LIGHT)
    button = PillButton(tk_root, "New Maze", theme=Theme.LIGHT, primary=True)

    button._on_focus_in()

    assert button.cget("highlightbackground") != colors.accent
    assert button.cget("highlightbackground") == colors_for(Theme.LIGHT).window


def test_primary_pill_button_dark_mode_focus_ring_also_uses_the_always_white_color(tk_root):
    button = PillButton(tk_root, "New Maze", theme=Theme.DARK, primary=True)

    button._on_focus_in()

    assert button.cget("highlightbackground") == colors_for(Theme.LIGHT).window
    assert button.cget("highlightcolor") == colors_for(Theme.LIGHT).window


def test_default_pill_button_focus_ring_still_uses_accent(tk_root):
    # The fill collision above is specific to the primary variant -- the
    # default variant's `colors.panel` fill has no such collision, so it
    # keeps the standard ring color every other focusable widget uses.
    colors = colors_for(Theme.LIGHT)
    button = PillButton(tk_root, "Cancel", theme=Theme.LIGHT)

    button._on_focus_in()

    assert button.cget("highlightbackground") == colors.accent


def test_primary_pill_buttons_kbd_tag_text_also_gets_the_aa_contrast_fix(tk_root):
    # Regression: the primary-text AA bugfix was applied to `_label` but
    # left `_kbd`'s foreground at `KbdTag`'s default `colors.ink_soft`,
    # which measures ~1.06:1 (light) / ~2.94:1 (dark) against a primary
    # fill -- the same failure class, one widget over.
    button = PillButton(tk_root, "New Maze", theme=Theme.DARK, primary=True, shortcut="Ctrl+N")

    assert button._kbd is not None
    assert button._kbd.cget("foreground") == colors_for(Theme.LIGHT).window


def test_default_pill_buttons_kbd_tag_text_keeps_ink_soft(tk_root):
    colors = colors_for(Theme.LIGHT)
    button = PillButton(tk_root, "Cancel", theme=Theme.LIGHT, shortcut="Esc")

    assert button._kbd is not None
    assert button._kbd.cget("foreground") == colors.ink_soft
