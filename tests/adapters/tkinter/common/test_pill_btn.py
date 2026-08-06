from labyrinthes.adapters.tkinter.common.pill_btn import PillButton
from labyrinthes.adapters.tkinter.common.tokens import Theme, colors_for


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
    assert button._label.cget("foreground") == colors.window


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
