"""`_HudRow` -- the Level/Difficulty/Time/Pos chip row + HARD-mode status light.

Pure display: every value is pushed in by `GameplayScreen` (`screen.py`)
through the `set_*`/`sync_hard_mode` setters below, in response to a session
change -- this widget holds no session state and no update-skipping logic of
its own (the "only redraw on an actual change" guards, e.g.
`_last_hard_sync_state`, live in `screen.py`, which is what decides *when*
to call these setters).

The HARD-mode status light (Story 2.8) is built but hidden at construction
(HARD starts off); `sync_hard_mode()` packs it in (and recolors it) only
while HARD is active, and hides it again the instant HARD turns off.
"""

from __future__ import annotations

import tkinter as tk

from labyrinthes.adapters.tkinter.common import SPACING, TYPOGRAPHY, HudChip, Theme
from labyrinthes.adapters.tkinter.common.tokens import colors_for

__all__ = ["_HudRow"]


class _HudRow(tk.Frame):
    """Level/Difficulty/Time/Pos chips, plus a hidden-by-default HARD status light."""

    def __init__(
        self,
        parent: tk.Widget,
        *,
        theme: Theme,
        level: str,
        difficulty: str,
        time: str,
        pos: str,
    ) -> None:
        colors = colors_for(theme)
        super().__init__(parent, background=colors.window)

        self._level_chip = HudChip(self, "Level", level, theme=theme)
        self._level_chip.pack(side="left", padx=(0, SPACING["sm"]))

        self._difficulty_chip = HudChip(self, "Difficulty", difficulty, theme=theme)
        self._difficulty_chip.pack(side="left", padx=(0, SPACING["sm"]))

        self._time_chip = HudChip(self, "Time", time, theme=theme, live=True)
        self._time_chip.pack(side="left", padx=(0, SPACING["sm"]))

        self._pos_chip = HudChip(self, "Pos", pos, theme=theme)
        self._pos_chip.pack(side="left")

        # HARD-mode status light (Story 2.8): a 10px round light + a
        # Ready/Moving label, per the mockup's `.status-wrap`. Built but
        # hidden at mount -- HARD starts off -- `sync_hard_mode()` packs it
        # in (and recolors it) only while HARD is active.
        self._status_light_frame = tk.Frame(self, background=colors.window)
        self._status_light_canvas = tk.Canvas(
            self._status_light_frame,
            width=10,
            height=10,
            background=colors.window,
            highlightthickness=0,
            bd=0,
        )
        self._status_light = self._status_light_canvas.create_oval(
            0, 0, 10, 10, fill=colors.accent, outline=""
        )
        self._status_light_canvas.pack(side="left", padx=(0, SPACING["xs"]))
        self._status_label = tk.Label(
            self._status_light_frame,
            text="Ready",
            font=TYPOGRAPHY.label.to_tk_font(),
            background=colors.window,
            foreground=colors.ink_soft,
        )
        self._status_label.pack(side="left")
        self._status_light_frame.pack(side="left", padx=(SPACING["sm"], 0))
        self._status_light_frame.pack_forget()

    def set_level(self, label: str) -> None:
        self._level_chip.set_value(label)

    def set_difficulty(self, label: str) -> None:
        self._difficulty_chip.set_value(label)

    def set_time(self, label: str) -> None:
        self._time_chip.set_value(label)

    def set_pos(self, label: str) -> None:
        self._pos_chip.set_value(label)

    def hide_hard_mode_status(self) -> None:
        """Hide the status light -- HARD is off."""
        self._status_light_frame.pack_forget()

    def show_hard_mode_status(self, *, moving: bool, ready_color: str, moving_color: str) -> None:
        """Pack in and recolor the status light -- HARD is on.

        `screen.py` only reads/passes fresh colors (`_hard_mode_colors()`)
        when HARD is actually on, and only calls this when `(hard, moving)`
        changed (`_last_hard_sync_state`) -- so every call here does real
        work.
        """
        self._status_light_frame.pack(side="left", padx=(SPACING["sm"], 0))
        self._status_light_canvas.itemconfigure(
            self._status_light, fill=moving_color if moving else ready_color
        )
        self._status_label.configure(text="Moving" if moving else "Ready")
