"""`GameplayScreen` -- rendering, HUD, movement modes, win detection (Story 2.4/2.5).

A `MazeCanvas` renders the mounted `Maze`'s walls/entry/exit/ball once, an
HUD row of `HudChip`s (`hud.py`'s `_HudRow`) shows Level/Difficulty/Time/Pos,
arrow keys drive a pure `domain.movement.attempt_move` +
`application.player_session` orchestration loop, and reaching `maze.exit`
shows an inline win banner (`banners.py`'s `_OutcomeBanner`).

This screen is the session-orchestrating controller: it owns `self._session`
and every method that reads or mutates it, and pushes the results into two
composed, session-agnostic widgets --
`hud.py`'s `_HudRow` (the chip row + HARD status light) and `sidebar.py`'s
`_Sidebar` (the Movement/Mode/Levels/Difficulty/Logo/Edit-in-Builder
column) -- through their small `set_*`/`sync_*` setters. Both widgets hold
no session state of their own; every button's *command* is still a callback
into this class, since deciding what a click does (including the
`_toplevel_has_focus()` guard) is this controller's job, not theirs.

Story 2.5 adds configurable movement modes and speed. The screen reads the
`game`-scoped `MOVEMENT_MODE`/`MOVEMENT_SPEED` settings at mount, applies
them to the session, and exposes a left-hand "Movement" sidebar (a mode
toggle bound to the `m` shortcut, active when Smooth, and a Ball-speed
button cycling Slow/Normal/Fast). Both modes run through the same
leg/animation engine (`request_move`/`advance_step` + a per-sub-step
`.after()` loop rescheduled at `cell_crossing_duration(speed) //
STEPS_PER_CELL` ms, recomputed per reschedule so a live speed change takes
effect immediately). Win detection now fires from the animation tick's
leg-completion branch, not from the keypress handler, so both modes resolve
a win at leg completion.

Story 2.6 makes the Level HUD chip real (driven by `session.level`) and
adds a "Levels" sidebar group (`−`/label/`+` cycling ONE..MAX, wrapped).
Level changes reroute through `set_level` (a session-level no-op once
solved), which re-initializes the session's `LevelVisibility`; whenever
`session.visibility` changes identity -- a level switch, a Level 2/3
partition advance, a Level 4 wall discovery, or a Level Max contour
toggle -- the screen calls `MazeCanvas.redraw_structure()` (an exact
object-identity diff, so nothing redraws on a run that doesn't change the
visible structure). Both `.after()` loops are cancelled on `<Destroy>` and
on solve so a torn-down or solved screen never fires a stale callback.

Story 2.7 makes the Difficulty HUD chip real (driven by `session.difficulty`)
and adds a "Difficulty" sidebar group (`−`/label/`+` cycling ONE..THREE,
wrapped) directly under the "Levels" group. Difficulty changes reroute
through `set_difficulty` (a no-op once solved), which re-initializes
`visibility` from the current position; the same `_sync_visibility()` redraw
fires on the resulting identity change. The Difficulty controls are disabled
(`_Sidebar.set_difficulty(..., enabled=False)`) whenever the level is ONE or
MAX -- unlockable from Level 2 onward, and inert at MAX (no partitions/walls
to threshold), matching the legacy `Niveau_max` gate. Both controls share
the toplevel focus guard and have no global shortcut.

Story 2.8 adds HARD mode: a "Mode" sidebar group with a single HARD
`ToolButton` (bound to the `h` shortcut) toggles `session.hard_mode`, and a
status light (a 10px round light + Ready/Moving label) in the HUD row shows
only while HARD is active. While the ball moves, `_sync_hard_mode_visuals()`
calls `MazeCanvas.set_hard_mode_moving(True)` so the ball is genuinely not
rendered and a fog scrim covers the corridor plane; at rest it restores the
ball and hides the fog instantly. Both light states read their color fresh
from the `game`-scoped settings on every activation/state sync
(`_hard_mode_colors()`), so a color change recolors ready *and* moving and
can never break the ready<->moving toggle (the legacy `"blue"` hardcode bug
is fixed by construction -- no color literal lives in this module).

Story 2.9 adds the optional time limit. The screen reads the `game`-scoped
`TIME_LIMIT_SECONDS` once at mount into `_time_limit`; `_on_tick()` checks
the wall clock against it after updating the Time chip and, once the limit
is reached on an unsolved run, stops the run via `_on_timeout()` (cancels
both `.after()` loops, marks the session `timed_out` -- freezing movement,
since every `PlayerSession` operation is a no-op once `timed_out` -- freezes
the Time chip, and shows an inline non-modal banner). The banner offers
Restart (`_restart_run`, a fresh run for the same maze with persisted
mode/speed/limit re-applied and the session defaults restored) and Continue
(dismisses the message; the run stays stopped).

Story 2.10 gates the level-change and restart actions behind per-action
confirmation settings. The `−`/`+` Level buttons (`_cycle_level`) and the
Restart button / timeout-banner Restart (`_restart_run`) read
`read_confirm_level_change` / `read_confirm_restart` at action time and,
when enabled, open a non-modal `ConfirmDialog` (parented to this screen, so
it cascade-destroys with it) instead of applying directly; the actual
mutation moves into `_apply_level_cycle` / `_apply_restart_run`, which the
dialog's Confirm invokes. `_confirm_dialog is not None` guards against a
second gated trigger stacking a second dialog (the dialog is non-modal, so
clicks can still reach this screen). Each action reads its setting at
action time -- never cached at mount -- so a Settings toggle takes effect
without an app restart (AC-3).

Story 3.8's amendment gives the screen an optional `on_back_to_builder`
callback (`None` in normal gallery-driven gameplay). When set (a Builder
"Test in Player" run), the win banner offers Restart + Back to Builder
instead of Continue -- the latter returns to the Builder, restoring the
session's markers from the `BuilderTestLaunch` payload it was mounted
with.
"""

