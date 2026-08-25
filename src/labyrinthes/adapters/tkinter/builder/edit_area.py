"""`_BuilderEditArea` -- tool side bar + HUD + maze canvas, wired to one
`BuilderSession` (Stories 3.2/3.3/3.4/3.6/3.8).

Owns one adapter-local `BuilderSession` (Epic 3 Technical Decisions'
"adapter-local mutable session wrapper... around the immutable `Maze`
value") and wires:
- A left `ToolButtonGroup` side bar: Break Wall / Pass-through / Destroy
  Zone / Restore Zone / Set Entry / Set Exit, mutually exclusive, mirrored
  by the `break_wall`/`pass_through`/`destroy_zone`/`restore_zone`/
  `set_entry`/`set_exit` keybindings (`ScreenId.BUILDER`-scoped, so
  'b'/'p' can also mean Home's `open_builder`/`open_player` while
  'd'/'r'/'e'/'x' are Builder-only -- see `common/keybindings.py`'s
  `scope` field).
- A center column: `HudChip`s for grid size + live "Walls broken", above
  `_BuilderMazeCanvas` (`maze_canvas.py`).
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
  `player/gameplay/screen.py`); clicking the marker's own cell is a no-op
  with no prompt. `_BuilderEditArea._on_move` re-syncs markers via
  `_sync_markers` so the ghost preview tracks the cursor, and it never
  rests on a placeholder for an unset exit nor on a cell already carrying
  a marker.
- The Save flow (Story 3.6): `save_maze` decides Sketch vs. Maze from
  whether the exit is set, then opens `_SaveNameDialog` (`save_dialog.py`)
  for the actual name entry/duplicate-name handling.

Never imports `home`/`player` or `adapters/storage/` (AD-1, AD-9).
"""

from __future__ import annotations

import functools
import tkinter as tk
from collections.abc import Callable
from dataclasses import replace

from labyrinthes.adapters.tkinter.builder.maze_canvas import _BuilderMazeCanvas
from labyrinthes.adapters.tkinter.builder.save_dialog import _SaveNameDialog
from labyrinthes.adapters.tkinter.common import (
    SPACING,
    BuilderTestLaunch,
    ConfirmDialog,
    HudChip,
    NavigateFn,
    PillButton,
    ScreenId,
    Theme,
    ToolButton,
    ToolButtonGroup,
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
    move_cursor,
    set_tool,
    start_builder_session,
)
from labyrinthes.application.confirmation_settings import read_confirm_redefine_marker
from labyrinthes.application.maze_repository import MazeRepository
from labyrinthes.application.settings_repository import SettingsRepository
from labyrinthes.domain.errors import DomainValidationError
from labyrinthes.domain.level_visibility import Wall
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.movement import Direction
from labyrinthes.domain.position import Position
from labyrinthes.domain.reachability import inaccessible_cells

__all__ = ["_BuilderEditArea"]

# Kinds `MazeRepository.save()` mints a `MazeId` for (AD-3/AD-6) -- a maze
# save promotes any other kind (in practice, only `SKETCH`: the Builder
# never opens a `GENERATED` maze) to `CLASSIC`; an already-eligible kind
# (a future Edit-in-Builder resave, Story 3.9) is left as-is so its
# existing id is carried forward, not re-minted.
_ID_ELIGIBLE_KINDS = frozenset({MazeKind.CLASSIC, MazeKind.SAVED_RANDOM})

