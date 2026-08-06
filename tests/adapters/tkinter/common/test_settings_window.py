import tkinter as tk

from labyrinthes.adapters.tkinter.common.settings_window import SettingsWindow
from labyrinthes.adapters.tkinter.common.tokens import Theme


def _all_label_texts(widget: tk.Widget) -> list[str]:
    texts = []
    for child in widget.winfo_children():
        if isinstance(child, tk.Label):
            texts.append(child.cget("text"))
        texts.extend(_all_label_texts(child))
    return texts


def test_settings_window_is_a_toplevel(tk_root):
    window = SettingsWindow(tk_root, theme=Theme.LIGHT)
    try:
        assert isinstance(window, tk.Toplevel)
    finally:
        window.destroy()


def test_settings_window_is_non_modal(tk_root):
    window = SettingsWindow(tk_root, theme=Theme.LIGHT)
    try:
        assert window.grab_status() is None
    finally:
        window.destroy()


def test_settings_window_shows_exactly_the_appearance_category_with_placeholder_content(tk_root):
    window = SettingsWindow(tk_root, theme=Theme.LIGHT)
    try:
        texts = _all_label_texts(window)
        assert "Appearance" in texts
        assert any("coming soon" in text.lower() for text in texts)
    finally:
        window.destroy()
