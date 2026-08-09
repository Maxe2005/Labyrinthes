"""`ClassicMazeGallery` -- classic-maze browsing widget for Player's selection screen (Story 2.1).

Browses one classic maze at a time (position-based label, e.g. "Classic
Maze 4 of 12") rather than the locked mockup's 4-card thumbnail grid --
no wall-bar rendering component exists yet to draw thumbnails from (see the
story's Boundaries & Constraints). Reuses `common/`'s `IconButton`/
`PillButton` for pager/restart/play controls rather than reimplementing
per-screen buttons.

Only reads from `MazeRepository` (an `application/` port) -- never
`adapters/storage/` directly (AD-9).
"""

from __future__ import annotations

import tkinter as tk

from labyrinthes.adapters.tkinter.common.icon_btn import IconButton
from labyrinthes.adapters.tkinter.common.keybindings import bind_shortcut, keybinding
from labyrinthes.adapters.tkinter.common.navigation import NavigateFn, ScreenId
from labyrinthes.adapters.tkinter.common.pill_btn import PillButton
from labyrinthes.adapters.tkinter.common.tokens import SPACING, TYPOGRAPHY, Theme, colors_for
from labyrinthes.application.maze_repository import MazeRepository
from labyrinthes.domain.maze import Maze, MazeKind

__all__ = ["ClassicMazeGallery"]

_EMPTY_STATE_MESSAGE = (
    "No classic mazes were found. Build one in the Builder, or play a random maze now."
)