from __future__ import annotations

import dataclasses
import functools
import time
import tkinter as tk
from collections.abc import Callable

from labyrinthes.adapters.tkinter.common.confirm_dialog import ConfirmDialog
from labyrinthes.adapters.tkinter.common.keybindings import bind_shortcut, keybinding
from labyrinthes.adapters.tkinter.common.navigation import BuilderTestLaunch, ScreenId
from labyrinthes.adapters.tkinter.common.pill_btn import PillButton
from labyrinthes.adapters.tkinter.common.tokens import SPACING, ColorTokens, Theme, colors_for
from labyrinthes.adapters.tkinter.player.gameplay.banners import _OutcomeBanner
from labyrinthes.adapters.tkinter.player.gameplay.hud import _HudRow
from labyrinthes.adapters.tkinter.player.gameplay.sidebar import _Sidebar
from labyrinthes.adapters.tkinter.player.maze_canvas import MazeCanvas
from labyrinthes.adapters.tkinter.player.save_maze_dialog import SaveMazeDialog
from labyrinthes.application.confirmation_settings import (
    read_confirm_level_change,
    read_confirm_restart,
)
from labyrinthes.application.hard_mode_settings import (
    read_hard_mode_moving_color,
    read_hard_mode_ready_color,
)
from labyrinthes.application.maze_repository import MazeRepository
from labyrinthes.application.movement_settings import (
    read_movement_mode,
    read_movement_speed,
    write_movement_mode,
    write_movement_speed,
)
from labyrinthes.application.player_session import (
    STEPS_PER_CELL,
    start_session,
)
from labyrinthes.application.player_session import (
    advance_step as session_advance_step,
)
from labyrinthes.application.player_session import (
    request_move as session_request_move,
)
from labyrinthes.application.player_session import (
    set_difficulty as session_set_difficulty,
)
from labyrinthes.application.player_session import (
    set_hard_mode as session_set_hard_mode,
)
from labyrinthes.application.player_session import (
    set_level as session_set_level,
)
from labyrinthes.application.player_session import (
    set_mode as session_set_mode,
)
from labyrinthes.application.player_session import (
    set_speed as session_set_speed,
)
from labyrinthes.application.player_session import (
    set_timed_out as session_set_timed_out,
)
from labyrinthes.application.player_session import (
    tick as session_tick,
)
from labyrinthes.application.settings_repository import SettingsRepository
from labyrinthes.application.theme_logo_settings import read_theme_logo
from labyrinthes.application.time_limit_settings import read_time_limit
from labyrinthes.domain.difficulty import Difficulty
from labyrinthes.domain.duration import Duration
from labyrinthes.domain.level import Level
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.movement import Direction
from labyrinthes.domain.movement_mode import MovementMode
from labyrinthes.domain.movement_speed import MovementSpeed, cell_crossing_duration
from labyrinthes.domain.position import Position

__all__ = ["GameplayScreen"]

_TICK_INTERVAL_MS = 1000

