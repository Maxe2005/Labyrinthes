import tkinter as tk

from labyrinthes.adapters.tkinter.common.kbd_tag import KbdTag
from labyrinthes.adapters.tkinter.common.tokens import Theme


def test_kbd_tag_shortcut_is_visible_without_any_hover(tk_root):
    tag = KbdTag(tk_root, "W", theme=Theme.LIGHT)

    assert isinstance(tag, tk.Label)
    assert tag.cget("text") == "W"


def test_kbd_tag_styles_from_the_given_theme(tk_root):
    light_tag = KbdTag(tk_root, "A", theme=Theme.LIGHT)
    dark_tag = KbdTag(tk_root, "A", theme=Theme.DARK)

    assert light_tag.cget("background") != dark_tag.cget("background")
