"""`MazeSelectionGallery` -- Player's maze-selection screen (Story 4.14).

Rebuilds Story 2.1/2.3's one-item-at-a-time pager (`ClassicMazeGallery`,
Previous/Next/Restart/jump-to-number over a flat classic-then-saved-random
list) as one scrollable card grid, per the locked mockup's
`gallery-grid`/`maze-card` pattern that Story 2.1 originally deferred for
lack of a wall-rendering component to draw thumbnails from (`maze_canvas.py`
since Epic 3 closes that gap; `maze_wall_rendering.py` extracts its drawing
routines so `MazeCard` can reuse them at thumbnail scale).

Three independently-populated, labeled sections -- Classic, Creations,
Random (`SAVED_RANDOM`) -- each built via `common.build_group_heading` plus
a `MazeCard` grid (4 columns) inside one shared `common.ScrollableFrame`. An
empty section shows its own inline empty-state message; the other sections
render normally regardless. Every listed maze is *eagerly* loaded at
construction (one `maze_repository.load()` per card, not lazily per browsed
position like the old pager) -- a grid must render every visible thumbnail
at once, which widens the reach of the pre-existing, already-deferred
"unguarded `load()` raises `MazeNotFoundError` if a listed file was deleted
after listing" gap (not fixed here, same codebase-wide posture).

Clicking or activating (`<Return>`/`<space>`) a card calls
`navigate(ScreenId.PLAYER, MazeWithName(maze, name))` -- the same commit
path the old pager's "Play" button used, now also carrying the maze's own
saved name (Story 4.13) so Player's breadcrumb can show it -- never gated
behind a confirm dialog: Story 2.10's own precedent is that *committing* to
a maze is not "switching mazes". Story 2.10's `ConfirmDialog`-gated
Previous/Next/Restart/jump-to-number surfaces have no equivalent in a grid
and are deleted outright, not ported; the two settings that gated them
(`confirm_switch_maze`/`confirm_invalid_input`) are left defined but now
unread anywhere (see `deferred-work.md`).

"Generate random" keeps its exact pre-existing wiring
(`GenerateRandomDialog`, shortcut "N", `_on_generation_confirmed`) verbatim,
packed below the three sections as a clearly separate action -- never a
fourth section card.

Only reads from `MazeRepository`/`SettingsRepository` (`application/`
ports) -- never `adapters/storage/` directly (AD-9).
"""

from __future__ import annotations

import random
import tkinter as tk

from labyrinthes.adapters.tkinter.common.group_heading import build_group_heading
from labyrinthes.adapters.tkinter.common.keybindings import bind_shortcut, keybinding
from labyrinthes.adapters.tkinter.common.navigation import MazeWithName, NavigateFn, ScreenId
from labyrinthes.adapters.tkinter.common.pill_btn import PillButton
from labyrinthes.adapters.tkinter.common.scrollable_frame import ScrollableFrame
from labyrinthes.adapters.tkinter.common.tokens import SPACING, TYPOGRAPHY, Theme, colors_for
from labyrinthes.adapters.tkinter.player.generate_random_dialog import GenerateRandomDialog
from labyrinthes.adapters.tkinter.player.maze_card import MazeCard
from labyrinthes.application.defaults_settings import read_random_maze_defaults
from labyrinthes.application.maze_repository import MazeRepository
from labyrinthes.application.maze_size_bounds import read_maze_size_bounds
from labyrinthes.application.settings_repository import SettingsRepository
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.maze_generation import generate_random_maze
from labyrinthes.domain.position import Position

__all__ = ["MazeSelectionGallery"]

_CARDS_PER_ROW = 4

# One section definition per `MazeKind` browsed here, in the order
# rendered top-to-bottom: `(kind, section label, empty-state message)`.
_SECTIONS: tuple[tuple[MazeKind, str, str], ...] = (
    (MazeKind.CLASSIC, "Classic", "No classic mazes were found yet."),
    (
        MazeKind.CREATION,
        "Creations",
        "No Creations saved yet. Build and save one in the Builder to see it here.",
    ),
    (
        MazeKind.SAVED_RANDOM,
        "Random",
        "No saved random mazes yet. Generate one below, or save one after playing it.",
    ),
)