_LEVEL_LABELS: dict[Level, str] = {
    Level.ONE: "1",
    Level.TWO: "2",
    Level.THREE: "3",
    Level.FOUR: "4",
    Level.MAX: "Max",
}

_LEVEL_CYCLE: tuple[Level, ...] = tuple(Level)

_DIFFICULTY_CYCLE: tuple[Difficulty, ...] = tuple(Difficulty)

_DIRECTION_ACTION_IDS: tuple[tuple[str, Direction], ...] = (
    ("move_up", Direction.UP),
    ("move_down", Direction.DOWN),
    ("move_left", Direction.LEFT),
    ("move_right", Direction.RIGHT),
)

_SPEED_CYCLE: tuple[MovementSpeed, ...] = tuple(MovementSpeed)


def _level_label(level: Level) -> str:
    """The Level chip/sidebar label: `1`/`2`/`3`/`4`/`Max`."""
    return _LEVEL_LABELS[level]


def _difficulty_label(difficulty: Difficulty) -> str:
    """The Difficulty chip/sidebar label: `1`/`2`/`3`."""
    return str(difficulty.value)


def _pos_text(position: Position) -> str:
    """The Pos chip's `"(row, col)"` format -- matches `test_hud_chip.py`'s own example."""
    return f"({position.row}, {position.col})"


def _speed_label(speed: MovementSpeed) -> str:
    """The Ball-speed button's display label, e.g. `Slow`/`Normal`/`Fast`."""
    return speed.name.capitalize()


