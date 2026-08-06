import tkinter as tk

from labyrinthes.adapters.tkinter.common.icon_btn import IconButton
from labyrinthes.adapters.tkinter.common.tokens import Theme


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
