"""Builder edit screen (Story 3.2).

`mount()` dispatches on `state` exactly like `player/screen.py`: `state is
None` opens `NewMazeDialog` as the entry state (nothing else renders --
the maze-frame stays empty until the user confirms dimensions, mirroring
`home/screen.py`'s own "New Maze" entry point); `state is a Maze` builds
the full edit UI via `_BuilderEditArea`. Confirming the dialog forwards
the freshly-built `Maze` to `navigate(ScreenId.BUILDER, maze)`, re-running
`mount()` with `state=maze` -- Builder never re-packs in place.

`_BuilderEditArea` owns one adapter-local `BuilderSession` (Epic 3
Technical Decisions' "adapter-local mutable session wrapper... around the
immutable `Maze` value") and wires:
- A left `ToolButtonGroup` side bar: Break Wall / Pass-through, mutually
  exclusive, mirrored by the `break_wall`/`pass_through` keybindings
  (`ScreenId.BUILDER`-scoped, so 'b'/'p' can also mean Home's
  `open_builder`/`open_player` without collision -- see
  `common/keybindings.py`'s `scope` field).
- A center column: `HudChip`s for grid size + live "Walls broken", above
  `_BuilderMazeCanvas`.
- Arrow-key cursor movement, reusing the existing (scope-less)
  `move_up`/`move_down`/`move_left`/`move_right` entries -- Builder and
  Player are never mounted simultaneously, so no scope is needed there.

Never imports `home`/`player` or `adapters/storage/` (AD-1, AD-9).
"""

from __future__ import annotations

import functools
import tkinter as tk
from collections.abc import Callable

from labyrinthes.adapters.tkinter.common import (
    SPACING,
    BreadcrumbSegment,
    HudChip,
    NavigateFn,
    NewMazeDialog,
    ScreenId,
    SettingsWindow,
    Theme,
    ToggleThemeFn,
    ToolButton,
    ToolButtonGroup,
    TopBar,
    bind_shortcut,
    keybinding,
)
from labyrinthes.adapters.tkinter.common.tokens import ColorTokens, colors_for
from labyrinthes.application.builder_session import (
    BuilderSession,
    BuilderTool,
    apply_wall_toggle,
    broken_wall_count,
    move_cursor,
    set_tool,
    start_builder_session,
)
from labyrinthes.application.settings_repository import SettingsRepository
from labyrinthes.domain.errors import DomainValidationError
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.level_visibility import Wall
from labyrinthes.domain.maze import Maze
from labyrinthes.domain.movement import Direction
from labyrinthes.domain.position import Position

__all__ = ["mount"]

_MAX_CANVAS_SPAN = 480
_MIN_CELL_SIZE = 16
_MAX_CELL_SIZE = 40
_WALL_WIDTH = 2
# Search radius (px) `find_closest()` accepts around a click -- without it,
# a click meant for a *broken* (gap) wall would have to land exactly on the
# invisible hairline drawn there (see `_BuilderMazeCanvas._draw_wall_bar`).
_CLICK_HALO = 6

_DIRECTION_ACTION_IDS: tuple[tuple[str, Direction], ...] = (
    ("move_up", Direction.UP),
    ("move_down", Direction.DOWN),
    ("move_left", Direction.LEFT),
    ("move_right", Direction.RIGHT),
)


