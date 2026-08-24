"""Builder edit screen (Stories 3.2/3.3/3.4).

from __future__ import annotations

from dataclasses import dataclass, replace

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
- A left `ToolButtonGroup` side bar: Break Wall / Pass-through / Destroy
  Zone / Restore Zone / Set Entry / Set Exit, mutually exclusive, mirrored
  by the `break_wall`/`pass_through`/`destroy_zone`/`restore_zone`/
  `set_entry`/`set_exit` keybindings (`ScreenId.BUILDER`-scoped, so
  'b'/'p' can also mean Home's `open_builder`/`open_player` while
  'd'/'r'/'e'/'x' are Builder-only -- see `common/keybindings.py`'s
  `scope` field).
- A center column: `HudChip`s for grid size + live "Walls broken", above
  `_BuilderMazeCanvas`.
- A HUD row trailing `pill-btn`s: the primary Save pill plus the
  non-primary Test in Player pill (Story 3.8), both mirroring the
  `save_maze`/`test_in_player` keybindings ('s'/'t', `ScreenId.BUILDER`) --
  the `test_in_player` binding hands the in-progress `Maze` to the Player
  via `navigate(ScreenId.PLAYER, BuilderTestLaunch(maze, entry, exit))`,
  with no serialization or save required first. It is gated on the exit
  being set (a blocked alert-mode `ConfirmDialog` otherwise, mirroring
  `save_maze`), and the payload carries the session's `entry`/`exit`
  markers so a "Back to Builder" return restores them exactly.
- Arrow-key cursor movement, reusing the existing (scope-less)
  `move_up`/`move_down`/`move_left`/`move_right` entries -- Builder and
  Player are never mounted simultaneously, so no scope is needed there.
- Click-and-drag zone editing (Story 3.3): `_BuilderMazeCanvas` compares
  the press cell to the release cell (both cell-quantized via
  `_pixel_to_cell`) and fires `on_zone_dragged` only when they differ --
  a same-cell click is never a zone operation, no separate pixel-distance
  threshold. The active tool is captured at *press* time (via
  `capture_tool`) and threaded through to `on_zone_dragged`/
  `apply_zone_operation` unchanged, rather than re-read live at release
  time -- so switching tools mid-drag (e.g. a keybinding fired while the
  button is still held) can never compound a press-time action under one
  tool with a release-time zone operation under a different one.
  `_on_zone_dragged` gates on the captured tool being
  `DESTROY_ZONE`/`RESTORE_ZONE`, so a drag while Break/Pass-through was
  active at press time is ignored.
- Entry/exit marking (Story 3.4): the Set Entry / Set Exit tools place
  optional session markers -- entry on any cell, exit on a border cell
  only (a non-border click is a no-op; `apply_set_exit`'s
  `DomainValidationError` is swallowed, mirroring `_on_wall_clicked`).
  Placement reuses the press/release cell comparison: `_on_release` fires
  `on_cell_clicked` only for a same-cell press-captured marker tool, so a
  stray drag never misplaces a marker. Redefining an existing marker at a
  different cell is gated behind the `builder`-scope
  `read_confirm_redefine_marker` setting (default `True`) via the shared
  non-modal `ConfirmDialog` (the `_maybe_confirm` guard pattern from
  `player/gameplay_screen.py`); clicking the marker's own cell is a no-op
  with no prompt. The `_BuilderMazeCanvas` renders the entry as a filled
  circle (`colors.entry`), the exit as a filled diamond (`colors.exit`),
  and, only while Set Exit is active, a dashed-`?` ghost preview
  (`colors.ghost`) at the cursor cell when that cell is on the border and
  holds no marker -- `_BuilderEditArea._on_move` re-syncs markers via
  `_sync_markers` so the ghost tracks the cursor, and it never rests on a
  placeholder for an unset exit nor on a cell already carrying a marker.

Never imports `home`/`player` or `adapters/storage/` (AD-1, AD-9).
"""

from __future__ import annotations

import functools
import tkinter as tk
from collections.abc import Callable
from dataclasses import replace

from labyrinthes.adapters.tkinter.common import (
    SPACING,
    TYPOGRAPHY,
    BreadcrumbSegment,
    BuilderTestLaunch,
    ConfirmDialog,
    FontSpec,
    HudChip,
    NavigateFn,
    NewMazeDialog,
    PillButton,
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
    apply_set_entry,
    apply_set_exit,
    apply_wall_toggle,
    apply_zone_operation,
    broken_wall_count,
    move_cursor,
    set_tool,
    start_builder_session,
)
from labyrinthes.application.confirmation_settings import read_confirm_redefine_marker
from labyrinthes.application.maze_repository import MazeRepository
from labyrinthes.application.settings_repository import SettingsRepository
from labyrinthes.domain.errors import DomainValidationError
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.level_visibility import Wall, is_border_cell
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.movement import Direction
from labyrinthes.domain.position import Position

