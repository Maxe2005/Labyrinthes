import tkinter as tk

from labyrinthes.adapters.tkinter.common.tokens import Theme
from labyrinthes.adapters.tkinter.common.tooltip import Tooltip


def _toplevel_children(widget: tk.Widget) -> list[tk.Toplevel]:
    return [child for child in widget.winfo_children() if isinstance(child, tk.Toplevel)]


def test_tooltip_appears_on_enter_and_is_destroyed_on_leave(tk_root):
    target = tk.Label(tk_root, text="Break Wall")
    target.pack()
    tk_root.update_idletasks()

    tooltip = Tooltip(
        target, "Removes the wall between the cursor and the next cell", theme=Theme.LIGHT
    )
    assert _toplevel_children(target) == []

    # `tk_root` is withdrawn (no visible flash), so a real, mapped-window
    # X11 pointer-enter event can't be synthesized reliably; call the bound
    # `<Enter>`/`<Leave>` handlers directly instead, per the story's testing
    # notes -- this exercises the exact same code a real hover would run.
    tooltip._on_enter()
    popups = _toplevel_children(target)
    assert len(popups) == 1
    assert popups[0].winfo_exists()

    tooltip._on_leave()
    assert _toplevel_children(target) == []


def test_tooltip_repeated_enter_does_not_stack_popups(tk_root):
    target = tk.Label(tk_root, text="Break Wall")
    target.pack()
    tk_root.update_idletasks()

    tooltip = Tooltip(target, "Removes the wall.", theme=Theme.DARK)

    tooltip._on_enter()
    first_popup = tooltip._popup

    tooltip._on_enter()

    assert tooltip._popup is first_popup