def _cell_size(width: int, height: int) -> int:
    """`clamp(min(480 // width, 480 // height), 16, 40)` px -- same clamp as
    `player/maze_canvas.py`'s `_cell_size`, kept local per the Boundaries
    (Builder-specific widgets stay local to `adapters/tkinter/builder/`)."""
    raw = min(_MAX_CANVAS_SPAN // width, _MAX_CANVAS_SPAN // height)
    return max(_MIN_CELL_SIZE, min(_MAX_CELL_SIZE, raw))


def mount(
    parent: tk.Widget,
    state: Maze | None,
    navigate: NavigateFn,
    theme: Theme,
    toggle_theme: ToggleThemeFn,
    *,
    settings_repository: SettingsRepository,
) -> tk.Frame:
    """Build the Builder edit screen `Frame`, parented under `parent`.

    `state is None` opens `NewMazeDialog` as the entry state; `state is a
    Maze` renders the maze-frame directly with that maze already loaded
    for editing (confirming the dialog re-enters this same branch via
    `navigate(ScreenId.BUILDER, maze)`).
    """
    frame = tk.Frame(parent)

    def open_settings() -> None:
        # `parent` (not `frame`) as the `Toplevel`'s master (Story 1.11):
        # `parent` is the app's persistent container, never destroyed by
        # `Router.navigate()`, so `SettingsWindow` survives navigating away
        # from Builder instead of being torn down as a cascade side effect
        # of `frame.destroy()`. See `SettingsWindow`'s module docstring.
        SettingsWindow(parent, theme=theme, settings_repository=settings_repository)

    breadcrumb_segments = [
        BreadcrumbSegment("Home", on_click=lambda: navigate(ScreenId.HOME, None)),
        BreadcrumbSegment("Builder"),
    ]
    top_bar = TopBar(
        frame,
        theme=theme,
        breadcrumb_segments=breadcrumb_segments,
        on_settings=open_settings,
        on_theme_toggle=toggle_theme,
    )
    top_bar.pack(fill="x")

    if state is None:
        # Parented to `frame` (the calling widget), not `parent` -- like
        # Home's own `NewMazeDialog` (Story 3.1), nothing here is worth
        # surviving a navigate-away, so it is torn down with `frame` if the
        # user leaves Builder while it's still open.
        NewMazeDialog(
            frame,
            theme=theme,
            settings_repository=settings_repository,
            on_confirm=lambda maze: navigate(ScreenId.BUILDER, maze),
        )
        return frame

    edit_area = _BuilderEditArea(frame, state, theme)
    edit_area.pack(
        fill="both",
        expand=True,
        padx=SPACING["page-margin"],
        pady=SPACING["section-gap"],
    )

    return frame


class _BuilderEditArea(tk.Frame):
    """Tool side bar + HUD + maze canvas, wired to one `BuilderSession`."""

    def __init__(self, parent: tk.Widget, maze: Maze, theme: Theme) -> None:
        colors = colors_for(theme)
        super().__init__(parent, background=colors.window)
        self._theme = theme
        self._session: BuilderSession = start_builder_session(maze)

        self._build_tool_sidebar(colors)

        center = tk.Frame(self, background=colors.window)
        center.pack(side="left", fill="both", expand=True)
        self._build_hud(center, colors)
        self._build_canvas(center)

        for action_id, direction in _DIRECTION_ACTION_IDS:
            bind_shortcut(self, keybinding(action_id), functools.partial(self._on_move, direction))
        bind_shortcut(self, keybinding("break_wall"), self._activate_break)
        bind_shortcut(self, keybinding("pass_through"), self._activate_pass_through)

    # -- construction --------------------------------------------------

    def _build_tool_sidebar(self, colors: ColorTokens) -> None:
        sidebar = tk.Frame(self, background=colors.window)
        sidebar.pack(side="left", fill="y", padx=(0, SPACING["lg"]))

        group = ToolButtonGroup()
        break_kb = keybinding("break_wall")
        pass_kb = keybinding("pass_through")

        self._break_button = ToolButton(
            sidebar,
            break_kb.label,
            theme=self._theme,
            shortcut=break_kb.display,
            tooltip="Click a wall segment to break or restore it",
            group=group,
            command=self._activate_break,
        )
        self._break_button.pack(fill="x", pady=(0, SPACING["sm"]))

        self._pass_through_button = ToolButton(
            sidebar,
            pass_kb.label,
            theme=self._theme,
            shortcut=pass_kb.display,
            tooltip="Moving the cursor across a wall breaks it",
            group=group,
            command=self._activate_pass_through,
        )
        self._pass_through_button.pack(fill="x")

        # `start_builder_session()` defaults to `BuilderTool.BREAK` -- reflect
        # that in the initial button styling.
        self._break_button.set_active(True)

    def _build_hud(self, parent: tk.Widget, colors: ColorTokens) -> None:
        hud_row = tk.Frame(parent, background=colors.window)
        hud_row.pack(fill="x", pady=(0, SPACING["lg"]))

        grid = self._session.maze.grid
        self._grid_chip = HudChip(hud_row, "Grid", f"{grid.width}×{grid.height}", theme=self._theme)
        self._grid_chip.pack(side="left", padx=(0, SPACING["sm"]))

        self._walls_chip = HudChip(
            hud_row,
            "Walls broken",
            str(broken_wall_count(self._session)),
            theme=self._theme,
            live=True,
        )
        self._walls_chip.pack(side="left")

    def _build_canvas(self, parent: tk.Widget) -> None:
        self._canvas = _BuilderMazeCanvas(
            parent,
            maze=self._session.maze,
            cursor=self._session.cursor,
            theme=self._theme,
            on_wall_clicked=self._on_wall_clicked,
        )
        self._canvas.pack(fill="both", expand=True)

    # -- tool switching --------------------------------------------------

    def _activate_break(self) -> None:
        self._session = set_tool(self._session, BuilderTool.BREAK)
        self._break_button.set_active(True)

    def _activate_pass_through(self) -> None:
        self._session = set_tool(self._session, BuilderTool.PASS_THROUGH)
        self._pass_through_button.set_active(True)

    # -- editing -----------------------------------------------------

    def _on_wall_clicked(self, wall: Wall) -> None:
        # Break-mode-only: Pass-through breaks walls via cursor movement,
        # never via a direct click (Design Notes).
        if self._session.tool is not BuilderTool.BREAK:
            return
        try:
            self._session = apply_wall_toggle(self._session, wall)
        except DomainValidationError:
            # Border wall: refused, no-op (FR-2's closed-border invariant).
            return
        self._sync_after_wall_change()

    def _on_move(self, direction: Direction) -> None:
        previous_grid = self._session.maze.grid
        self._session = move_cursor(self._session, direction)
        self._canvas.set_cursor(self._session.cursor)
        if self._session.maze.grid is not previous_grid:
            self._sync_after_wall_change()

    def _sync_after_wall_change(self) -> None:
        self._canvas.refresh_walls(self._session.maze.grid)
        self._walls_chip.set_value(str(broken_wall_count(self._session)))


class _BuilderMazeCanvas(tk.Canvas):
    """Renders every wall position (border + interior) as a bar/gap, hit-testable
    back to its `Wall`, plus an editing-cursor rectangle.

    Every wall position gets exactly one permanent canvas line item, colored
    `colors.wall` (present) or `colors.corridor` (broken -- a gap that blends
    into the background, per the spec's "gaps for broken segments"). Editing
    only ever recolors these items (`refresh_walls()`); positions are fixed
    for the canvas's lifetime, so a gap stays clickable to restore later.
    """

    def __init__(
        self,
        parent: tk.Widget,
        *,
        maze: Maze,
        cursor: Position,
        theme: Theme,
        on_wall_clicked: Callable[[Wall], None],
    ) -> None:
        self._theme = theme
        self._on_wall_clicked = on_wall_clicked
        grid = maze.grid
        self._cell_size = _cell_size(grid.width, grid.height)
        colors = colors_for(theme)

        super().__init__(
            parent,
            width=grid.width * self._cell_size,
            height=grid.height * self._cell_size,
            background=colors.corridor,
            highlightthickness=0,
            bd=0,
        )

        self._wall_items: dict[Wall, int] = {}
        self._item_walls: dict[int, Wall] = {}
        self._draw_walls(grid, colors)
        # Drawn last so the cursor's own creation-order stacks it above
        # every wall bar/gap, permanently (wall items are only ever
        # recolored after this, never deleted/recreated).
        self._cursor_id = self._draw_cursor(cursor, colors)

        self.bind("<Button-1>", self._on_click)

    def _draw_walls(self, grid: Grid, colors: ColorTokens) -> None:
        # Only genuine wall positions: a "top" bit is only meaningful for a
        # real column (`col < width`), a "left" bit only for a real row
        # (`row < height`) -- see `domain.wall_editing.count_broken_walls`'s
        # docstring on the padding row/column's dead bits. Border positions
        # (row/col 0 or height/width) are included and drawn like any other
        # wall; clicking one is refused by `apply_wall_toggle` (caught,
        # no-op) rather than excluded from hit-testing here.
        for row in range(grid.height + 1):
            for col in range(grid.width):
                self._draw_wall_bar(Wall(row, col, "top"), grid, colors)
        for row in range(grid.height):
            for col in range(grid.width + 1):
                self._draw_wall_bar(Wall(row, col, "left"), grid, colors)

    def _wall_present(self, wall: Wall, grid: Grid) -> bool:
        cell = grid.cell_at(Position(row=wall.row, col=wall.col))
        return cell.has_top_wall if wall.side == "top" else cell.has_left_wall

    def _draw_wall_bar(self, wall: Wall, grid: Grid, colors: ColorTokens) -> None:
        size = self._cell_size
        color = colors.wall if self._wall_present(wall, grid) else colors.corridor
        x0, y0 = wall.col * size, wall.row * size
        if wall.side == "top":
            item = self.create_line(
                x0, y0, x0 + size, y0, width=_WALL_WIDTH, fill=color, tags=("wall",)
            )
        else:
            item = self.create_line(
                x0, y0, x0, y0 + size, width=_WALL_WIDTH, fill=color, tags=("wall",)
            )
        self._wall_items[wall] = item
        self._item_walls[item] = wall

    def refresh_walls(self, grid: Grid) -> None:
        """Recolor every wall bar to match `grid`'s current present/broken state."""
        colors = colors_for(self._theme)
        for wall, item in self._wall_items.items():
            color = colors.wall if self._wall_present(wall, grid) else colors.corridor
            self.itemconfigure(item, fill=color)

    def _draw_cursor(self, position: Position, colors: ColorTokens) -> int:
        size = self._cell_size
        x0, y0 = position.col * size, position.row * size
        return self.create_rectangle(
            x0,
            y0,
            x0 + size,
            y0 + size,
            outline=colors.accent,
            width=_WALL_WIDTH,
            tags=("cursor",),
        )

    def set_cursor(self, position: Position) -> None:
        """Move the cursor rectangle to `position`'s cell, without redrawing walls."""
        size = self._cell_size
        x0, y0 = position.col * size, position.row * size
        self.coords(self._cursor_id, x0, y0, x0 + size, y0 + size)

    def _on_click(self, event: tk.Event) -> None:
        hit = self.find_closest(event.x, event.y, halo=_CLICK_HALO)
        if not hit:
            return
        wall = self._item_walls.get(hit[0])
        if wall is None:
            # Closest item was the cursor rectangle, not a wall bar/gap.
            return
        self._on_wall_clicked(wall)
