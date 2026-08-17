"""`ClassicMazeGallery` -- classic + saved-random browsing widget for Player's selection screen.

Story 2.1, extended by Story 2.3.

Browses one maze at a time (position-based label, e.g. "Classic Maze 4 of
12") rather than the locked mockup's 4-card thumbnail grid -- no wall-bar
rendering component exists yet to draw thumbnails from (see the story's
Boundaries & Constraints). Reuses `common/`'s `IconButton`/`PillButton` for
pager/restart/play controls rather than reimplementing per-screen buttons.

Only reads from `MazeRepository`/`SettingsRepository` (`application/`
ports) -- never `adapters/storage/` directly (AD-9).

Story 2.2 wires "Generate random" to a real `GenerateRandomDialog`
(parented to this widget, not the app's persistent container -- see that
module's docstring): opening it reads the FR-4 size bounds via
`read_maze_size_bounds`, and confirming it calls `generate_random_maze`
with a fresh `random.Random()` before handing the resulting `Maze` off
through the exact same `navigate(ScreenId.PLAYER, maze)` path `_on_play`
already uses.

Story 2.3 extends the browsed set beyond `MazeKind.CLASSIC`: `self._entries`
is one flat `list[tuple[MazeKind, str]]`, classic names first (so a restart
with no saved-random mazes leaves every classic-only test's "Classic Maze N
of M" position label byte-for-byte unchanged), then
`MazeKind.SAVED_RANDOM` names appended after -- one shared 1-based index
drives the position label, the jump-entry, and Previous/Next/Restart across
*both* kinds combined, not per-kind (see the story's Design Notes: this
keeps the jump-entry's typed number always matching the label's own
number). This is what makes a maze saved from the gameplay placeholder
(Story 2.3's `GameplayPlaceholder`) resurface here after an app restart --
the exact dead end the legacy player's "write but never read back" random
save reproduced.

Story 2.10 gates the browse/jump surfaces behind per-action confirmation
settings (`read_confirm_switch_maze` for Previous/Next/Restart and a valid
jump, `read_confirm_invalid_input` for the invalid-jump alert) via
`_maybe_confirm`, which opens a non-modal `ConfirmDialog` (parented to this
gallery, so it cascade-destroys with it on navigate-away) and guards against
stacking a second dialog while one is open (`_confirm_dialog is not None`
-> no-op). Each gated action reads its setting *at action time* -- never
cached at mount -- which is what makes a Settings toggle take effect without
an app restart (AC-3). `_on_play`/`_on_generate_random` stay ungated:
committing to the shown maze / opening the generation dialog is not
"switching mazes".
"""

from __future__ import annotations

import random
import tkinter as tk
from collections.abc import Callable

from labyrinthes.adapters.tkinter.common.confirm_dialog import ConfirmDialog
from labyrinthes.adapters.tkinter.common.icon_btn import IconButton
from labyrinthes.adapters.tkinter.common.keybindings import bind_shortcut, keybinding
from labyrinthes.adapters.tkinter.common.navigation import NavigateFn, ScreenId
from labyrinthes.adapters.tkinter.common.pill_btn import PillButton
from labyrinthes.adapters.tkinter.common.tokens import SPACING, TYPOGRAPHY, Theme, colors_for
from labyrinthes.adapters.tkinter.player.generate_random_dialog import GenerateRandomDialog
from labyrinthes.application.confirmation_settings import (
    read_confirm_invalid_input,
    read_confirm_switch_maze,
)
from labyrinthes.application.maze_repository import MazeRepository
from labyrinthes.application.maze_size_bounds import read_maze_size_bounds
from labyrinthes.application.settings_repository import SettingsRepository
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.maze_generation import generate_random_maze
from labyrinthes.domain.position import Position

__all__ = ["ClassicMazeGallery"]

_EMPTY_STATE_MESSAGE = (
    "No classic or saved mazes were found. Build one in the Builder, or play a random maze now."
)

_INVALID_JUMP_MESSAGE = "That's not a valid maze number."


