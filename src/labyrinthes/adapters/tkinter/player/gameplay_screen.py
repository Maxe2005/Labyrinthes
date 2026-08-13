"""`GameplayScreen` -- rendering, HUD, movement modes, win detection (Story 2.4/2.5).

A `MazeCanvas` renders the mounted `Maze`'s walls/entry/exit/ball once, an
HUD row of `HudChip`s shows Level/Difficulty/Time/Pos, arrow keys drive a
pure `domain.movement.attempt_move` + `application.player_session`
orchestration loop, and reaching `maze.exit` shows an inline win banner.

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

Movement mechanics/session orchestration are pure functions imported from
`domain`/`application` -- this module only wires input events to them,
renders the result, and owns the `.after()` loops (the elapsed-time tick and
the per-sub-step animation tick). Both tick jobs are cancelled on `<Destroy>`
and on solve so a torn-down or solved screen never fires a stale callback.
"""

from __future__ import annotations

import dataclasses
import functools
import time
import tkinter as tk
from collections.abc import Callable

from labyrinthes.adapters.tkinter.common.hud_chip import HudChip
from labyrinthes.adapters.tkinter.common.keybindings import bind_shortcut, keybinding
from labyrinthes.adapters.tkinter.common.pill_btn import PillButton
from labyrinthes.adapters.tkinter.common.tokens import (
    SPACING,
    TYPOGRAPHY,
    ColorTokens,
    Theme,
    colors_for,
)
from labyrinthes.adapters.tkinter.common.tool_btn import ToolButton
from labyrinthes.adapters.tkinter.player.maze_canvas import MazeCanvas
from labyrinthes.adapters.tkinter.player.save_maze_dialog import SaveMazeDialog
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
    set_mode as session_set_mode,
)
from labyrinthes.application.player_session import (
    set_speed as session_set_speed,
)
from labyrinthes.application.player_session import (
    tick as session_tick,
)
from labyrinthes.application.settings_repository import SettingsRepository
from labyrinthes.domain.duration import Duration
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.movement import Direction
from labyrinthes.domain.movement_mode import MovementMode
from labyrinthes.domain.movement_speed import MovementSpeed, cell_crossing_duration
from labyrinthes.domain.position import Position

__all__ = ["GameplayScreen"]

_TICK_INTERVAL_MS = 1000

_PLACEHOLDER_LEVEL = "1"
_PLACEHOLDER_DIFFICULTY = "—"

_DIRECTION_ACTION_IDS: tuple[tuple[str, Direction], ...] = (
    ("move_up", Direction.UP),
    ("move_down", Direction.DOWN),
    ("move_left", Direction.LEFT),
    ("move_right", Direction.RIGHT),
)

