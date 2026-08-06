from labyrinthes.adapters.tkinter.common.hud_chip import HudChip
from labyrinthes.adapters.tkinter.common.tokens import Theme, colors_for


def test_hud_chip_shows_uppercased_label_and_value(tk_root):
    chip = HudChip(tk_root, "level", 3, theme=Theme.LIGHT)

    assert chip._caption.cget("text") == "LEVEL"
    assert chip._value_label.cget("text") == "3"


def test_hud_chip_set_value_updates_only_the_value(tk_root):
    chip = HudChip(tk_root, "pos", "(0, 0)", theme=Theme.LIGHT)

    chip.set_value("(1, 2)")

    assert chip._value_label.cget("text") == "(1, 2)"
    assert chip._caption.cget("text") == "POS"


def test_hud_chip_live_variant_uses_accent_background_and_value_color(tk_root):
    colors = colors_for(Theme.LIGHT)
    normal_chip = HudChip(tk_root, "level", 3, theme=Theme.LIGHT, live=False)
    live_chip = HudChip(tk_root, "time", "00:42", theme=Theme.LIGHT, live=True)

    assert normal_chip.cget("background") == colors.panel
    assert live_chip.cget("background") == colors.accent_bg
    assert live_chip._value_label.cget("foreground") == colors.accent
    assert normal_chip._value_label.cget("foreground") == colors.ink
