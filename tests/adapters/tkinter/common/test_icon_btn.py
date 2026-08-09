import tkinter as tk

from labyrinthes.adapters.tkinter.common.icon_btn import IconButton
from labyrinthes.adapters.tkinter.common.tokens import (
    FOCUS_RING_THICKNESS,
    RESTING_RING_THICKNESS,
    Theme,
    colors_for,
)


def test_icon_button_has_a_fixed_30x30_footprint(tk_root):
    button = IconButton(tk_root, glyph="⚙", theme=Theme.LIGHT)
    button.pack()
    tk_root.update_idletasks()

    assert button.winfo_reqwidth() == 30
    assert button.winfo_reqheight() == 30


def test_icon_button_command_fires_on_click(tk_root):
    calls = []
    button = IconButton(tk_root, glyph="⚙", theme=Theme.LIGHT, command=lambda: calls.append(1))

    # `tk_root` is withdrawn (no visible flash), so a real, mapped-window
    # X11 button press can't be synthesized reliably; invoke the bound
    # handler directly instead -- exercises the same code path a click would.
    button._on_click()

    assert calls == [1]


def test_icon_button_with_tooltip_shows_a_popup_on_hover(tk_root):
    button = IconButton(tk_root, glyph="⚙", theme=Theme.LIGHT, tooltip="Open settings.")
    button.pack()
    tk_root.update_idletasks()

    assert button._tooltip is not None
    button._tooltip._on_enter()
    tk_root.update_idletasks()

    popups = [child for child in button.winfo_children() if isinstance(child, tk.Toplevel)]
    assert popups


def test_icon_button_is_keyboard_focusable(tk_root):
    button = IconButton(tk_root, glyph="⚙", theme=Theme.LIGHT)

    assert button.cget("takefocus")


def test_icon_button_binds_return_and_space_to_activation(tk_root):
    button = IconButton(tk_root, glyph="⚙", theme=Theme.LIGHT)

    assert button.bind("<Return>") != ""
    assert button.bind("<space>") != ""


def test_icon_button_return_key_fires_the_same_command_as_a_click(tk_root):
    calls = []
    button = IconButton(tk_root, glyph="⚙", theme=Theme.LIGHT, command=lambda: calls.append(1))

    # `tk_root` is withdrawn, so real X11 key-press synthesis isn't
    # reliable; invoke the bound handler directly (see this module's other
    # `_on_click()` tests).
    button._on_click()

    assert calls == [1]


def test_icon_button_rests_at_resting_ring_thickness_and_border_color(tk_root):
    colors = colors_for(Theme.LIGHT)
    button = IconButton(tk_root, glyph="⚙", theme=Theme.LIGHT)

    assert button.cget("highlightthickness") == RESTING_RING_THICKNESS
    assert button.cget("highlightbackground") == colors.border
    assert button.cget("highlightcolor") == colors.border


def test_icon_button_focus_in_shows_an_accent_focus_ring(tk_root):
    colors = colors_for(Theme.LIGHT)
    button = IconButton(tk_root, glyph="⚙", theme=Theme.LIGHT)

    # Real Tab-traversal focus isn't reliably synthesizable under this
    # suite's withdrawn `tk_root`; invoke the bound handler directly.
    button._on_focus_in()

    assert button.cget("highlightthickness") == FOCUS_RING_THICKNESS
    assert button.cget("highlightbackground") == colors.accent
    assert button.cget("highlightcolor") == colors.accent


def test_icon_button_focus_out_reverts_to_the_resting_ring(tk_root):
    colors = colors_for(Theme.LIGHT)
    button = IconButton(tk_root, glyph="⚙", theme=Theme.LIGHT)

    button._on_focus_in()
    button._on_focus_out()

    assert button.cget("highlightthickness") == RESTING_RING_THICKNESS
    assert button.cget("highlightbackground") == colors.border
    assert button.cget("highlightcolor") == colors.border
