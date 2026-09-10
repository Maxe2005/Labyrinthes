"""`_OutcomeBanner` -- shared inline banner for the win and timeout messages.

Both the win banner (`_on_solved`) and the timeout banner (`_on_timeout`) in
`screen.py` are the same shape (UX-DR9): an accent-bordered `Frame`, a
message `Label` on the left, and 1-2 non-primary `PillButton`s on the right
-- the first (rightmost, since `pack(side="right")` stacks inward from the
edge) gets the outer `lg` padding, any further button gets none. This
widget is that shared shape; `screen.py` decides the message, the button
set (Restart/Continue, Restart/Back to Builder, or just Continue), and
where to pack it (always `before=self._maze_frame`, non-modal and inline,
never a `messagebox`).
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from labyrinthes.adapters.tkinter.common import SPACING, TYPOGRAPHY, PillButton, Theme
from labyrinthes.adapters.tkinter.common.tokens import colors_for

__all__ = ["_OutcomeBanner"]


class _OutcomeBanner(tk.Frame):
    """An accent-bordered inline message + right-aligned action buttons.

    Not packed by itself -- the caller packs it (`screen.py` always packs
    with `before=self._maze_frame`, matching both the win and timeout
    banner's placement just above the maze).
    """

    def __init__(
        self,
        parent: tk.Widget,
        *,
        theme: Theme,
        message: str,
        buttons: list[tuple[str, Callable[[], None]]],
    ) -> None:
        colors = colors_for(theme)
        super().__init__(
            parent,
            background=colors.accent_bg,
            highlightthickness=1,
            highlightbackground=colors.accent,
            highlightcolor=colors.accent,
        )

        tk.Label(
            self,
            text=message,
            font=TYPOGRAPHY.body.to_tk_font(),
            background=colors.accent_bg,
            foreground=colors.ink,
        ).pack(side="left", padx=SPACING["lg"], pady=SPACING["sm"])

        # Packed in order: the first button lands rightmost (`pack(side=
        # "right")` stacks inward from the edge) and alone carries the
        # outer `lg` padding; any further button packs immediately to its
        # left with none.
        for index, (label, command) in enumerate(buttons):
            padx = SPACING["lg"] if index == 0 else 0
            PillButton(
                self,
                label,
                theme=theme,
                primary=False,
                command=command,
            ).pack(side="right", padx=padx, pady=SPACING["sm"])