_DIRECTION_ACTION_IDS: tuple[tuple[str, Direction], ...] = (
    ("move_up", Direction.UP),
    ("move_down", Direction.DOWN),
    ("move_left", Direction.LEFT),
    ("move_right", Direction.RIGHT),
)


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
        bind_shortcut(
            self, keybinding("toggle_break_pass_through"), self._toggle_break_pass_through
        )
        bind_shortcut(self, keybinding("destroy_zone"), self._activate_destroy_zone)
        bind_shortcut(self, keybinding("restore_zone"), self._activate_restore_zone)
        bind_shortcut(self, keybinding("set_entry"), self._activate_set_entry)
        bind_shortcut(self, keybinding("set_exit"), self._activate_set_exit)
        bind_shortcut(self, keybinding("place_marker"), self._place_marker_at_cursor)
        bind_shortcut(self, keybinding("save_maze"), self.save_maze)
        bind_shortcut(self, keybinding("test_in_player"), self._test_in_player)
        # Escape cancels armed zone anchor (click-click gesture, Story 4.3).
        self.bind_all("<Escape>", self._cancel_armed_anchor, add="+")

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
            tooltip="Moving the cursor across a wall breaks it",
            group=group,
            command=self._activate_break,
        )
        self._break_button.pack(fill="x", pady=(0, SPACING["sm"]))

        self._pass_through_button = ToolButton(
            sidebar,
            pass_kb.label,
            theme=self._theme,
            shortcut=pass_kb.display,
            tooltip="Moving the cursor crosses walls freely",
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
            tooltip=(
                "Click-and-drag or click-click across a rectangle to break "
                "every wall inside it; Escape cancels"
            ),
            group=group,
            command=self._activate_destroy_zone,
        )
        self._destroy_zone_button.pack(fill="x", pady=(SPACING["sm"], 0))

        self._restore_zone_button = ToolButton(
            sidebar,
            restore_kb.label,
            theme=self._theme,
            shortcut=restore_kb.display,
            tooltip=(
                "Click-and-drag or click-click across a rectangle to restore "
                "every wall inside it; Escape cancels"
            ),
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
            tooltip="Click a cell to mark it as the maze exit (not on entry)",
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

        # Reachability counter (Story 4.5) -- replaces "Walls broken"
        self._reachability_chip = HudChip(
            hud_row,
            "Unreachable",
            self._compute_reachability_count(),
            theme=self._theme,
            live=True,
            command=self._toggle_reachability_highlight,
        )
        self._reachability_chip.pack(side="left")

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

        # Reachability highlight state
        self._reachability_highlight_active: bool = False
        self._inaccessible_cells: frozenset[Position] = frozenset()

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

    def _toggle_break_pass_through(self) -> None:
        """Toggle between Break and Pass-through tools via Space key."""
        if self._session.tool is BuilderTool.BREAK:
            self._activate_pass_through()
        elif self._session.tool is BuilderTool.PASS_THROUGH:
            self._activate_break()

    def _cancel_armed_anchor(self, _event: tk.Event | None = None) -> None:
        """Cancel the armed zone anchor (click-click gesture) on Escape key.

        Also cancels any ongoing drag operation so that releasing the mouse
        button does not apply the zone operation.
        """
        self._canvas._cancel_drag()

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
        # Any cell except the entry: a target on the entry is a silent no-op.
        # Same-cell is a no-op; first placement is direct; only a redefinition
        # is gated by the setting.
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
        self._update_reachability_on_marker_change()

    def _apply_set_exit(self, position: Position) -> None:
        try:
            self._session = apply_set_exit(self._session, position)
        except DomainValidationError:
            # Non-border target: refused, silent no-op (the I/O matrix's
            # "adapter swallows" path -- mirrors `_on_wall_clicked`).
            return
        self._sync_markers()
        self._update_reachability_on_marker_change()

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
        (`player/gameplay/screen.py`).
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

    def _place_marker_at_cursor(self) -> None:
        """Place the entry or exit marker at the current cursor position via Enter key.

        Delegates to the existing `_place_entry`/`_place_exit` methods which
        handle the redefinition confirmation flow.
        """
        if self._session.tool is BuilderTool.SET_ENTRY:
            self._place_entry(self._session.cursor)
        elif self._session.tool is BuilderTool.SET_EXIT:
            self._place_exit(self._session.cursor)

    def _sync_markers(self) -> None:
        # Ghost previews for Set Entry (filled square) and Set Exit (filled
        # diamond) -- shown at the cursor cell when the respective tool is
        # active, except on the other marker's cell and except on the
        # marker's own cell (no ghost over an already-placed marker).
        # Every session change that could affect markers (tool switch,
        # cursor move, a placement) re-syncs through this single method.
        entry_ghost: Position | None = None
        exit_ghost: Position | None = None
        cursor = self._session.cursor
        tool = self._session.tool
        entry_blocked = cursor in (self._session.exit, self._session.entry)
        exit_blocked = cursor in (self._session.entry, self._session.exit)
        if tool is BuilderTool.SET_ENTRY and not entry_blocked:
            entry_ghost = cursor
        elif tool is BuilderTool.SET_EXIT and not exit_blocked:
            exit_ghost = cursor
        self._canvas.refresh_markers(
            self._session.entry, self._session.exit, entry_ghost, exit_ghost
        )

    def _sync_after_wall_change(self) -> None:
        self._canvas.refresh_walls(self._session.maze.grid)
        self._update_reachability()

    def _compute_reachability_count(self) -> str:
        """Compute the reachability count for the HUD chip."""
        entry = self._session.entry
        if entry is None:
            return "—"
        inaccessible = inaccessible_cells(self._session.maze, entry)
        return str(len(inaccessible))

    def _update_reachability(self) -> None:
        """Update the reachability HUD chip and refresh highlight if active."""
        self._reachability_chip.set_value(self._compute_reachability_count())
        if self._reachability_highlight_active:
            # Recompute and redraw highlight
            entry = self._session.entry
            if entry is not None:
                self._inaccessible_cells = inaccessible_cells(self._session.maze, entry)
                self._canvas.draw_reachability_highlight(self._inaccessible_cells)

    def _toggle_reachability_highlight(self) -> None:
        """Toggle the reachability highlight on the canvas."""
        entry = self._session.entry
        if entry is None:
            return
        if self._reachability_highlight_active:
            self._canvas.clear_reachability_highlight()
            self._reachability_highlight_active = False
            self._inaccessible_cells = frozenset()
        else:
            self._inaccessible_cells = inaccessible_cells(self._session.maze, entry)
            self._canvas.draw_reachability_highlight(self._inaccessible_cells)
            self._reachability_highlight_active = True

    def _update_reachability_on_marker_change(self) -> None:
        """Update reachability when entry/exit markers change."""
        self._update_reachability()

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
        `apply_set_entry`/`apply_set_exit` (`application/builder_session.py`),
        so no separate override is needed here -- only `kind`/`id` change.
        """
        sketch_maze = replace(self._session.maze, kind=MazeKind.SKETCH, id=None)
        saved = self._maze_repository.save(sketch_maze, name)
        self._navigate(ScreenId.BUILDER, saved)

    def _do_save_maze(self, target_kind: MazeKind, name: str) -> None:
        """Persist the current maze as a finished Maze and return to Builder with it."""
        maze_to_save = replace(self._session.maze, kind=target_kind)
        saved = self._maze_repository.save(maze_to_save, name)
        self._navigate(ScreenId.BUILDER, saved)