class ClassicMazeGallery(tk.Frame):
    """Browse-one-classic-maze-at-a-time picker, plus a generate-random entry point.

    Populated state (`maze_repository.list_names(MazeKind.CLASSIC)` non-empty):
    a position label ("Classic Maze {i+1} of {n}"), Previous/Next
    `IconButton`s clamped at the bounds (no wraparound, no-op past either
    end), a Restart `IconButton` jumping back to index 0, a jump-to-number
    `Entry` bound to `<Return>` (reverts its text on an invalid/out-of-range
    number, leaving the browsed index unchanged), and a primary "Play"
    `PillButton` that loads the browsed name and calls
    `navigate(ScreenId.PLAYER, maze)`.

    Empty state (no classics saved yet): an inline message, no pager/Play
    controls.

    Both states show a "Generate random" primary `PillButton` (kbd "N")
    wired to a documented no-op placeholder -- Story 2.2 wires real
    generation, the same "placeholder for a later story to complete"
    pattern Story 1.7 already established for whole screens.
    """

    def __init__(
        self,
        parent: tk.Widget,
        *,
        theme: Theme,
        maze_repository: MazeRepository,
        navigate: NavigateFn,
    ) -> None:
        colors = colors_for(theme)
        super().__init__(parent, background=colors.window)
        self._theme = theme
        self._maze_repository = maze_repository
        self._navigate = navigate
        self._names: list[str] = maze_repository.list_names(MazeKind.CLASSIC)
        self._index = 0

        if self._names:
            self._build_populated()
        else:
            self._build_empty_state()

        self._build_generate_random_zone()

    # -- populated state ---------------------------------------------------

    def _build_populated(self) -> None:
        colors = colors_for(self._theme)

        header = tk.Frame(self, background=colors.window)
        header.pack(fill="x", pady=(0, SPACING["md"]))

        self._position_label = tk.Label(
            header,
            text=self._position_text(),
            font=TYPOGRAPHY.body.to_tk_font(),
            background=colors.window,
            foreground=colors.ink,
        )
        self._position_label.pack(side="left")

        pager = tk.Frame(header, background=colors.window)
        pager.pack(side="right")

        self._previous_button = IconButton(
            pager,
            glyph="◀",
            theme=self._theme,
            tooltip="Previous classic maze.",
            command=self._on_previous,
        )
        self._previous_button.pack(side="left", padx=(0, SPACING["xs"]))

        self._restart_button = IconButton(
            pager,
            glyph="⟲",
            theme=self._theme,
            tooltip="Restart at the first classic maze.",
            command=self._on_restart,
        )
        self._restart_button.pack(side="left", padx=(0, SPACING["xs"]))

        self._jump_entry = tk.Entry(pager, width=4, justify="center")
        self._jump_entry.insert(0, str(self._index + 1))
        self._jump_entry.pack(side="left", padx=(0, SPACING["xs"]))
        self._jump_entry.bind("<Return>", self._on_jump)
        # Consume "n"/"N" locally before they reach the global
        # `generate_random` shortcut's `bind_all()` handler (Tk fires
        # widget-instance bindings before `bind_all` ones, and a `"break"`
        # return stops it there) -- otherwise typing "n" while this field
        # has focus both inserts the character and fires generate-random.
        self._jump_entry.bind("<KeyPress-n>", lambda _event: "break")
        self._jump_entry.bind("<KeyPress-N>", lambda _event: "break")

        self._next_button = IconButton(
            pager, glyph="▶", theme=self._theme, tooltip="Next classic maze.", command=self._on_next
        )
        self._next_button.pack(side="left")

        self._size_label = tk.Label(
            self,
            text=self._size_text(),
            font=TYPOGRAPHY.body_secondary.to_tk_font(),
            background=colors.window,
            foreground=colors.ink_soft,
        )
        self._size_label.pack(anchor="w", pady=(0, SPACING["lg"]))

        self._play_button = PillButton(
            self, "Play", theme=self._theme, primary=True, command=self._on_play
        )
        self._play_button.pack(anchor="w")

    def _position_text(self) -> str:
        return f"Classic Maze {self._index + 1} of {len(self._names)}"

    def _size_text(self) -> str:
        maze = self._current_maze()
        return f"{maze.grid.width}×{maze.grid.height}"

    def _current_maze(self) -> Maze:
        name = self._names[self._index]
        return self._maze_repository.load(name, MazeKind.CLASSIC)

    def _refresh_display(self) -> None:
        self._position_label.configure(text=self._position_text())
        self._jump_entry.delete(0, "end")
        self._jump_entry.insert(0, str(self._index + 1))
        self._size_label.configure(text=self._size_text())

    def _on_previous(self) -> None:
        # Clamped at the lower bound -- a no-op past index 0, never wraps
        # (see the story's I/O matrix).
        if self._index > 0:
            self._index -= 1
            self._refresh_display()

    def _on_next(self) -> None:
        # Clamped at the upper bound -- a no-op past the last index, never
        # wraps (see the story's I/O matrix).
        if self._index < len(self._names) - 1:
            self._index += 1
            self._refresh_display()

    def _on_restart(self) -> None:
        self._index = 0
        self._refresh_display()

    def _on_jump(self, _event: tk.Event | None = None) -> None:
        """Jump to the 1-based number in the entry, or revert it if invalid.

        A valid jump is a plain integer within `[1, len(self._names)]`.
        Anything else (non-numeric text, out-of-range) leaves the browsed
        index untouched and reverts the entry's displayed text back to it
        -- no exception raised, no state change (see the story's I/O
        matrix).
        """
        text = self._jump_entry.get()
        try:
            number = int(text)
        except ValueError:
            number = None

        if number is not None and 1 <= number <= len(self._names):
            self._index = number - 1
            self._refresh_display()
        else:
            self._jump_entry.delete(0, "end")
            self._jump_entry.insert(0, str(self._index + 1))

    def _on_play(self) -> None:
        maze = self._current_maze()
        self._navigate(ScreenId.PLAYER, maze)

    # -- empty state ---------------------------------------------------

    def _build_empty_state(self) -> None:
        colors = colors_for(self._theme)
        tk.Label(
            self,
            text=_EMPTY_STATE_MESSAGE,
            font=TYPOGRAPHY.body_secondary.to_tk_font(),
            background=colors.window,
            foreground=colors.ink_soft,
            wraplength=420,
            justify="left",
        ).pack(anchor="w", pady=(0, SPACING["lg"]))

    # -- generate-random (shown in both states) ----------------------------

    def _build_generate_random_zone(self) -> None:
        generate_kb = keybinding("generate_random")
        self._generate_random_button = PillButton(
            self,
            generate_kb.label,
            theme=self._theme,
            primary=True,
            shortcut=generate_kb.display,
            command=self._on_generate_random,
        )
        self._generate_random_button.pack(anchor="w", pady=(SPACING["lg"], 0))
        bind_shortcut(self, generate_kb, self._on_generate_random)

    def _on_generate_random(self) -> None:
        """No-op placeholder -- Story 2.2 wires real random-maze generation.

        Mirrors Story 1.7's "placeholder for a later story to complete"
        pattern, applied to a single control instead of a whole screen.
        """