# Kinds `MazeRepository.save()` mints a `MazeId` for (AD-3/AD-6) -- a maze
# save promotes any other kind (in practice, only `SKETCH`: the Builder
# never opens a `GENERATED` maze) to `CLASSIC`; an already-eligible kind
# (a future Edit-in-Builder resave, Story 3.9) is left as-is so its
# existing id is carried forward, not re-minted.
_ID_ELIGIBLE_KINDS = frozenset({MazeKind.CLASSIC, MazeKind.SAVED_RANDOM})

__all__ = ["mount"]

_MAX_CANVAS_SPAN = 480
_MIN_CELL_SIZE = 16
_MAX_CELL_SIZE = 40
_WALL_WIDTH = 2
# Fraction of a cell a marker's radius spans -- same scale as the Player's
# `maze_canvas._MARKER_SCALE` (Story 3.4's marker geometry reference).
_MARKER_SCALE = 0.6
# Fraction of a cell the Set Exit ghost's dashed outline is inset from the
# cell edge (scales with the cell so it never overflows the smallest cells).
_GHOST_INSET_SCALE = 0.25
# Fraction of a cell the ghost's "?" glyph's font size spans.
_GHOST_FONT_SCALE = 0.55
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
    state: Maze | None | BuilderTestLaunch,
    navigate: NavigateFn,
    theme: Theme,
    toggle_theme: ToggleThemeFn,
    *,
    settings_repository: SettingsRepository,
    maze_repository: MazeRepository,
) -> tk.Frame:
    """Build the Builder edit screen `Frame`, parented under `parent`.

    `state is None` opens `NewMazeDialog` as the entry state; `state is a
    Maze` renders the maze-frame directly with that maze already loaded
    for editing (confirming the dialog re-enters this same branch via
    `navigate(ScreenId.BUILDER, maze)`); `state is a BuilderTestLaunch`
    (the "Test in Player" round-trip) renders the same edit UI with the
    launch's `maze` and restores the session's `entry`/`exit` markers from
    the payload.

    `maze_repository` (Story 3.6) is required and keyword-only, mirroring
    `player/screen.py`'s own `mount()` -- the Save flow needs it to persist
    Sketches/Mazes and to duplicate-name-check via `list_names()`/`load()`.
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

    maze = state.maze if isinstance(state, BuilderTestLaunch) else state
    entry = state.entry if isinstance(state, BuilderTestLaunch) else None
    exit_marker = state.exit if isinstance(state, BuilderTestLaunch) else None
    edit_area = _BuilderEditArea(
        frame,
        maze,
        theme,
        navigate=navigate,
        settings_repository=settings_repository,
        maze_repository=maze_repository,
        entry=entry,
        exit=exit_marker,
    )
    edit_area.pack(
        fill="both",
        expand=True,
        padx=SPACING["page-margin"],
        pady=SPACING["section-gap"],
    )

    return frame


class _BuilderEditArea(tk.Frame):
    """Tool side bar + HUD + maze canvas, wired to one `BuilderSession`."""

    def __init__(
        self,
        parent: tk.Widget,
        maze: Maze,
        theme: Theme,
        *,
        navigate: NavigateFn,
        settings_repository: SettingsRepository,
        maze_repository: MazeRepository,
        entry: Position | None = None,
        exit: Position | None = None,
    ) -> None:
        colors = colors_for(theme)
        super().__init__(parent, background=colors.window)
        self._parent = parent
        self._theme = theme
        self._navigate = navigate
        self._settings_repository = settings_repository
        self._maze_repository = maze_repository
        self._session: BuilderSession = start_builder_session(maze, entry=entry, exit=exit)
        # The open marker-redefinition `ConfirmDialog`, if any -- `None`
        # when no prompt is showing (Story 3.4). `_maybe_confirm`'s guard
        # (`is not None` -> no-op) stops a second gated trigger from
        # stacking a second dialog (the dialog is non-modal, so clicks can
        # still reach this screen -- see `confirm_dialog.py`'s docstring).
        self._confirm_dialog: ConfirmDialog | None = None

        self._build_tool_sidebar(colors)

        center = tk.Frame(self, background=colors.window)
        center.pack(side="left", fill="both", expand=True)
        self._build_hud(center, colors)
        self._build_canvas(center)

        for action_id, direction in _DIRECTION_ACTION_IDS:
            bind_shortcut(self, keybinding(action_id), functools.partial(self._on_move, direction))
        bind_shortcut(self, keybinding("break_wall"), self._activate_break)
        bind_shortcut(self, keybinding("pass_through"), self._activate_pass_through)
        bind_shortcut(self, keybinding("destroy_zone"), self._activate_destroy_zone)
        bind_shortcut(self, keybinding("restore_zone"), self._activate_restore_zone)
        bind_shortcut(self, keybinding("set_entry"), self._activate_set_entry)
        bind_shortcut(self, keybinding("set_exit"), self._activate_set_exit)
        bind_shortcut(self, keybinding("save_maze"), self.save_maze)
        bind_shortcut(self, keybinding("test_in_player"), self._test_in_player)

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

        destroy_kb = keybinding("destroy_zone")
        restore_kb = keybinding("restore_zone")

        self._destroy_zone_button = ToolButton(
            sidebar,
            destroy_kb.label,
            theme=self._theme,
            shortcut=destroy_kb.display,
            tooltip="Click-and-drag across a rectangle to break every wall inside it",
            group=group,
            command=self._activate_destroy_zone,
        )
        self._destroy_zone_button.pack(fill="x", pady=(SPACING["sm"], 0))

        self._restore_zone_button = ToolButton(
            sidebar,
            restore_kb.label,
            theme=self._theme,
            shortcut=restore_kb.display,
            tooltip="Click-and-drag across a rectangle to restore every wall inside it",
            group=group,
            command=self._activate_restore_zone,
        )
        self._restore_zone_button.pack(fill="x", pady=(SPACING["sm"], 0))

        entry_kb = keybinding("set_entry")
        exit_kb = keybinding("set_exit")

        self._set_entry_button = ToolButton(
            sidebar,
            entry_kb.label,
            theme=self._theme,
            shortcut=entry_kb.display,
            tooltip="Click a cell to mark it as the maze entry",
            group=group,
            command=self._activate_set_entry,
        )
        self._set_entry_button.pack(fill="x", pady=(SPACING["sm"], 0))

        self._set_exit_button = ToolButton(
            sidebar,
            exit_kb.label,
            theme=self._theme,
            shortcut=exit_kb.display,
            tooltip="Click a border cell to mark it as the maze exit",
            group=group,
            command=self._activate_set_exit,
        )
        self._set_exit_button.pack(fill="x", pady=(SPACING["sm"], 0))

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

        # "Draft" status (AC3, Story 3.6): shown only for a `SKETCH`-kind
        # maze -- set once, at construction, from the maze this area was
        # built with. A save always re-`navigate()`s to a freshly mounted
        # `_BuilderEditArea` (see `save_maze`), so this never goes stale --
        # there is no in-place chip update to keep in sync.
        if self._session.maze.kind is MazeKind.SKETCH:
            self._status_chip: HudChip | None = HudChip(
                hud_row, "Status", "Draft", theme=self._theme
            )
            self._status_chip.pack(side="left", padx=(SPACING["sm"], 0))
        else:
            self._status_chip = None

        # The single primary `pill-btn` for this screen (Epic 3's UX
        # pattern: "exactly one primary pill-btn per screen -- New Maze,
        # Save"), placed in the screen body like Home's own "New Maze"
        # pill (`home/screen.py`), not inside the shared `TopBar` (which
        # carries only the brand/breadcrumb/icon-btns, per `top_bar.py`).
        save_kb = keybinding("save_maze")
        PillButton(
            hud_row,
            save_kb.label,
            theme=self._theme,
            primary=True,
            shortcut=save_kb.display,
            command=self.save_maze,
        ).pack(side="right")

        # Non-primary variant (exactly one primary `pill-btn` per screen):
        # Save keeps `primary=True`; Test in Player is the default style.
        test_kb = keybinding("test_in_player")
        PillButton(
            hud_row,
            test_kb.label,
            theme=self._theme,
            shortcut=test_kb.display,
            command=self._test_in_player,
        ).pack(side="right")

    def _build_canvas(self, parent: tk.Widget) -> None:
        self._canvas = _BuilderMazeCanvas(
            parent,
            maze=self._session.maze,
            cursor=self._session.cursor,
            theme=self._theme,
            on_wall_clicked=self._on_wall_clicked,
            on_zone_dragged=self._on_zone_dragged,
            on_cell_clicked=self._on_cell_clicked,
            capture_tool=lambda: self._session.tool,
        )
        self._canvas.pack(fill="both", expand=True)
        self._sync_markers()

    # -- tool switching --------------------------------------------------

    def _activate_break(self) -> None:
        self._session = set_tool(self._session, BuilderTool.BREAK)
        self._break_button.set_active(True)
        self._sync_markers()

    def _activate_pass_through(self) -> None:
        self._session = set_tool(self._session, BuilderTool.PASS_THROUGH)
        self._pass_through_button.set_active(True)
        self._sync_markers()

    def _activate_destroy_zone(self) -> None:
        self._session = set_tool(self._session, BuilderTool.DESTROY_ZONE)
        self._destroy_zone_button.set_active(True)
        self._sync_markers()

    def _activate_restore_zone(self) -> None:
        self._session = set_tool(self._session, BuilderTool.RESTORE_ZONE)
        self._restore_zone_button.set_active(True)
        self._sync_markers()

    def _activate_set_entry(self) -> None:
        self._session = set_tool(self._session, BuilderTool.SET_ENTRY)
        self._set_entry_button.set_active(True)
        self._sync_markers()

    def _activate_set_exit(self) -> None:
        self._session = set_tool(self._session, BuilderTool.SET_EXIT)
        self._set_exit_button.set_active(True)
        self._sync_markers()

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

    def _on_zone_dragged(self, tool: BuilderTool, anchor: Position, end: Position) -> None:
        # Zone-tool-only: a Break/Pass-through drag never triggers a zone
        # operation (Story 3.3's Boundaries -- zone dispatch gates on the
        # active tool, same as `_on_wall_clicked` gates on `BREAK`).
        # `tool` is the tool captured at press time (`_BuilderMazeCanvas`'s
        # `capture_tool`), not a live re-read of `self._session.tool` --
        # see the module docstring's "switching tools mid-drag" note.
        if tool not in (BuilderTool.DESTROY_ZONE, BuilderTool.RESTORE_ZONE):
            return
        self._session = apply_zone_operation(self._session, tool, anchor, end)
        self._sync_after_wall_change()

    def _on_move(self, direction: Direction) -> None:
        previous_grid = self._session.maze.grid
        self._session = move_cursor(self._session, direction)
        self._canvas.set_cursor(self._session.cursor)
        # The Set Exit ghost follows the cursor (border cells only) -- see
        # `_sync_markers`.
        self._sync_markers()
        if self._session.maze.grid is not previous_grid:
            self._sync_after_wall_change()

    def _on_cell_clicked(self, tool: BuilderTool, position: Position) -> None:
        # Marker-tool-only (the canvas only fires `on_cell_clicked` for a
        # press-captured SET_ENTRY/SET_EXIT); dispatch on the captured
        # `tool`, not a live re-read of `session.tool`, matching
        # `_on_zone_dragged`'s press-time-gesture convention.
        if tool is BuilderTool.SET_ENTRY:
            self._place_entry(position)
        elif tool is BuilderTool.SET_EXIT:
            self._place_exit(position)
        else:
            # No marker tool active: move editing cursor directly to clicked cell
            self._session = replace(self._session, cursor=position)
            self._canvas.set_cursor(self._session.cursor)
            self._sync_markers()

    def _place_entry(self, position: Position) -> None:
        # Clicking the cell already holding the marker, or the one holding
        # the *other* marker (start and goal never share a cell), is a
        # no-op with no prompt (I/O matrix). First placement is direct --
        # only a *redefinition* at a different cell is gated by
        # `read_confirm_redefine_marker` (default `True`).
        if self._session.entry == position:
            return
        if self._session.exit == position:
            return
        on_apply = functools.partial(self._apply_set_entry, position)
        if self._session.entry is None:
            on_apply()
            return
        self._maybe_confirm(
            read_confirm_redefine_marker(self._settings_repository),
            message="Move the entry marker to this cell?",
            on_confirm=on_apply,
        )

    def _place_exit(self, position: Position) -> None:
        # Border-cell-only: a non-border target is a silent no-op, never a
        # prompt (the ghost only ever previews border cells, so this is the
        # accidental/exploratory click path). Same-cell is a no-op, and so
        # is placing on the entry's cell (start and goal never share a
        # cell); first placement is direct; only a redefinition is gated by
        # the setting.
        if not is_border_cell(self._session.maze.grid, position):
            return
        if self._session.exit == position:
            return
        if self._session.entry == position:
            return
        on_apply = functools.partial(self._apply_set_exit, position)
        if self._session.exit is None:
            on_apply()
            return
        self._maybe_confirm(
            read_confirm_redefine_marker(self._settings_repository),
            message="Move the exit marker to this cell?",
            on_confirm=on_apply,
        )

    def _apply_set_entry(self, position: Position) -> None:
        try:
            self._session = apply_set_entry(self._session, position)
        except DomainValidationError:
            # Out-of-bounds, or collides with the exit marker: refused,
            # silent no-op (mirrors `_apply_set_exit`).
            return
        self._sync_markers()

    def _apply_set_exit(self, position: Position) -> None:
        try:
            self._session = apply_set_exit(self._session, position)
        except DomainValidationError:
            # Non-border target: refused, silent no-op (the I/O matrix's
            # "adapter swallows" path -- mirrors `_on_wall_clicked`).
            return
        self._sync_markers()

    def _maybe_confirm(
        self,
        enabled: bool,
        *,
        message: str,
        on_confirm: Callable[[], None] | None = None,
    ) -> None:
        """Gate a marker redefinition behind a `ConfirmDialog` when `enabled`.

        Never stacks: a second trigger while a dialog is already open is a
        no-op (the dialog is non-modal, so a click could otherwise reach
        this screen behind it). When `enabled`, opens the dialog and stores
        it so the owning action's `on_confirm` only runs on Confirm; when
        `enabled` is `False`, applies the action immediately. `on_close`
        clears the guard. Mirrors `GameplayScreen._maybe_confirm`
        (`player/gameplay_screen.py:665`).
        """
        if not enabled:
            if on_confirm is not None:
                on_confirm()
            return
        if self._confirm_dialog is not None:
            return
        self._confirm_dialog = ConfirmDialog(
            self,
            theme=self._theme,
            message=message,
            on_confirm=on_confirm,
            on_close=self._clear_confirm_dialog,
        )

    def _clear_confirm_dialog(self) -> None:
        self._confirm_dialog = None

    def _sync_markers(self) -> None:
        # The ghost preview is rendered only while Set Exit is active, at
        # the cursor cell if that cell is on the border and holds no
        # marker -- never a standing default/placeholder position for an
        # unset exit, and never drawn over the entry/exit it would preview
        # (the I/O matrix's "filled diamond marker replaces the ghost").
        # Every session change that could affect markers (tool switch,
        # cursor move, a placement) re-syncs through this single method.
        ghost: Position | None = None
        cursor = self._session.cursor
        if (
            self._session.tool is BuilderTool.SET_EXIT
            and is_border_cell(self._session.maze.grid, cursor)
            and cursor != self._session.entry
            and cursor != self._session.exit
        ):
            ghost = cursor
        self._canvas.refresh_markers(self._session.entry, self._session.exit, ghost)

    def _sync_after_wall_change(self) -> None:
        self._canvas.refresh_walls(self._session.maze.grid)
        self._walls_chip.set_value(str(broken_wall_count(self._session)))

    def _test_in_player(self) -> None:
        """Hand the in-progress `Maze` straight to the Player's gameplay screen.

        A live in-memory hand-off through `navigate()` (FR-8): the Player
        mounts `GameplayScreen` directly when its `mount()` receives a
        `BuilderTestLaunch` state, so this is the only Builder-side trigger
        -- no serialization round-trip and no save required first (Story
        3.8).

        Blocking popup gate (amendment): Test in Player is refused while
        the session's exit marker is unset -- `start_builder_session` always
        seeds the entry (the (0,0) default counts as defined), so only the
        exit can be missing. An alert-mode `ConfirmDialog` (OK-only, no
        action) explains and refuses, mirroring `save_maze`'s own
        exit-unset gate. On success the hand-off is a `BuilderTestLaunch`
        carrying the session's `entry`/`exit` set-ness, so the round-trip
        back restores exactly those markers.
        """
        if self._session.exit is None:
            ConfirmDialog(
                self,
                theme=self._theme,
                message=("Test in Player needs the exit to be set. Set the exit first?"),
                on_confirm=None,
                on_close=lambda: None,
                confirm_label="OK",
                cancel_label=None,
            )
            return
        self._navigate(
            ScreenId.PLAYER,
            BuilderTestLaunch(
                maze=self._session.maze,
                entry=self._session.entry,
                exit=self._session.exit,
            ),
        )

    def save_maze(self) -> None:
        """Start the Save flow (AC1/AC2, I/O matrix).

        Exit not set: Maze save is blocked; a `ConfirmDialog` explains why
        and offers Sketch save instead (always available). Exit set: goes
        straight to Maze save. Either path opens `_SaveNameDialog` next for
        the actual name entry/duplicate-name handling -- this method only
        decides *which* kind is being saved.
        """
        if self._session.exit is None:
            ConfirmDialog(
                self,
                theme=self._theme,
                message=(
                    'Exit not set. Save as "Sketch" (always available, no '
                    "exit required), or set the exit first?"
                ),
                on_confirm=self._open_save_dialog_for_sketch,
                on_close=lambda: None,
            )
            return
        self._open_save_dialog_for_maze()

    def _open_save_dialog_for_sketch(self) -> None:
        self._open_save_dialog(MazeKind.SKETCH, self._do_save_sketch)

    def _open_save_dialog_for_maze(self) -> None:
        # Promote to CLASSIC unless the maze already carries an
        # id-eligible kind (a future Edit-in-Builder resave, Story 3.9) --
        # `MazeRepository.save()` never infers/rewrites `kind` itself, so
        # the caller must set the target kind before calling it (its own
        # docstring), and never re-mints an id an already-eligible maze
        # already carries (AD-3/AD-6).
        target_kind = self._session.maze.kind
        if target_kind not in _ID_ELIGIBLE_KINDS:
            target_kind = MazeKind.CLASSIC
        self._open_save_dialog(target_kind, functools.partial(self._do_save_maze, target_kind))

    def _open_save_dialog(self, kind: MazeKind, on_confirm: Callable[[str], None]) -> None:
        grid = self._session.maze.grid
        suggested_name = f"{grid.width}x{grid.height}"
        existing_names = self._maze_repository.list_names(kind)
        _SaveNameDialog(
            self,
            theme=self._theme,
            suggested_name=suggested_name,
            existing_names=existing_names,
            on_confirm=on_confirm,
        )

    def _do_save_sketch(self, name: str) -> None:
        """Persist the current maze as a Sketch and return to Builder with it.

        `session.maze.entry`/`.exit` are already kept in sync with the
        session's own optional `entry`/`exit` fields by
        `apply_set_entry`/`apply_set_exit` (`builder_session.py`), so no
        separate override is needed here -- only `kind`/`id` change.
        """
        sketch_maze = replace(self._session.maze, kind=MazeKind.SKETCH, id=None)
        saved = self._maze_repository.save(sketch_maze, name)
        self._navigate(ScreenId.BUILDER, saved)

    def _do_save_maze(self, target_kind: MazeKind, name: str) -> None:
        """Persist the current maze as a finished Maze and return to Builder with it."""
        maze_to_save = replace(self._session.maze, kind=target_kind)
        saved = self._maze_repository.save(maze_to_save, name)
        self._navigate(ScreenId.BUILDER, saved)


_NAME_REQUIRED_MESSAGE = "Name is required."
_PATH_SEPARATOR_MESSAGE = "Name must not contain a path separator."
_PATH_SEPARATORS = ("/", "\\")


def _validate_save_name(name: str) -> str | None:
    """The inline error for `name`, or `None` if it's shape-valid.

    Duplicates `player/save_maze_dialog.py::_validate_name`'s two rules
    (empty / contains a path separator) locally rather than importing them
    -- `adapters/tkinter/builder/` never imports `adapters/tkinter/player/`
    (AD-1, AD-9/AD-10), so the rules are kept in sync by convention, the
    same way `save_maze_dialog.py` itself duplicates them from
    `adapters/storage/paths.py::maze_file_path` rather than importing that
    (AD-9's Builder/Player-never-import-each-other applies one layer up:
    neither screen package imports the storage adapter directly either).
    """
    if not name:
        return _NAME_REQUIRED_MESSAGE
    if any(separator in name for separator in _PATH_SEPARATORS):
        return _PATH_SEPARATOR_MESSAGE
    return None


class _SaveNameDialog(tk.Toplevel):
    """Name entry, live validation, and arm/confirm overwrite for the Save flow.

    Mirrors `player/save_maze_dialog.py`'s `SaveMazeDialog` (Story 2.3)
    deliberately: FR-5's "match the Builder's save behavior" was written
    against *this* story providing the shape `SaveMazeDialog` follows, so
    the two are kept in lock-step -- a duplicate-name collision arms the
    Save button (relabeled "Overwrite") and shows an inline warning rather
    than saving immediately; a second click on the *same, unchanged* name
    confirms the overwrite. Kept local rather than imported from
    `adapters/tkinter/player/` per AD-1/AD-9/AD-10 (Builder and Player
    never import each other); unifying this with `SaveMazeDialog` into
    `adapters/tkinter/common/` is a reasonable follow-up (AD-11), not done
    here to keep this story's diff scoped to the Builder.
    """

    def __init__(
        self,
        parent: tk.Widget,
        *,
        theme: Theme,
        suggested_name: str,
        existing_names: list[str],
        on_confirm: Callable[[str], None],
    ) -> None:
        super().__init__(parent)
        self.title("Save")
        self._existing_names = existing_names
        self._on_confirm = on_confirm
        self._armed_name: str | None = None

        colors = colors_for(theme)
        self.configure(background=colors.window)

        form = tk.Frame(self, background=colors.window)
        form.pack(padx=SPACING["2xl"], pady=SPACING["2xl"], fill="both", expand=True)

        row = tk.Frame(form, background=colors.window)
        row.pack(fill="x", pady=(0, SPACING["xs"]))

        tk.Label(
            row,
            text="Name",
            font=TYPOGRAPHY.body.to_tk_font(),
            background=colors.window,
            foreground=colors.ink,
            width=12,
            anchor="w",
        ).pack(side="left")

        self._name_entry = tk.Entry(row, width=24)
        self._name_entry.insert(0, suggested_name)
        self._name_entry.select_range(0, "end")
        self._name_entry.pack(side="left")
        self._name_entry.bind("<KeyRelease>", self._on_name_changed)
        self._name_entry.bind("<Return>", self._on_save_clicked)
        # Consume "s"/"S" and "t"/"T" locally before they reach the global
        # `save_maze`/`test_in_player` shortcuts' `bind_all()` handlers --
        # same guard as `SaveMazeDialog._name_entry` (Story 2.3/2.4):
        # otherwise typing a "t" into a maze *name* while the dialog is open
        # fires `_test_in_player` and navigates away mid-save, abandoning
        # the dialog and the session (Story 3.8's review finding), and
        # typing an "s" both inserts the character and reopens a second
        # `_SaveNameDialog` stacked on this one.
        self._name_entry.bind("<KeyPress-s>", lambda _event: "break")
        self._name_entry.bind("<KeyPress-S>", lambda _event: "break")
        self._name_entry.bind("<KeyPress-t>", lambda _event: "break")
        self._name_entry.bind("<KeyPress-T>", lambda _event: "break")
        self._name_entry.focus_set()

        self._message_label = tk.Label(
            form,
            text="",
            font=TYPOGRAPHY.body_secondary.to_tk_font(),
            background=colors.window,
            foreground=colors.exit,
            anchor="w",
            justify="left",
            wraplength=360,
        )
        self._message_label.pack(fill="x", pady=(0, SPACING["sm"]))

        buttons = tk.Frame(self, background=colors.window)
        buttons.pack(padx=SPACING["2xl"], pady=(0, SPACING["2xl"]), anchor="e")

        self._cancel_button = PillButton(buttons, "Cancel", theme=theme, command=self._on_cancel)
        self._cancel_button.pack(side="left", padx=(0, SPACING["sm"]))

        self._save_button = PillButton(
            buttons, "Save", theme=theme, primary=True, command=self._on_save_clicked
        )
        self._save_button.pack(side="left")

        self.bind("<Escape>", self._on_cancel)

    # -- arming --------------------------------------------------------

    def _reset_arming(self) -> None:
        if self._armed_name is not None:
            self._armed_name = None
            self._save_button.set_text("Save")

    def _on_name_changed(self, _event: tk.Event | None = None) -> None:
        # Compared against the raw (unstripped) field text, the same value
        # `_armed_name` was captured from -- a non-content `<KeyRelease>`
        # (arrow keys, Home/End, Shift) fires this handler too but leaves
        # the text unchanged, so arming must survive it; only an actual
        # edit resets it.
        if self._name_entry.get() != self._armed_name:
            self._reset_arming()
        if self._armed_name is not None:
            return
        self._message_label.configure(
            text=_validate_save_name(self._name_entry.get().strip()) or ""
        )

    # -- actions ---------------------------------------------------

    def _on_save_clicked(self, _event: tk.Event | None = None) -> None:
        raw = self._name_entry.get()
        name = raw.strip()
        error = _validate_save_name(name)
        if error is not None:
            self._reset_arming()
            self._message_label.configure(text=error)
            return

        if name in self._existing_names and self._armed_name != raw:
            # First click on a colliding name: arm, warn, relabel -- no
            # save yet.
            self._armed_name = raw
            self._save_button.set_text("Overwrite")
            self._message_label.configure(
                text=f'A maze named "{name}" already exists — Save again to overwrite it.'
            )
            return

        # Destroy before invoking `on_confirm`: `on_confirm` triggers
        # `_navigate()`, which mounts a fresh Builder frame -- closing this
        # dialog's own window first, via its own controlled path, avoids
        # relying on that navigation's frame teardown to also clean this up.
        self.destroy()
        self._on_confirm(name)

    def _on_cancel(self, _event: tk.Event | None = None) -> None:
        self.destroy()


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
        on_zone_dragged: Callable[[BuilderTool, Position, Position], None],
        on_cell_clicked: Callable[[BuilderTool, Position], None],
        capture_tool: Callable[[], BuilderTool],
    ) -> None:
        self._theme = theme
        self._on_wall_clicked = on_wall_clicked
        self._on_zone_dragged = on_zone_dragged
        self._on_cell_clicked = on_cell_clicked
        self._capture_tool = capture_tool
        grid = maze.grid
        self._grid_width = grid.width
        self._grid_height = grid.height
        self._cell_size = _cell_size(grid.width, grid.height)
        self._drag_anchor: Position | None = None
        self._drag_tool: BuilderTool | None = None
        self._marker_radius = int(round(self._cell_size * _MARKER_SCALE / 2))
        self._ghost_font = FontSpec(
            family=TYPOGRAPHY.heading.family,
            size=max(8, int(self._cell_size * _GHOST_FONT_SCALE)),
            weight="700",
        ).to_tk_font()
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
        self.bind("<ButtonRelease-1>", self._on_release)

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
        cx = position.col * size + size // 2
        cy = position.row * size + size // 2
        radius = int(round(size * _MARKER_SCALE / 2))
        return self.create_oval(
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
            fill=colors.accent,
            outline="",
            tags=("cursor",),
        )

    def set_cursor(self, position: Position) -> None:
        """Move the cursor circle to `position`'s cell, without redrawing walls."""
        size = self._cell_size
        cx = position.col * size + size // 2
        cy = position.row * size + size // 2
        radius = int(round(size * _MARKER_SCALE / 2))
        self.coords(self._cursor_id, cx - radius, cy - radius, cx + radius, cy + radius)

    def _pixel_to_cell(self, x: int, y: int) -> Position:
        """The grid cell containing pixel `(x, y)`, clamped to the grid's
        bounds -- a drag that ends (or starts) outside the canvas still
        resolves to the nearest edge cell rather than raising."""
        size = self._cell_size
        col = max(0, min(self._grid_width - 1, x // size))
        row = max(0, min(self._grid_height - 1, y // size))
        return Position(row=row, col=col)

    def _on_click(self, event: tk.Event) -> None:
        self._drag_anchor = self._pixel_to_cell(event.x, event.y)
        # Snapshot the active tool now -- the gesture this press might
        # start is governed by whichever tool was active at press time,
        # even if the user switches tools before releasing. Wall
        # hit-testing only matters under the Break tool: marker tools place
        # via `_on_release`'s same-cell click, so a wall hit under them is
        # wasted work.
        self._drag_tool = self._capture_tool()
        if self._drag_tool is not BuilderTool.BREAK:
            return
        hit = self.find_closest(event.x, event.y, halo=_CLICK_HALO)
        if not hit:
            return
        wall = self._item_walls.get(hit[0])
        if wall is None:
            # Closest item was the cursor rectangle, not a wall bar/gap.
            return
        self._on_wall_clicked(wall)

    def _on_release(self, event: tk.Event) -> None:
        # The click-vs-drag split is decided purely by comparing the press
        # cell to the release cell -- a release on the same cell as the
        # press is never a zone operation, with no separate pixel-distance
        # threshold (Story 3.3's Boundaries).
        if self._drag_anchor is None:
            return
        anchor = self._drag_anchor
        tool = self._drag_tool
        end = self._pixel_to_cell(event.x, event.y)
        # Consumed: reset both before dispatching so a stray/duplicate
        # <ButtonRelease-1> with no intervening <Button-1> can never replay
        # a stale anchor/tool as a zone operation.
        self._drag_anchor = None
        self._drag_tool = None
        if tool is None:
            return
        if end != anchor:
            # Zone drag: only a press-captured zone tool fires a zone
            # operation -- a Break/Pass-through/marker drag never is one
            # (`_on_zone_dragged`'s own gate is a defensive fallback).
            if tool in (BuilderTool.DESTROY_ZONE, BuilderTool.RESTORE_ZONE):
                self._on_zone_dragged(tool, anchor, end)
        elif tool is BuilderTool.SET_ENTRY or tool is BuilderTool.SET_EXIT:
            # Same-cell release under a press-captured marker tool = a
            # cell click (Story 3.4).
            self._on_cell_clicked(tool, end)
        elif end == anchor:
            # Same-cell click with no zone-drag and no marker tool active:
            # move editing cursor directly to the clicked cell (Story 3.5).
            self._on_cell_clicked(tool, end)

    def _cell_center(self, position: Position) -> tuple[int, int]:
        size = self._cell_size
        return (position.col * size + size // 2, position.row * size + size // 2)

    def _cell_bounds(self, position: Position) -> tuple[int, int, int, int]:
        size = self._cell_size
        x0, y0 = position.col * size, position.row * size
        return x0, y0, x0 + size, y0 + size

    def refresh_markers(
        self,
        entry: Position | None,
        exit: Position | None,
        ghost: Position | None,
    ) -> None:
        """Redraw the entry/exit markers and any Set Exit ghost preview.

        Destroys every tagged `marker`/`ghost-marker` item and redraws from
        scratch, so a stale marker at a previous position can never linger
        after a placement/undo/redefinition -- this is the single redraw
        seam `_BuilderEditArea._sync_markers` drives. Colors come from the
        active theme via `colors_for`; the ghost is dashed + `?`-glyphed
        and purely informational, never hit-testable as a wall or a marker.
        """
        colors = colors_for(self._theme)
        self.delete("marker", "ghost-marker")
        if entry is not None:
            self._draw_entry_marker(entry, colors)
        if exit is not None:
            self._draw_exit_marker(exit, colors)
        if ghost is not None:
            self._draw_ghost(ghost, colors)

    def _draw_entry_marker(self, position: Position, colors: ColorTokens) -> None:
        # Filled square (entry = square, exit = diamond, builder/player = circle),
        # radius `_marker_radius`.
        cx, cy = self._cell_center(position)
        r = self._marker_radius
        self.create_rectangle(
            cx - r,
            cy - r,
            cx + r,
            cy + r,
            outline=colors.entry,
            fill=colors.entry,
            tags=("marker",),
        )

    def _draw_exit_marker(self, position: Position, colors: ColorTokens) -> None:
        # Filled diamond (see `_draw_entry_marker` for the shape/color split).
        cx, cy = self._cell_center(position)
        r = self._marker_radius
        self.create_polygon(
            cx,
            cy - r,
            cx + r,
            cy,
            cx,
            cy + r,
            cx - r,
            cy,
            outline=colors.exit,
            fill=colors.exit,
            tags=("marker",),
        )

    def _draw_ghost(self, position: Position, colors: ColorTokens) -> None:
        # Dashed outline + `?` glyph at the cursor cell, `colors.ghost`,
        # non-interactive (tags `ghost-marker` only -- never hit-testable).
        # The inset and glyph size scale with the cell size so the preview
        # stays inside the smallest cells (Story 3.4's marker geometry).
        x0, y0, x1, y1 = self._cell_bounds(position)
        inset = max(2, int(self._cell_size * _GHOST_INSET_SCALE))
        self.create_rectangle(
            x0 + inset,
            y0 + inset,
            x1 - inset,
            y1 - inset,
            outline=colors.ghost,
            dash=(3, 3),
            width=_WALL_WIDTH,
            tags=("ghost-marker",),
        )
        cx, cy = self._cell_center(position)
        self.create_text(
            cx,
            cy,
            text="?",
            fill=colors.ghost,
            font=self._ghost_font,
            tags=("ghost-marker",),
        )