class GameplayScreen(tk.Frame):
    """Renders `maze`, wires arrow-key movement + movement modes, and marks a win."""

    def __init__(
        self,
        parent: tk.Widget,
        maze: Maze,
        theme: Theme,
        *,
        maze_repository: MazeRepository,
        settings_repository: SettingsRepository,
        navigate: Callable[[ScreenId, Maze | None | BuilderTestLaunch], None] | None = None,
        on_kind_changed: Callable[[MazeKind], None] | None = None,
        on_back_to_builder: Callable[[], None] | None = None,
    ) -> None:
        colors = colors_for(theme)
        super().__init__(parent, background=colors.window)
        self._theme = theme
        self._maze_repository = maze_repository
        self._maze = maze  # tracks kind/id across a save -- see `_build_save_zone()`
        self._on_kind_changed = on_kind_changed
        # The test-mode "Back to Builder" callback (Builder's Test in
        # Player, Story 3.8): `None` in normal gallery-driven gameplay. When
        # set, the win banner offers Restart + Back to Builder instead of
        # Continue, per the amendment.
        self._on_back_to_builder = on_back_to_builder
        # Callback to navigate the router (e.g. "Edit in Builder").
        # Set by `mount()` via `functools.partial` in `composition_root.py`.
        self._navigate = navigate
        self._settings_repository = settings_repository
        self._session = start_session(maze)
        # Apply the `game`-scoped settings-loaded mode/speed at mount. This
        # screen is rebuilt on re-navigate, so settings loaded here are fresh.
        self._session = session_set_mode(self._session, read_movement_mode(settings_repository))
        self._session = session_set_speed(self._session, read_movement_speed(settings_repository))
        # The optional time limit is read once at mount, like mode/speed --
        # a mid-run settings change applies to the next mount/restart, not
        # the active run (`_restart_run` re-reads it).
        self._time_limit: Duration | None = read_time_limit(settings_repository)
        self._start_time = time.monotonic()
        self._tick_job: str | None = None
        self._animation_job: str | None = None
        self._win_banner: _OutcomeBanner | None = None
        self._timeout_banner: _OutcomeBanner | None = None
        # Story 2.10: the open `ConfirmDialog`, if any -- `None` when no
        # prompt is showing. `_maybe_confirm`'s guard (`is not None` ->
        # no-op) stops a second gated trigger from stacking a second dialog
        # on top of the first (the dialog is non-modal, so clicks can still
        # reach this screen -- see `confirm_dialog.py`'s docstring).
        self._confirm_dialog: ConfirmDialog | None = None
        # `(hard_mode, moving)` of the last `_sync_hard_mode_visuals()` that
        # actually did work -- lets per-tick calls skip redundant canvas
        # toggles / repository color reads when nothing changed (Story 2.8).
        self._last_hard_sync_state: tuple[bool, bool] | None = None

        self._hud = _HudRow(
            self,
            theme=theme,
            level=_level_label(self._session.level),
            difficulty=_difficulty_label(self._session.difficulty),
            time=self._session.elapsed.to_clock_string(),
            pos=_pos_text(self._session.position),
        )
        self._hud.pack(fill="x", pady=(0, SPACING["lg"]))

        self._sidebar = _Sidebar(
            self,
            theme=theme,
            mode_active=self._session.mode is MovementMode.SMOOTH,
            speed_label=_speed_label(self._session.speed),
            hard_active=self._session.hard_mode,
            level_label=_level_label(self._session.level),
            difficulty_label=_difficulty_label(self._session.difficulty),
            difficulty_enabled=self._difficulty_enabled(),
            logo_key=read_theme_logo(settings_repository),
            show_edit_in_builder=self._maze.kind in {MazeKind.CLASSIC, MazeKind.SAVED_RANDOM},
            on_toggle_mode=self._toggle_mode,
            on_cycle_speed=self._cycle_speed,
            on_toggle_hard_mode=self._toggle_hard_mode,
            on_level_minus=functools.partial(self._cycle_level, -1),
            on_level_plus=functools.partial(self._cycle_level, +1),
            on_difficulty_minus=functools.partial(self._cycle_difficulty, -1),
            on_difficulty_plus=functools.partial(self._cycle_difficulty, +1),
            on_edit_in_builder=self._on_edit_in_builder_clicked,
        )
        self._sidebar.pack(side="left", fill="y", padx=(0, SPACING["lg"]))

        self._build_maze_frame(colors, theme)
        self._rendered_visibility = self._session.visibility
        self._save_zone = tk.Frame(self, background=colors.window)
        self._save_zone.pack(anchor="w", pady=(SPACING["lg"], 0))
        self._build_save_zone()

        for action_id, direction in _DIRECTION_ACTION_IDS:
            kb = keybinding(action_id)
            bind_shortcut(self, kb, functools.partial(self._on_move, direction))
        mode_kb = keybinding("toggle_movement_mode")
        bind_shortcut(self, mode_kb, self._toggle_mode)
        hard_kb = keybinding("toggle_hard_mode")
        self._hard_mode_handler = bind_shortcut(self, hard_kb, self._toggle_hard_mode)

        # `add="+"`: `bind_shortcut()` above already registered its own
        # `<Destroy>` cleanup on `self` (once per keybinding, each via
        # `add="+"`) -- a plain `self.bind("<Destroy>", ...)` with no `add`
        # argument *replaces* every previously bound handler for that
        # sequence, which would silently wipe those out and leak the
        # `bind_all()` shortcuts past this screen's own teardown.
        self.bind("<Destroy>", self._on_destroy, add="+")
        self._tick_job = self.after(_TICK_INTERVAL_MS, self._on_tick)

    # -- construction ------------------------------------------------------

    def _on_edit_in_builder_clicked(self) -> None:
        if self._navigate is not None:
            self._navigate(ScreenId.BUILDER, self._maze)

    def _build_maze_frame(self, colors: ColorTokens, theme: Theme) -> None:
        self._maze_frame = tk.Frame(
            self,
            background=colors.window,
            highlightthickness=1,
            highlightbackground=colors.border,
            highlightcolor=colors.border,
        )
        self._maze_frame.pack(anchor="w", pady=(0, SPACING["lg"]))

        self._maze_canvas = MazeCanvas(
            self._maze_frame, self._maze, self._session.position, theme=theme
        )
        self._maze_canvas.pack()

    def _build_save_zone(self) -> None:
        for child in self._save_zone.winfo_children():
            child.destroy()
        if hasattr(self, "_save_button"):
            del self._save_button

        if self._maze.kind is not MazeKind.GENERATED:
            return

        save_kb = keybinding("save_maze")
        self._save_button = PillButton(
            self._save_zone,
            save_kb.label,
            theme=self._theme,
            primary=True,
            shortcut=save_kb.display,
            command=self._on_save_clicked,
        )
        self._save_button.pack(anchor="w")
        bind_shortcut(self._save_button, save_kb, self._on_save_clicked)

    # -- focus guard -------------------------------------------------------

    def _toplevel_has_focus(self) -> bool:
        # Movement/mode shortcuts are bound via `bind_all()` (Story 1.10),
        # which fires regardless of which widget holds focus -- including any
        # widget inside `SaveMazeDialog` (a separate `Toplevel`;
        # `focus_get()` is application-wide, not scoped to this screen's own
        # toplevel). Guarding by widget *class* (e.g. `isinstance(...,
        # tk.Entry)`) only covers the name field itself -- tabbing from there
        # to the dialog's own Save/Cancel `PillButton`s (both
        # `takefocus=True`) would escape that guard and move the ball / toggle
        # the mode behind the still-open dialog. Guarding by *toplevel*
        # instead covers every widget any current or future dialog might
        # contain. Guarding here, rather than with a per-widget `"break"`
        # key binding, is deliberate: an instance-level `"break"` stops Tk's
        # bindtag scan before a widget's own *class* binding (e.g. an
        # `Entry`'s cursor movement/self-insert) ever runs, which would
        # silently disable that behavior (confirmed live).
        focused = self.focus_get()
        return focused is None or focused.winfo_toplevel() is self.winfo_toplevel()

    # -- movement ----------------------------------------------------------

    def _on_move(self, direction: Direction) -> None:
        if not self._toplevel_has_focus():
            return

        previous_moving = self._session.moving_direction
        self._session = session_request_move(self._session, direction)
        self._sync_visibility()
        self._sync_hard_mode_visuals()

        if self._session.moving_direction is not None and previous_moving is None:
            self._animation_job = self.after(self._per_step_ms(), self._on_animation_tick)

    def _on_animation_tick(self) -> None:
        previous_position = self._session.position
        self._session = session_advance_step(self._session)
        self._sync_visibility()
        # Sync before the solved branch so a rest-after-solve keeps the ball
        # visible at rest (`moving_direction` is None on solve).
        self._sync_hard_mode_visuals()

        direction = self._session.moving_direction
        if direction is not None:
            fraction = self._session.step / STEPS_PER_CELL
            self._maze_canvas.set_ball_offset(
                self._session.position,
                direction.row_delta * fraction,
                direction.col_delta * fraction,
            )
        else:
            self._maze_canvas.set_ball_position(self._session.position)

        if self._session.position != previous_position:
            self._hud.set_pos(_pos_text(self._session.position))

        if self._session.solved:
            # Refresh elapsed from the wall clock before showing the win
            # banner -- `self._session.elapsed` otherwise only reflects the
            # last full-second `_on_tick()` boundary, up to ~1s stale.
            # `session_tick()` itself is a no-op once `solved` (by design,
            # see its docstring), so replace the field directly here rather
            # than routing through it.
            elapsed_ms = int((time.monotonic() - self._start_time) * 1000)
            self._session = dataclasses.replace(
                self._session, elapsed=Duration(milliseconds=elapsed_ms)
            )
            self._cancel_tick_job()
            self._cancel_animation_job()
            self._on_solved()
            return

        self._reschedule_animation()

    def _per_step_ms(self) -> int:
        # Recompute the per-step delay from the *current* speed so a live
        # `set_speed` change takes effect immediately on the next reschedule.
        return cell_crossing_duration(self._session.speed).milliseconds // STEPS_PER_CELL

    def _reschedule_animation(self) -> None:
        if self._session.moving_direction is None:
            return
        self._animation_job = self.after(self._per_step_ms(), self._on_animation_tick)

    def _cancel_animation_job(self) -> None:
        if self._animation_job is not None:
            self.after_cancel(self._animation_job)
            self._animation_job = None

    # -- movement mode & speed ---------------------------------------------

    def _sync_visibility(self) -> None:
        """Redraw the maze structure iff the session's visibility changed identity.

        `set_level`/`advance_visibility`/`note_collision` only mint a *new*
        `LevelVisibility` object when something visible changes (their
        documented contract), so this exact `is not` diff redraws exactly
        when needed and never churns a run that leaves the structure alone.
        """
        if self._session.visibility is not self._rendered_visibility:
            self._maze_canvas.redraw_structure(self._session.visibility)
            self._rendered_visibility = self._session.visibility

    def _cycle_level(self, delta: int) -> None:
        if not self._toplevel_has_focus():
            return
        # Story 2.10: the level change is gated behind
        # `confirm_level_change` (read at action time). When on, the actual
        # `session_set_level` waits for the dialog's Confirm.
        new_level = _LEVEL_CYCLE[
            (_LEVEL_CYCLE.index(self._session.level) + delta) % len(_LEVEL_CYCLE)
        ]
        self._maybe_confirm(
            read_confirm_level_change(self._settings_repository),
            message=f"Change the level to {_level_label(new_level)}?",
            on_confirm=functools.partial(self._apply_level_cycle, delta),
        )

    def _apply_level_cycle(self, delta: int) -> None:
        new_level = _LEVEL_CYCLE[
            (_LEVEL_CYCLE.index(self._session.level) + delta) % len(_LEVEL_CYCLE)
        ]
        self._session = session_set_level(self._session, new_level)
        self._sync_level_widgets()
        self._sync_difficulty_widgets()
        self._sync_visibility()

    def _maybe_confirm(
        self,
        enabled: bool,
        *,
        message: str,
        on_confirm: Callable[[], None] | None = None,
    ) -> None:
        """Gate an action behind a `ConfirmDialog` when `enabled`.

        Never stacks: a second trigger while a dialog is already open is a
        no-op (the dialog is non-modal, so a click could otherwise reach
        this screen behind it). When `enabled`, opens the dialog and stores
        it so the owning action's `on_confirm` only runs on Confirm; when
        `enabled` is `False`, applies the action immediately (AC-2). When
        `enabled` is `True`, checks for an open dialog first (anti-stacking),
        then opens the ConfirmDialog. `on_close` clears the guard.
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

    def _sync_level_widgets(self) -> None:
        label = _level_label(self._session.level)
        self._hud.set_level(label)
        self._sidebar.set_level(label)

    def _cycle_difficulty(self, delta: int) -> None:
        if not self._toplevel_has_focus():
            return
        if not self._difficulty_enabled():
            return
        new_difficulty = _DIFFICULTY_CYCLE[
            (_DIFFICULTY_CYCLE.index(self._session.difficulty) + delta) % len(_DIFFICULTY_CYCLE)
        ]
        self._session = session_set_difficulty(self._session, new_difficulty)
        self._sync_difficulty_widgets()
        self._sync_visibility()

    def _sync_difficulty_widgets(self) -> None:
        enabled = self._difficulty_enabled()
        label = _difficulty_label(self._session.difficulty)
        self._sidebar.set_difficulty(label, enabled=enabled)
        self._hud.set_difficulty(label)

    def _difficulty_enabled(self) -> bool:
        return self._session.level not in (Level.ONE, Level.MAX)

    def _toggle_mode(self) -> None:
        if not self._toplevel_has_focus():
            return
        new_mode = (
            MovementMode.DISCRETE
            if self._session.mode is MovementMode.SMOOTH
            else MovementMode.SMOOTH
        )
        self._session = session_set_mode(self._session, new_mode)
        write_movement_mode(self._settings_repository, new_mode)
        self._sync_mode_button()

    def _sync_mode_button(self) -> None:
        self._sidebar.sync_mode_button(self._session.mode is MovementMode.SMOOTH)

    def _cycle_speed(self) -> None:
        if not self._toplevel_has_focus():
            return
        new_speed = _SPEED_CYCLE[(_SPEED_CYCLE.index(self._session.speed) + 1) % len(_SPEED_CYCLE)]
        self._session = session_set_speed(self._session, new_speed)
        write_movement_speed(self._settings_repository, new_speed)
        self._sidebar.set_speed_label(_speed_label(new_speed))

    # -- HARD mode (Story 2.8) ------------------------------------------

    def _hard_mode_colors(self) -> tuple[str, str]:
        """The current `(ready, moving)` status-light colors, read fresh.

        Both states read their color from the `game`-scoped settings on every
        call -- never cached -- so a settings change recolors ready *and*
        moving consistently and can never break the ready<->moving toggle
        (AC-4). The theme defaults (`colors.accent` ready / `colors.exit`
        moving, per DESIGN.md `status-light-default`) are passed into the
        application-layer readers as parameters, keeping `application/`
        theme-agnostic.
        """
        colors = colors_for(self._theme)
        return (
            read_hard_mode_ready_color(self._settings_repository, colors.accent),
            read_hard_mode_moving_color(self._settings_repository, colors.exit),
        )

    def _toggle_hard_mode(self) -> None:
        if not self._toplevel_has_focus():
            return
        new = not self._session.hard_mode
        self._session = session_set_hard_mode(self._session, new)
        # Derive the button's active flag from the *session*, not the
        # requested `new` value: `set_hard_mode` is a strict no-op once
        # solved, so flipping the button from `new` there would show it
        # "active" while `session.hard_mode` is still `False` (the
        # `_toggle_mode`/`_sync_mode_button` convention -- the button always
        # mirrors the session).
        self._sidebar.sync_hard_button(self._session.hard_mode)
        self._sync_hard_mode_visuals()

    def _sync_hard_mode_visuals(self) -> None:
        """Make the fog/ball/status light match the current HARD + moving state.

        Driven by `session.moving_direction` (leg start/stop), never by
        animation sub-steps, and only toggles canvas item `state` -- it never
        redraws structure. With HARD off the light is hidden and the ball is
        shown; with HARD on the light packs in and colors/labels follow
        ready vs. moving from `_hard_mode_colors()`.

        The `(hard_mode, moving)` guard makes repeated per-tick calls cheap:
        only the leg start/stop and toggle transitions that actually change
        the visual state do any work (canvas `itemconfigure` + the two
        fresh repository color reads), so the default HARD-off path and the
        steady-moving path both cost a tuple compare per sub-step.
        """
        hard = self._session.hard_mode
        moving = hard and self._session.moving_direction is not None
        state = (hard, moving)
        if state == self._last_hard_sync_state:
            return
        self._last_hard_sync_state = state
        self._maze_canvas.set_hard_mode_moving(moving)
        if not hard:
            self._hud.hide_hard_mode_status()
            return
        ready_color, moving_color = self._hard_mode_colors()
        self._hud.show_hard_mode_status(
            moving=moving, ready_color=ready_color, moving_color=moving_color
        )

    # -- elapsed-time ticking ----------------------------------------------

    def _on_tick(self) -> None:
        elapsed_ms = int((time.monotonic() - self._start_time) * 1000)
        self._session = session_tick(self._session, Duration(milliseconds=elapsed_ms))
        self._hud.set_time(self._session.elapsed.to_clock_string())
        # The timeout check sits after the chip update, before the
        # reschedule: the timeout branch fires once the limit is reached on
        # an unsolved run and stops the loop here (no reschedule). The
        # `not solved` guard resolves the solve/timeout race in favor of the
        # win -- whichever `.after()` callback runs first wins.
        if (
            not self._session.solved
            and self._time_limit is not None
            and elapsed_ms >= self._time_limit.milliseconds
        ):
            self._on_timeout()
            return
        self._tick_job = self.after(_TICK_INTERVAL_MS, self._on_tick)

    def _cancel_tick_job(self) -> None:
        if self._tick_job is not None:
            self.after_cancel(self._tick_job)
            self._tick_job = None

    def _on_destroy(self, _event: tk.Event | None = None) -> None:
        self._cancel_tick_job()
        self._cancel_animation_job()

    # -- time limit / timeout (Story 2.9) ------------------------------

    def _on_timeout(self) -> None:
        # "Run stops": cancel both loops, mark the session timed out (which
        # freezes movement -- every `PlayerSession` operation is a no-op once
        # `timed_out`), freeze the Time chip at the timeout value, and show
        # the inline message. No work is scheduled here; `_restart_run` is
        # the only place that rebuilds state.
        self._cancel_tick_job()
        self._cancel_animation_job()
        self._session = session_set_timed_out(self._session, True)
        self._hud.set_time(self._session.elapsed.to_clock_string())
        self._show_timeout_banner()

    def _show_timeout_banner(self) -> None:
        # Mirrors `_show_win_banner` (UX-DR9): the same `_OutcomeBanner`
        # shape, the same `before=self._maze_frame` placement, non-modal
        # inline -- never a `messagebox`.
        self._timeout_banner = _OutcomeBanner(
            self,
            theme=self._theme,
            message="Time's up — the exit wasn't reached.",
            buttons=[
                ("Restart", self._restart_run),
                ("Continue", self._on_timeout_continue_clicked),
            ],
        )
        self._timeout_banner.pack(fill="x", pady=(0, SPACING["lg"]), before=self._maze_frame)

    def _on_timeout_continue_clicked(self) -> None:
        # Only dismisses the banner -- `timed_out` stays `True`, the run
        # stays stopped, and the breadcrumb/selection navigation remains
        # available (mirrors `_on_continue_clicked` for the win banner).
        if self._timeout_banner is not None:
            self._timeout_banner.destroy()
            self._timeout_banner = None

    def _restart_run(self) -> None:
        # Story 2.10: the restart is gated behind `confirm_restart` (read
        # at action time -- AC-3). When on, the actual fresh run waits for
        # the dialog's Confirm.
        self._maybe_confirm(
            read_confirm_restart(self._settings_repository),
            message="Restart the run for this maze?",
            on_confirm=self._apply_restart_run,
        )

    def _apply_restart_run(self) -> None:
        # A fresh run for the same maze, exactly what a re-mount would build:
        # `start_session` defaults (Level ONE, Difficulty ONE, HARD off --
        # all session-scoped, never persisted) plus re-applied persisted
        # mode/speed and a fresh `read_time_limit`. Leaves the screen fully
        # interactive again (a `_tick_job` is rescheduled).
        self._cancel_tick_job()
        self._cancel_animation_job()
        self._session = start_session(self._maze)
        self._session = session_set_mode(
            self._session, read_movement_mode(self._settings_repository)
        )
        self._session = session_set_speed(
            self._session, read_movement_speed(self._settings_repository)
        )
        self._time_limit = read_time_limit(self._settings_repository)
        self._start_time = time.monotonic()
        self._maze_canvas.redraw_structure(self._session.visibility)
        self._rendered_visibility = self._session.visibility
        self._maze_canvas.set_ball_position(self._session.position)
        self._sync_level_widgets()
        self._sync_difficulty_widgets()
        self._sync_mode_button()
        self._hud.set_time(self._session.elapsed.to_clock_string())
        self._hud.set_pos(_pos_text(self._session.position))
        if self._timeout_banner is not None:
            self._timeout_banner.destroy()
            self._timeout_banner = None
        if self._win_banner is not None:
            self._win_banner.destroy()
            self._win_banner = None
        # The fresh session has HARD off, so the status light hides and the
        # ball shows again; resetting `_last_hard_sync_state` forces the sync
        # to actually run (Story 2.8). The HARD button mirrors the session
        # too, so a restart from a HARD-on timeout de-activates it.
        self._sidebar.sync_hard_button(False)
        self._last_hard_sync_state = None
        self._sync_hard_mode_visuals()
        self._tick_job = self.after(_TICK_INTERVAL_MS, self._on_tick)

    # -- win banner ------------------------------------------------------

    def _on_solved(self) -> None:
        # Freeze the tick loop the moment the session is solved, rather
        # than letting the already-scheduled `.after()` job fire once more
        # up to a second late (it would be a harmless no-op via
        # `player_session.tick`'s own solved guard, but cancelling here
        # keeps the Time chip's freeze visibly immediate).
        self._cancel_tick_job()
        # Reflect the same freshly-refreshed `self._session.elapsed` (see
        # `_on_animation_tick`) the win banner is about to show, so the
        # frozen Time chip and the banner's "Solved in MM:SS." text never
        # disagree.
        self._hud.set_time(self._session.elapsed.to_clock_string())
        self._show_win_banner()

    def _show_win_banner(self) -> None:
        # `on_back_to_builder is not None` is test mode (Builder's Test in
        # Player, Story 3.8): instead of Continue, the banner offers
        # Restart (a fresh run, exactly the timeout banner's own Restart)
        # and Back to Builder (returns to the Builder, restoring the
        # session's markers from the `BuilderTestLaunch` payload the screen
        # was mounted with).
        if self._on_back_to_builder is not None:
            buttons = [
                ("Restart", self._restart_run),
                ("Back to Builder", self._on_back_to_builder),
            ]
        else:
            buttons = [("Continue", self._on_continue_clicked)]
        self._win_banner = _OutcomeBanner(
            self,
            theme=self._theme,
            message=f"Solved in {self._session.elapsed.to_clock_string()}.",
            buttons=buttons,
        )
        self._win_banner.pack(fill="x", pady=(0, SPACING["lg"]), before=self._maze_frame)

    def _on_continue_clicked(self) -> None:
        # Only dismisses the banner -- `solved` stays `True`, and
        # `player_session` functions are already no-ops once solved (see
        # the story's Design Notes), so nothing else needs resetting here.
        if self._win_banner is not None:
            self._win_banner.destroy()
            self._win_banner = None

    # -- save flow (Story 2.3, unchanged) -------------------------------

    def _on_save_clicked(self) -> None:
        existing_names = self._maze_repository.list_names(MazeKind.SAVED_RANDOM)
        SaveMazeDialog(
            self,
            theme=self._theme,
            existing_names=existing_names,
            on_confirm=self._on_save_confirmed,
        )

    def _on_save_confirmed(self, name: str) -> None:
        candidate = dataclasses.replace(self._maze, kind=MazeKind.SAVED_RANDOM, id=None)
        self._maze = self._maze_repository.save(candidate, name)
        # Keep `self._session.maze` in lockstep with `self._maze` -- grid/
        # entry/exit are unchanged by the kind/id transition so movement
        # math is unaffected either way, but leaving them to silently
        # diverge would be a latent trap for any future code reading
        # `session.maze.kind`/`id`.
        self._session = dataclasses.replace(self._session, maze=self._maze)
        self._build_save_zone()
        if self._on_kind_changed is not None:
            self._on_kind_changed(self._maze.kind)