_SPEED_CYCLE: tuple[MovementSpeed, ...] = tuple(MovementSpeed)


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
        on_kind_changed: Callable[[MazeKind], None] | None = None,
    ) -> None:
        colors = colors_for(theme)
        super().__init__(parent, background=colors.window)
        self._theme = theme
        self._maze_repository = maze_repository
        self._settings_repository = settings_repository
        self._maze = maze  # tracks kind/id across a save -- see `_build_save_zone()`
        self._on_kind_changed = on_kind_changed
        self._session = start_session(maze)
        # Apply the `game`-scoped settings-loaded mode/speed at mount. This
        # screen is rebuilt on re-navigate, so settings loaded here are fresh.
        self._session = session_set_mode(self._session, read_movement_mode(settings_repository))
        self._session = session_set_speed(self._session, read_movement_speed(settings_repository))
        self._start_time = time.monotonic()
        self._tick_job: str | None = None
        self._animation_job: str | None = None
        self._win_banner: tk.Frame | None = None

        self._build_hud(colors)
        self._build_sidebar(colors)
        self._build_maze_frame(colors, theme)
        self._save_zone = tk.Frame(self, background=colors.window)
        self._save_zone.pack(anchor="w", pady=(SPACING["lg"], 0))
        self._build_save_zone()

        for action_id, direction in _DIRECTION_ACTION_IDS:
            kb = keybinding(action_id)
            bind_shortcut(self, kb, functools.partial(self._on_move, direction))
        mode_kb = keybinding("toggle_movement_mode")
        bind_shortcut(self, mode_kb, self._toggle_mode)

        # `add="+"`: `bind_shortcut()` above already registered its own
        # `<Destroy>` cleanup on `self` (once per keybinding, each via
        # `add="+"`) -- a plain `self.bind("<Destroy>", ...)` with no `add`
        # argument *replaces* every previously bound handler for that
        # sequence, which would silently wipe those out and leak the
        # `bind_all()` shortcuts past this screen's own teardown.
        self.bind("<Destroy>", self._on_destroy, add="+")
        self._tick_job = self.after(_TICK_INTERVAL_MS, self._on_tick)

    # -- construction ------------------------------------------------------

    def _build_hud(self, colors: ColorTokens) -> None:
        hud_row = tk.Frame(self, background=colors.window)
        hud_row.pack(fill="x", pady=(0, SPACING["lg"]))

        self._level_chip = HudChip(hud_row, "Level", _PLACEHOLDER_LEVEL, theme=self._theme)
        self._level_chip.pack(side="left", padx=(0, SPACING["sm"]))

        self._difficulty_chip = HudChip(
            hud_row, "Difficulty", _PLACEHOLDER_DIFFICULTY, theme=self._theme
        )
        self._difficulty_chip.pack(side="left", padx=(0, SPACING["sm"]))

        self._time_chip = HudChip(
            hud_row, "Time", self._session.elapsed.to_clock_string(), theme=self._theme, live=True
        )
        self._time_chip.pack(side="left", padx=(0, SPACING["sm"]))

        self._pos_chip = HudChip(
            hud_row, "Pos", _pos_text(self._session.position), theme=self._theme
        )
        self._pos_chip.pack(side="left")

    def _build_sidebar(self, colors: ColorTokens) -> None:
        self._sidebar = tk.Frame(self, background=colors.window)
        self._sidebar.pack(side="left", fill="y", padx=(0, SPACING["lg"]))

        tk.Label(
            self._sidebar,
            text="Movement",
            font=TYPOGRAPHY.body.to_tk_font(),
            background=colors.window,
            foreground=colors.ink,
        ).pack(anchor="w", pady=(0, SPACING["sm"]))

        mode_kb = keybinding("toggle_movement_mode")
        self._mode_button = ToolButton(
            self._sidebar,
            "Smooth",
            theme=self._theme,
            shortcut=mode_kb.display,
            command=self._toggle_mode,
        )
        self._mode_button.pack(anchor="w", pady=(0, SPACING["sm"]))

        self._speed_button = ToolButton(
            self._sidebar,
            _speed_label(self._session.speed),
            theme=self._theme,
            command=self._cycle_speed,
        )
        self._speed_button.pack(anchor="w")

        self._sync_mode_button()

    def _sync_mode_button(self) -> None:
        self._mode_button.set_active(self._session.mode is MovementMode.SMOOTH)

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

        if self._session.moving_direction is not None and previous_moving is None:
            per_step_ms = cell_crossing_duration(self._session.speed).milliseconds // STEPS_PER_CELL
            self._animation_job = self.after(per_step_ms, self._on_animation_tick)

    def _on_animation_tick(self) -> None:
        previous_position = self._session.position
        self._session = session_advance_step(self._session)

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
            self._pos_chip.set_value(_pos_text(self._session.position))

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

    def _reschedule_animation(self) -> None:
        if self._session.moving_direction is None:
            return
        # Recompute the per-step delay from the *current* speed on every
        # reschedule so a live `set_speed` change takes effect immediately.
        per_step_ms = cell_crossing_duration(self._session.speed).milliseconds // STEPS_PER_CELL
        self._animation_job = self.after(per_step_ms, self._on_animation_tick)

    def _cancel_animation_job(self) -> None:
        if self._animation_job is not None:
            self.after_cancel(self._animation_job)
            self._animation_job = None

    # -- movement mode & speed ---------------------------------------------

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

    def _cycle_speed(self) -> None:
        if not self._toplevel_has_focus():
            return
        new_speed = _SPEED_CYCLE[(_SPEED_CYCLE.index(self._session.speed) + 1) % len(_SPEED_CYCLE)]
        self._session = session_set_speed(self._session, new_speed)
        write_movement_speed(self._settings_repository, new_speed)
        self._speed_button.set_text(_speed_label(new_speed))

    # -- elapsed-time ticking ----------------------------------------------

    def _on_tick(self) -> None:
        elapsed_ms = int((time.monotonic() - self._start_time) * 1000)
        self._session = session_tick(self._session, Duration(milliseconds=elapsed_ms))
        self._time_chip.set_value(self._session.elapsed.to_clock_string())
        self._tick_job = self.after(_TICK_INTERVAL_MS, self._on_tick)

    def _cancel_tick_job(self) -> None:
        if self._tick_job is not None:
            self.after_cancel(self._tick_job)
            self._tick_job = None

    def _on_destroy(self, _event: tk.Event | None = None) -> None:
        self._cancel_tick_job()
        self._cancel_animation_job()

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
        self._time_chip.set_value(self._session.elapsed.to_clock_string())
        self._show_win_banner()

    def _show_win_banner(self) -> None:
        colors = colors_for(self._theme)
        self._win_banner = tk.Frame(
            self,
            background=colors.accent_bg,
            highlightthickness=1,
            highlightbackground=colors.accent,
            highlightcolor=colors.accent,
        )
        self._win_banner.pack(fill="x", pady=(0, SPACING["lg"]), before=self._maze_frame)

        tk.Label(
            self._win_banner,
            text=f"Solved in {self._session.elapsed.to_clock_string()}.",
            font=TYPOGRAPHY.body.to_tk_font(),
            background=colors.accent_bg,
            foreground=colors.ink,
        ).pack(side="left", padx=SPACING["lg"], pady=SPACING["sm"])

        # `primary=False`: per `PillButton`'s own docstring ("at most one
        # `primary` pill sits on a screen at a time"), not `True` here --
        # a `GENERATED` maze's Save pill (`_build_save_zone()`) can still
        # be showing underneath this banner (winning doesn't hide it), and
        # two simultaneous primary pills would violate that rule.
        PillButton(
            self._win_banner,
            "Continue",
            theme=self._theme,
            primary=False,
            command=self._on_continue_clicked,
        ).pack(side="right", padx=SPACING["lg"], pady=SPACING["sm"])

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
