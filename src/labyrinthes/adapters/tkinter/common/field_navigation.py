"""`FieldNavigator` -- shared arrow-key/Enter navigation for stacked-field popup forms.

`NewMazeDialog` (builder) and `GenerateRandomDialog` (player) both lay out a
short, single-column stack of `tk.Entry` fields above a Cancel/Confirm
button pair. Before this, `<Return>` on every field fired the confirm
handler directly, and the arrow keys did nothing beyond each `Entry`'s own
built-in text-cursor movement. This gives both dialogs a single shared,
tested navigation behavior instead of hand-rolling it twice:

- `<Up>`/`<Down>` always move focus to the previous/next field, regardless
  of cursor position -- `Entry`'s class binding has no behavior on these
  keys to preserve, so there is nothing to fall through to.
- `<Left>`/`<Right>` only move focus when the text cursor is already at the
  field's start/end *and* nothing is selected; otherwise the handler
  returns `None` so Tk's bindtag scan falls through to `Entry`'s own class
  binding and the key moves the cursor within the text as normal. Returning
  `"break"` at an instance-level binding stops that fallthrough entirely
  (confirmed live -- see `test_save_maze_dialog.py`'s note on
  `move_up`/`move_down`/`move_left`/`move_right`), so this handler must
  return `None`, not `"break"`, whenever it declines to intercept.
- `<Return>` moves focus forward one step, exactly like `<Down>` -- it no
  longer submits directly. On the last field, both `<Down>` and `<Return>`
  move focus to `confirm_widget` rather than wrapping or no-op'ing, so the
  keyboard flow continues "in the same direction" onto the button. A
  second `<Return>` then activates it: `PillButton` already binds
  `<Return>`/`<space>` on itself to its own click handler once focused, so
  no submit wiring is needed here.

Only the fields and the confirm widget participate -- Cancel stays reachable
by `Tab` (Tk's native focus-traversal order) as before, unaffected by any of
this.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable, Sequence

__all__ = ["FieldNavigator"]

_EventHandler = Callable[[tk.Event | None], "str | None"]


def is_at_text_boundary(entry: tk.Entry, delta: int) -> bool:
    """Whether `entry`'s cursor sits at its start (`delta < 0`) or end (`delta > 0`).

    A pending selection never counts as "at the boundary" -- Left/Right on a
    selection collapses it under `Entry`'s own class binding rather than
    hopping fields, mirroring how a plain (non-empty) selection behaves in
    any text field. Extracted as a standalone, widget-only function so it
    can be exercised directly in tests without synthesizing real Tk key
    events (unreliable against this suite's withdrawn `tk_root`, per
    `test_save_maze_dialog.py`'s convention).
    """
    if entry.selection_present():
        return False
    cursor = entry.index("insert")
    return cursor == 0 if delta < 0 else cursor == entry.index("end")


class FieldNavigator:
    """Wire Up/Down, boundary-aware Left/Right, and Enter across `entries`, ending at
    `confirm_widget`.
    """

    def __init__(self, entries: Sequence[tk.Entry], confirm_widget: tk.Widget) -> None:
        self._order: list[tk.Widget] = [*entries, confirm_widget]

        for index, entry in enumerate(entries):
            entry.bind("<Up>", self._make_step(index, -1))
            entry.bind("<Down>", self._make_step(index, +1))
            entry.bind("<Return>", self._make_step(index, +1))
            entry.bind("<Left>", self._make_boundary_step(index, entry, -1))
            entry.bind("<Right>", self._make_boundary_step(index, entry, +1))

    def focus_step(self, index: int, delta: int) -> None:
        """Move focus from `index` by `delta` steps, clamped to the field/button chain."""
        target = index + delta
        if 0 <= target < len(self._order):
            self._order[target].focus_set()

    def _make_step(self, index: int, delta: int) -> _EventHandler:
        def handler(_event: tk.Event | None = None) -> str:
            self.focus_step(index, delta)
            return "break"

        return handler

    def _make_boundary_step(self, index: int, entry: tk.Entry, delta: int) -> _EventHandler:
        def handler(_event: tk.Event | None = None) -> str | None:
            if not is_at_text_boundary(entry, delta):
                return None
            self.focus_step(index, delta)
            return "break"

        return handler
