"""`build_maze_frame` -- the bordered frame wrapping a maze canvas (Story 4.10).

Extracted from `builder/edit_area.py`'s and `player/gameplay/screen.py`'s
identical `tk.Frame(..., highlightthickness=1, highlightbackground=
colors.border, highlightcolor=colors.border, background=colors.window)`
construction (one screen's own comment used to call this out as "the same
recipe as Player's own" -- now there is exactly one recipe, not two kept in
sync by hand). A plain function, not a widget class: callers still own
packing it (`fill="both", expand=True`, per Story 4.8, plus whatever
padding/anchor their own layout needs) and mounting their maze canvas
inside it -- this only builds the empty bordered frame.
"""

from __future__ import annotations

import tkinter as tk

from labyrinthes.adapters.tkinter.common.tokens import ColorTokens

__all__ = ["build_maze_frame"]


def build_maze_frame(parent: tk.Widget, colors: ColorTokens) -> tk.Frame:
    """An empty bordered `tk.Frame` for a caller to pack/mount a maze canvas into."""
    return tk.Frame(
        parent,
        background=colors.window,
        highlightthickness=1,
        highlightbackground=colors.border,
        highlightcolor=colors.border,
    )
