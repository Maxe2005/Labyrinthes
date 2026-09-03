import tkinter as tk
import tkinter.font as tkfont

from labyrinthes.adapters.tkinter.common.group_heading import build_group_heading
from labyrinthes.adapters.tkinter.common.tokens import TYPOGRAPHY, Theme, colors_for


def test_build_group_heading_uppercases_the_given_text(tk_root):
    heading = build_group_heading(tk_root, "Walls", colors_for(Theme.LIGHT))

    assert isinstance(heading, tk.Label)
    assert heading.cget("text") == "WALLS"


def test_build_group_heading_uses_the_label_typography_token(tk_root):
    heading = build_group_heading(tk_root, "Zones", colors_for(Theme.LIGHT))

    expected = TYPOGRAPHY.label.to_tk_font()
    actual = tkfont.Font(font=heading.cget("font"))
    assert actual.actual("size") == expected.actual("size")
    assert actual.actual("weight") == expected.actual("weight")


def test_build_group_heading_styles_from_the_given_theme(tk_root):
    light_heading = build_group_heading(tk_root, "Markers", colors_for(Theme.LIGHT))
    dark_heading = build_group_heading(tk_root, "Markers", colors_for(Theme.DARK))

    light_colors = colors_for(Theme.LIGHT)
    dark_colors = colors_for(Theme.DARK)
    assert light_heading.cget("foreground") == light_colors.ghost
    assert dark_heading.cget("foreground") == dark_colors.ghost
    assert light_heading.cget("background") == light_colors.window
    assert dark_heading.cget("background") == dark_colors.window