class ClassicMazeGallery(tk.Frame):
    """Browse-one-maze-at-a-time picker (classic, then saved-random), plus generate-random.

    Populated state (`self._entries` non-empty -- classics plus any
    `SAVED_RANDOM` mazes): a position label ("Classic Maze {i+1} of {n}" or
    "Saved Random Maze {i+1} of {n}" depending on which kind the browsed
    entry is, with {i+1}/{n} always the *overall* combined position),
    Previous/Next `IconButton`s clamped at the bounds (no wraparound, no-op
    past either end), a Restart `IconButton` jumping back to index 0, a
    jump-to-number `Entry` bound to `<Return>` (reverts its text on an
    invalid/out-of-range number, leaving the browsed index unchanged), and a
    primary "Play" `PillButton` that loads the browsed entry and calls
    `navigate(ScreenId.PLAYER, maze)`.

    Empty state (neither classics nor saved-random mazes exist yet): an
    inline message, no pager/Play controls.

    Both states show a "Generate random" primary `PillButton` (kbd "N")
    that opens a `GenerateRandomDialog`; confirming it generates and
    navigates to a fresh random `Maze` the same way `_on_play` hands off a
    browsed entry.
    """

    def __init__(
        self,
        parent: tk.Widget,
        *,
        theme: Theme,
        maze_repository: MazeRepository,
        settings_repository: SettingsRepository,
        navigate: NavigateFn,
    ) -> None:
        colors = colors_for(theme)
        super().__init__(parent, background=colors.window)
        self._theme = theme
        self._maze_repository = maze_repository
        self._settings_repository = settings_repository
        self._navigate = navigate
        # Classics first (so a restart with no saved-random mazes leaves
        # every classic-only test's numbering byte-for-byte unchanged), then
        # saved-random -- one flat, kind-aware list driving one shared
        # 1-based index (see the module docstring's Story 2.3 note).
        self._entries: list[tuple[MazeKind, str]] = [
            (MazeKind.CLASSIC, name) for name in maze_repository.list_names(MazeKind.CLASSIC)
        ] + [
            (MazeKind.SAVED_RANDOM, name)
            for name in maze_repository.list_names(MazeKind.SAVED_RANDOM)
        ]
        self._index = 0
        # Story 2.10: the open `ConfirmDialog`, if any -- `None` when no
        # prompt is showing. The `_maybe_confirm` guard (`is not None` ->
        # no-op) is what stops a second gated trigger from stacking a second
        # dialog on top of the first (the dialog is non-modal, so clicks can
        # still reach this screen -- see `confirm_dialog.py`'s docstring).
        self._confirm_dialog: ConfirmDialog | None = None

        if self._entries:
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
            tooltip="Previous maze.",
            command=self._on_previous,
        )
        self._previous_button.pack(side="left", padx=(0, SPACING["xs"]))

        self._restart_button = IconButton(
            pager,
            glyph="⟲",
            theme=self._theme,
            tooltip="Restart at the first maze.",
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
            pager, glyph="▶", theme=self._theme, tooltip="Next maze.", command=self._on_next
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
        kind, _name = self._entries[self._index]
        label = "Classic Maze" if kind is MazeKind.CLASSIC else "Saved Random Maze"
        return f"{label} {self._index + 1} of {len(self._entries)}"

    def _size_text(self) -> str:
        maze = self._current_maze()
        return f"{maze.grid.width}×{maze.grid.height}"

    def _current_maze(self) -> Maze:
        kind, name = self._entries[self._index]
        return self._maze_repository.load(name, kind)

    def _refresh_display(self) -> None:
        self._position_label.configure(text=self._position_text())
        self._jump_entry.delete(0, "end")
        self._jump_entry.insert(0, str(self._index + 1))
        self._size_label.configure(text=self._size_text())

    def _on_previous(self) -> None:
        # Clamped at the lower bound -- a no-op past index 0, never wraps
        # (see the story's I/O matrix). Gated behind `confirm_switch_maze`
        # (Story 2.10): when on, the actual index move waits for the
        # dialog's Confirm.
        self._maybe_confirm(
            read_confirm_switch_maze(self._settings_repository),
            message="Switch to the previous maze?",
            on_confirm=self._apply_previous,
        )

    def _apply_previous(self) -> None:
        if self._index > 0:
            self._index -= 1
            self._refresh_display()

    def _on_next(self) -> None:
        # Clamped at the upper bound -- a no-op past the last index, never
        # wraps (see the story's I/O matrix). Gated behind
        # `confirm_switch_maze` (Story 2.10).
        self._maybe_confirm(
            read_confirm_switch_maze(self._settings_repository),
            message="Switch to the next maze?",
            on_confirm=self._apply_next,
        )

    def _apply_next(self) -> None:
        if self._index < len(self._entries) - 1:
            self._index += 1
            self._refresh_display()

    def _on_restart(self) -> None:
        # Gated behind `confirm_switch_maze` like previous/next (Story
        # 2.10): restarting changes the selected maze, so it prompts under
        # the same setting.
        self._maybe_confirm(
            read_confirm_switch_maze(self._settings_repository),
            message="Restart at the first maze?",
            on_confirm=self._apply_restart,
        )

    def _apply_restart(self) -> None:
        self._index = 0
        self._refresh_display()

    def _on_jump(self, _event: tk.Event | None = None) -> None:
        """Jump to the 1-based number in the entry, or revert it if invalid.

        A valid jump is a plain integer within `[1, len(self._entries)]`
        (the overall combined position, spanning classic then saved-random
        entries -- see the module docstring's Story 2.3 note). Anything
        else (non-numeric text, out-of-range) leaves the browsed index
        untouched and reverts the entry's displayed text back to it -- no
        exception raised, no state change (see the story's I/O matrix).

        Story 2.10: the valid branch is gated behind `confirm_switch_maze`;
        the invalid branch reverts immediately (the revert is not a gate)
        and then shows an OK-only alert when `confirm_invalid_input` is on
        (the legacy `alerte mauvaise entree`, alert-mode `ConfirmDialog`).
        """
        text = self._jump_entry.get()
        try:
            number = int(text)
        except ValueError:
            number = None

        if number is not None and 1 <= number <= len(self._entries):
            self._maybe_confirm(
                read_confirm_switch_maze(self._settings_repository),
                message=f"Jump to maze {number}?",
                on_confirm=lambda: self._apply_jump(number),
            )
        else:
            self._jump_entry.delete(0, "end")
            self._jump_entry.insert(0, str(self._index + 1))
            self._maybe_confirm(
                read_confirm_invalid_input(self._settings_repository),
                message=_INVALID_JUMP_MESSAGE,
                confirm_label="OK",
                cancel_label=None,
            )

    def _apply_jump(self, number: int) -> None:
        self._index = number - 1
        self._refresh_display()

    def _maybe_confirm(
        self,
        enabled: bool,
        *,
        message: str,
        on_confirm: Callable[[], None] | None = None,
        confirm_label: str = "Confirm",
        cancel_label: str | None = "Cancel",
    ) -> None:
        """Gate an action behind a `ConfirmDialog` when `enabled`.

        Never stacks: a second trigger while a dialog is already open is a
        no-op (the dialog is non-modal, so a click could otherwise reach
        this screen behind it). When `enabled`, opens the dialog and stores
        it so the owning action's `on_confirm` only runs on Confirm; when
        `enabled` is `False`, runs `on_confirm` immediately (the action
        applies with no prompt -- AC-2). `on_close` clears the guard.
        """
        if self._confirm_dialog is not None:
            return
        if enabled:
            self._confirm_dialog = ConfirmDialog(
                self,
                theme=self._theme,
                message=message,
                on_confirm=on_confirm,
                on_close=self._clear_confirm_dialog,
                confirm_label=confirm_label,
                cancel_label=cancel_label,
            )
        elif on_confirm is not None:
            on_confirm()

    def _clear_confirm_dialog(self) -> None:
        self._confirm_dialog = None

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
        """Open a `GenerateRandomDialog`, pre-filled from the shared FR-4 size bounds.

        Parented to `self` (this gallery), not the app's persistent
        container unlike `SettingsWindow` -- nothing in the dialog's state
        is worth surviving a navigate-away.
        """
        bounds = read_maze_size_bounds(self._settings_repository)
        GenerateRandomDialog(
            self,
            theme=self._theme,
            bounds=bounds,
            on_confirm=self._on_generation_confirmed,
        )

    def _on_generation_confirmed(self, width: int, height: int, entry: Position) -> None:
        """Generate a random `Maze` and hand it off exactly like `_on_play` does."""
        maze = generate_random_maze(width, height, entry, random.Random())
        self._navigate(ScreenId.PLAYER, maze)
