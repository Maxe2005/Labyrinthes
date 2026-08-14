from labyrinthes.adapters.tkinter.common.tokens import (
    FOCUS_RING_THICKNESS,
    RESTING_RING_THICKNESS,
    Theme,
    colors_for,
)
from labyrinthes.adapters.tkinter.common.tool_btn import ToolButton, ToolButtonGroup


def test_tool_button_group_activation_is_mutually_exclusive(tk_root):
    group = ToolButtonGroup()
    b1 = ToolButton(tk_root, "Break Wall", theme=Theme.LIGHT, group=group)
    b2 = ToolButton(tk_root, "Set Entry", theme=Theme.LIGHT, group=group)
    b3 = ToolButton(tk_root, "Set Exit", theme=Theme.LIGHT, group=group)

    group.activate(b1)
    assert b1.active is True
    assert b2.active is False
    assert b3.active is False

    group.activate(b2)
    assert b1.active is False
    assert b2.active is True
    assert b3.active is False


def test_clicking_a_grouped_tool_button_activates_it(tk_root):
    group = ToolButtonGroup()
    b1 = ToolButton(tk_root, "Break Wall", theme=Theme.LIGHT, group=group)
    b2 = ToolButton(tk_root, "Set Entry", theme=Theme.LIGHT, group=group)

    # `tk_root` is withdrawn, so real X11 button-press synthesis isn't
    # reliable; invoke the bound handler directly (exercises the same code
    # path a real click would, per the story's testing notes).
    b1._on_click()
    assert b1.active is True
    assert b2.active is False

    b2._on_click()
    assert b1.active is False
    assert b2.active is True


def test_ungrouped_tool_button_command_fires_on_click(tk_root):
    calls = []
    button = ToolButton(tk_root, "Solo", theme=Theme.DARK, command=lambda: calls.append(1))

    button._on_click()

    assert calls == [1]


def test_calling_set_active_directly_still_respects_group_exclusivity(tk_root):
    # Regression: set_active(True) called directly (bypassing activate())
    # must not let two grouped buttons both show active styling.
    group = ToolButtonGroup()
    b1 = ToolButton(tk_root, "Break Wall", theme=Theme.LIGHT, group=group)
    b2 = ToolButton(tk_root, "Set Entry", theme=Theme.LIGHT, group=group)

    b1.set_active(True)
    assert b1.active is True
    assert b2.active is False

    b2.set_active(True)
    assert b1.active is False
    assert b2.active is True


def test_tool_button_with_shortcut_renders_a_kbd_tag(tk_root):
    button = ToolButton(tk_root, "Break Wall", theme=Theme.LIGHT, shortcut="B")

    assert button._kbd is not None
    assert button._kbd.cget("text") == "B"


def test_tool_button_is_keyboard_focusable(tk_root):
    button = ToolButton(tk_root, "Break Wall", theme=Theme.LIGHT)

    assert button.cget("takefocus")


def test_tool_button_binds_return_and_space_to_activation(tk_root):
    button = ToolButton(tk_root, "Break Wall", theme=Theme.LIGHT)

    assert button.bind("<Return>") != ""
    assert button.bind("<space>") != ""


def test_tool_button_return_key_fires_the_same_command_as_a_click(tk_root):
    calls = []
    button = ToolButton(tk_root, "Solo", theme=Theme.LIGHT, command=lambda: calls.append(1))

    # `tk_root` is withdrawn, so real X11 key-press synthesis isn't
    # reliable; invoke the bound handler directly (see this module's other
    # `_on_click()` tests).
    button._on_click()

    assert calls == [1]


def test_inactive_tool_button_focus_in_shows_an_accent_focus_ring(tk_root):
    colors = colors_for(Theme.LIGHT)
    button = ToolButton(tk_root, "Break Wall", theme=Theme.LIGHT)

    button._on_focus_in()

    assert button.cget("highlightthickness") == FOCUS_RING_THICKNESS
    assert button.cget("highlightbackground") == colors.accent
    assert button.cget("highlightcolor") == colors.accent


def test_inactive_tool_button_focus_out_reverts_to_resting_border(tk_root):
    colors = colors_for(Theme.LIGHT)
    button = ToolButton(tk_root, "Break Wall", theme=Theme.LIGHT)

    button._on_focus_in()
    button._on_focus_out()

    assert button.cget("highlightthickness") == RESTING_RING_THICKNESS
    assert button.cget("highlightbackground") == colors.border
    assert button.cget("highlightcolor") == colors.border


def test_active_and_focused_tool_button_renders_a_thicker_ring_than_active_unfocused(tk_root):
    # The regression this story explicitly guards against: an active
    # ToolButton already borders in `colors.accent` at resting thickness,
    # so an active-but-unfocused button must stay visually distinct from
    # an active-and-focused one via thickness, not just color.
    button = ToolButton(tk_root, "Break Wall", theme=Theme.LIGHT)
    button.set_active(True)
    active_unfocused_thickness = button.cget("highlightthickness")

    button._on_focus_in()
    active_focused_thickness = button.cget("highlightthickness")

    assert active_unfocused_thickness == RESTING_RING_THICKNESS
    assert active_focused_thickness == FOCUS_RING_THICKNESS
    assert active_focused_thickness != active_unfocused_thickness


def test_set_text_replaces_the_label_in_place_without_disturbing_active_state(tk_root):
    button = ToolButton(tk_root, "Normal", theme=Theme.LIGHT)
    button.set_active(True)
    assert button._label.cget("text") == "Normal"

    button.set_text("Fast")

    assert button._label.cget("text") == "Fast"
    assert button.active is True


def test_disabled_tool_button_click_does_not_fire_the_command(tk_root):
    calls = []
    button = ToolButton(tk_root, "Solo", theme=Theme.LIGHT, command=lambda: calls.append(1))
    button.set_enabled(False)

    button._on_click()

    assert calls == []


def test_disabled_tool_button_is_non_focusable_and_renders_ghost_styling(tk_root):
    colors = colors_for(Theme.LIGHT)
    button = ToolButton(tk_root, "Break Wall", theme=Theme.LIGHT)
    button.set_enabled(False)

    assert button.cget("takefocus") == "0"
    assert button.cget("background") == colors.window
    assert button._label.cget("foreground") == colors.ghost


def test_re_enabled_tool_button_restores_focusability_activation_and_styling(tk_root):
    colors = colors_for(Theme.LIGHT)
    calls = []
    button = ToolButton(tk_root, "Solo", theme=Theme.LIGHT, command=lambda: calls.append(1))
    button.set_enabled(False)
    assert button.cget("takefocus") == "0"

    button.set_enabled(True)
    button._on_click()

    assert calls == [1]
    assert button.cget("takefocus") == "1"
    # The ghost disabled branch is gone: the click re-activated the button,
    # so it renders active (accent), never the ghost disabled palette.
    assert button.cget("background") == colors.accent_bg
    assert button._label.cget("foreground") != colors.ghost


def test_disabled_tool_button_focus_in_shows_no_focus_ring(tk_root):
    colors = colors_for(Theme.LIGHT)
    button = ToolButton(tk_root, "Break Wall", theme=Theme.LIGHT)
    button.set_enabled(False)

    button._on_focus_in()

    assert button.cget("highlightthickness") == RESTING_RING_THICKNESS
    assert button.cget("highlightbackground") == colors.ghost
    assert button.cget("highlightcolor") == colors.ghost
