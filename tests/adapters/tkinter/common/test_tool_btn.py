from labyrinthes.adapters.tkinter.common.tokens import Theme
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