class MazeSelectionGallery(tk.Frame):
    """Three labeled, independently-populated `MazeCard` grids, plus generate-random.

    Each of `_SECTIONS`' three kinds gets its own heading (`build_group_heading`)
    and either a `_CARDS_PER_ROW`-column grid of `MazeCard`s (one per
    `maze_repository.list_names(kind)` entry) or, when that kind has no
    saved mazes, its own inline empty-state message -- the other sections
    are unaffected either way. The whole three-section stack lives inside a
    `ScrollableFrame`, which auto-scrolls a Tab-focused card into view (Tk's
    default focus traversal does not scroll anything on its own). Every
    heading and card also gets `ScrollableFrame.bind_wheel_recursive()`
    applied to it -- Tk delivers a wheel event to whatever's under the
    pointer, not to the scroll container itself, so without this the wheel
    would only work over the canvas's bare margin.

    A "Generate random" primary `PillButton` (kbd "N") is packed below the
    scrollable grid, outside it -- always visible, never a fourth section.
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

        self._scrollable = ScrollableFrame(self, colors=colors)
        self._scrollable.pack(fill="both", expand=True)

        for kind, label, empty_message in _SECTIONS:
            self._build_section(kind, label, empty_message)

        self._build_generate_random_zone()

    # -- sections -----------------------------------------------------

    def _build_section(self, kind: MazeKind, label: str, empty_message: str) -> None:
        colors = colors_for(self._theme)
        section = tk.Frame(self._scrollable.content, background=colors.window)
        section.pack(fill="x", pady=(0, SPACING["lg"]))

        heading = build_group_heading(section, label, colors)
        heading.pack(anchor="w", pady=(0, SPACING["sm"]))
        self._scrollable.bind_wheel_recursive(heading)

        names = self._maze_repository.list_names(kind)
        if not names:
            tk.Label(
                section,
                text=empty_message,
                font=TYPOGRAPHY.body_secondary.to_tk_font(),
                background=colors.window,
                foreground=colors.ink_soft,
                wraplength=420,
                justify="left",
            ).pack(anchor="w")
            return

        grid = tk.Frame(section, background=colors.window)
        grid.pack(fill="x")
        for column in range(_CARDS_PER_ROW):
            grid.grid_columnconfigure(column, weight=1, uniform="maze-card")

        for index, name in enumerate(names):
            maze = self._maze_repository.load(name, kind)
            card = MazeCard(
                grid,
                maze,
                name,
                theme=self._theme,
                on_activate=lambda maze=maze, name=name: self._on_card_activated(maze, name),
            )
            row, column = divmod(index, _CARDS_PER_ROW)
            card.grid(
                row=row, column=column, sticky="nsew", padx=SPACING["md"], pady=(0, SPACING["md"])
            )
            card.bind("<FocusIn>", lambda _event, card=card: self._on_card_focus(card), add="+")
            # Tk delivers a mouse-wheel event to whatever's under the
            # pointer, not to `self._scrollable._canvas` regardless of
            # where the pointer is -- without this, the wheel would only
            # scroll while over the canvas's bare margin, going dead over
            # every card. Recurses into the card's own thumbnail/name/meta
            # children too.
            self._scrollable.bind_wheel_recursive(card)

    def _on_card_focus(self, card: MazeCard) -> None:
        self._scrollable.scroll_into_view(card)

    def _on_card_activated(self, maze: Maze, name: str) -> None:
        self._navigate(ScreenId.PLAYER, MazeWithName(maze, name))

    # -- generate-random -------------------------------------------------

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
        default_columns, default_rows = read_random_maze_defaults(self._settings_repository)
        GenerateRandomDialog(
            self,
            theme=self._theme,
            bounds=bounds,
            default_columns=default_columns,
            default_rows=default_rows,
            on_confirm=self._on_generation_confirmed,
        )

    def _on_generation_confirmed(self, width: int, height: int, entry: Position) -> None:
        """Generate a random `Maze` and hand it off exactly like a card click does."""
        maze = generate_random_maze(width, height, entry, random.Random())
        self._navigate(ScreenId.PLAYER, maze)
