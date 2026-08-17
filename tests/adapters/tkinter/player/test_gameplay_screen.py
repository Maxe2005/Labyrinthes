import dataclasses
import time
import tkinter as tk

from labyrinthes.adapters.tkinter.common.keybindings import keybinding
from labyrinthes.adapters.tkinter.common.pill_btn import PillButton
from labyrinthes.adapters.tkinter.common.tokens import Theme, colors_for
from labyrinthes.adapters.tkinter.player.gameplay_screen import GameplayScreen
from labyrinthes.adapters.tkinter.player.maze_canvas import MazeCanvas
from labyrinthes.adapters.tkinter.player.save_maze_dialog import SaveMazeDialog
from labyrinthes.application.confirmation_settings import (
    write_confirm_level_change,
    write_confirm_restart,
)
from labyrinthes.application.hard_mode_settings import (
    read_hard_mode_moving_color,
    read_hard_mode_ready_color,
    write_hard_mode_moving_color,
    write_hard_mode_ready_color,
)
from labyrinthes.application.player_session import STEPS_PER_CELL
from labyrinthes.application.settings_keys import (
    MOVEMENT_MODE,
    MOVEMENT_SPEED,
    TIME_LIMIT_SECONDS,
)
from labyrinthes.application.settings_repository import SettingsScope
from labyrinthes.application.time_limit_settings import write_time_limit
from labyrinthes.domain.cell import Cell
from labyrinthes.domain.difficulty import Difficulty
from labyrinthes.domain.duration import Duration
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.level import Level
from labyrinthes.domain.level_visibility import Wall, visible_walls
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.movement import Direction
from labyrinthes.domain.movement_mode import MovementMode
from labyrinthes.domain.movement_speed import MovementSpeed, cell_crossing_duration
from labyrinthes.domain.position import Position

# -- fixtures ------------------------------------------------------------


def _generated_maze(width=4, height=3) -> Maze:
    return Maze(
        grid=Grid.filled(width=width, height=height),
        entry=Position(row=0, col=0),
        exit=Position(row=height - 1, col=width - 1),
        kind=MazeKind.GENERATED,
        id=None,
    )


def _classic_maze(width=4, height=3) -> Maze:
    return Maze(
        grid=Grid.filled(width=width, height=height),
        entry=Position(row=0, col=0),
        exit=Position(row=height - 1, col=width - 1),
        kind=MazeKind.CLASSIC,
        id=None,
    )


def _open_maze(width=2) -> Maze:
    """A `width`x1 maze, every cell connected in a straight line, entry at the
    left, exit at the right -- lets movement tests reach the exit in `width -
    1` `Direction.RIGHT` presses."""
    real_cells = tuple(Cell("1") for _ in range(width))  # top wall only: left clear
    row = real_cells + (Cell("2"),)
    padding_row = tuple(Cell("1") for _ in range(width)) + (Cell("0"),)
    grid = Grid(cells=(row, padding_row))
    return Maze(
        grid=grid,
        entry=Position(row=0, col=0),
        exit=Position(row=0, col=width - 1),
        kind=MazeKind.CLASSIC,
        id=None,
    )


def _corridor_maze(width=4) -> Maze:
    """A 2-row corridor: row 0 open left-to-right, exit at the far right,
    everything below walled -- open enough to move across partition
    boundaries, walled enough to exercise blocked moves."""
    row0 = tuple(Cell("0") for _ in range(width)) + (Cell("2"),)
    row1 = tuple(Cell("3") for _ in range(width)) + (Cell("2"),)
    padding_row = tuple(Cell("1") for _ in range(width)) + (Cell("0"),)
    grid = Grid(cells=(row0, row1, padding_row))
    return Maze(
        grid=grid,
        entry=Position(row=0, col=0),
        exit=Position(row=0, col=width - 1),
        kind=MazeKind.CLASSIC,
        id=None,
    )


def _stopping_maze() -> Maze:
    """Corridor along row 0 that ends against an interior wall: (0,1) going
    right is blocked by the left wall of (0,2), which is not a border."""
    grid = Grid(
        cells=(
            (Cell("0"), Cell("0"), Cell("3"), Cell("0"), Cell("0"), Cell("2")),
            (Cell("3"), Cell("3"), Cell("3"), Cell("3"), Cell("3"), Cell("2")),
            (Cell("3"), Cell("3"), Cell("3"), Cell("3"), Cell("3"), Cell("2")),
            (Cell("1"), Cell("1"), Cell("1"), Cell("1"), Cell("1"), Cell("0")),
        )
    )
    return Maze(
        grid=grid,
        entry=Position(row=0, col=0),
        exit=Position(row=0, col=4),
        kind=MazeKind.CLASSIC,
        id=None,
    )


class ExplodingMazeRepository:
    def save(self, maze, name):
        raise AssertionError("save() must not be called")

    def load(self, name, kind):
        raise AssertionError("load() must not be called")

    def find_by_id(self, maze_id):
        raise AssertionError("find_by_id() must not be called")

    def list_names(self, kind):
        raise AssertionError("list_names() must not be called")


def _settle(screen) -> None:
    """Drive the animation loop until the in-flight leg completes (or the run
    is solved), so tests no longer assert an instant post-keypress state."""
    while screen._session.moving_direction is not None:
        screen._on_animation_tick()


def _use_discrete(fake_settings_repository) -> None:
    fake_settings_repository.set(SettingsScope.GAME, MOVEMENT_MODE, "discrete")


# -- initial render --------------------------------------------------------


def test_initial_render_shows_the_maze_canvas_with_entry_exit_and_ball(
    tk_root, fake_maze_repository, fake_settings_repository
):
    maze = _classic_maze()
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    canvas = screen._maze_canvas
    assert isinstance(canvas, MazeCanvas)
    assert len(canvas.find_withtag("wall")) > 0
    assert len(canvas.find_withtag("entry-marker")) == 1
    assert len(canvas.find_withtag("exit-marker")) == 1
    ball_items = canvas.find_withtag("ball")
    assert len(ball_items) == 1
    # Same center as the entry marker, smaller bounding box -- the ball is
    # deliberately smaller than a marker so the marker's shape stays
    # visible as a ring around it (NFR6), not exact-coordinate equality.
    entry_x0, entry_y0, entry_x1, entry_y1 = canvas.coords(canvas.find_withtag("entry-marker")[0])
    ball_x0, ball_y0, ball_x1, ball_y1 = canvas.coords(ball_items[0])
    assert ((ball_x0 + ball_x1) / 2, (ball_y0 + ball_y1) / 2) == (
        (entry_x0 + entry_x1) / 2,
        (entry_y0 + entry_y1) / 2,
    )
    assert (ball_x1 - ball_x0) < (entry_x1 - entry_x0)


def test_hud_shows_level_and_difficulty_and_initial_time_and_pos(
    tk_root, fake_maze_repository, fake_settings_repository
):
    maze = _classic_maze()
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    assert screen._level_chip._value_label.cget("text") == "1"
    assert screen._difficulty_chip._value_label.cget("text") == "1"
    assert screen._time_chip._value_label.cget("text") == "00:00"
    assert screen._pos_chip._value_label.cget("text") == "(0, 0)"


def test_settings_loaded_at_mount_apply_to_the_session(
    tk_root, fake_maze_repository, fake_settings_repository
):
    fake_settings_repository.set(SettingsScope.GAME, MOVEMENT_MODE, "discrete")
    fake_settings_repository.set(SettingsScope.GAME, MOVEMENT_SPEED, "fast")
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    assert screen._session.mode is MovementMode.DISCRETE
    assert screen._session.speed is MovementSpeed.FAST


# -- movement ------------------------------------------------------


def test_move_through_an_open_passage_updates_the_ball_and_pos_chip(
    tk_root, fake_maze_repository, fake_settings_repository
):
    _use_discrete(fake_settings_repository)
    maze = _open_maze(width=3)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    ball_coords_before = screen._maze_canvas.coords(screen._maze_canvas.find_withtag("ball")[0])

    screen._on_move(Direction.RIGHT)
    _settle(screen)

    assert screen._session.position == Position(row=0, col=1)
    assert screen._pos_chip._value_label.cget("text") == "(0, 1)"
    ball_coords_after = screen._maze_canvas.coords(screen._maze_canvas.find_withtag("ball")[0])
    assert ball_coords_after != ball_coords_before


def test_move_blocked_by_a_wall_leaves_the_ball_and_pos_chip_unchanged(
    tk_root, fake_maze_repository, fake_settings_repository
):
    maze = _classic_maze()
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    ball_coords_before = screen._maze_canvas.coords(screen._maze_canvas.find_withtag("ball")[0])

    screen._on_move(Direction.UP)  # blocked: entry (0, 0) is fully walled

    assert screen._session.position == maze.entry
    assert screen._pos_chip._value_label.cget("text") == "(0, 0)"
    ball_coords_after = screen._maze_canvas.coords(screen._maze_canvas.find_withtag("ball")[0])
    assert ball_coords_after == ball_coords_before


def test_movement_shortcuts_are_registered(tk_root, fake_maze_repository, fake_settings_repository):
    GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    for action_id in ("move_up", "move_down", "move_left", "move_right"):
        kb = keybinding(action_id)
        assert tk_root.bind_all(kb.event) != ""


def test_move_is_a_no_op_while_a_text_entry_holds_focus(
    tk_root, fake_maze_repository, fake_settings_repository
):
    # The `save_maze` Save dialog's name field is a real `tk.Entry` in a
    # separate `Toplevel`; `move_*` fires via `bind_all()` regardless of
    # focus, so `_on_move` must itself refuse to act while any `Entry` --
    # anywhere in the application, not just this screen -- holds focus.
    # (`focus_get()` is application-wide, confirmed empirically.) This is
    # deliberately *not* a per-`Entry` key-binding "break" guard: that
    # would also swallow the `Entry`'s own class binding and disable its
    # cursor navigation, not just this shortcut -- see `_on_move`'s
    # docstring.
    maze = _open_maze(width=3)
    screen = GameplayScreen(
        tk_root,
        dataclasses.replace(maze, kind=MazeKind.GENERATED),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._on_save_clicked()
    dialog = next(c for c in screen.winfo_children() if isinstance(c, SaveMazeDialog))
    dialog._name_entry.focus_set()
    tk_root.update()

    screen._on_move(Direction.RIGHT)

    assert screen._session.position == maze.entry


def test_move_is_a_no_op_while_focus_is_on_a_non_entry_widget_in_another_toplevel(
    tk_root, fake_maze_repository, fake_settings_repository
):
    # Regression: guarding by widget *class* (`isinstance(..., tk.Entry)`)
    # only covers the dialog's name field -- tabbing from there to the
    # dialog's own Save `PillButton` (also `takefocus=True`, not an
    # `Entry`) used to escape the guard entirely, letting arrow keys move
    # the ball behind the still-open dialog. Guarding by *toplevel*
    # instead covers every widget in the dialog, not just the `Entry`.
    maze = _open_maze(width=3)
    screen = GameplayScreen(
        tk_root,
        dataclasses.replace(maze, kind=MazeKind.GENERATED),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._on_save_clicked()
    dialog = next(c for c in screen.winfo_children() if isinstance(c, SaveMazeDialog))
    dialog._save_button.focus_set()
    tk_root.update()

    screen._on_move(Direction.RIGHT)

    assert screen._session.position == maze.entry


# -- win detection ------------------------------------------------------


def test_reaching_the_exit_marks_the_session_solved_and_shows_a_win_banner(
    tk_root, fake_maze_repository, fake_settings_repository
):
    maze = _open_maze(width=2)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    screen._on_move(Direction.RIGHT)
    _settle(screen)

    assert screen._session.solved is True
    assert screen._session.position == maze.exit
    assert screen._win_banner is not None
    assert screen._win_banner.winfo_exists()


def test_win_banner_text_reports_the_elapsed_clock_string(
    tk_root, fake_maze_repository, fake_settings_repository
):
    maze = _open_maze(width=2)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    screen._on_move(Direction.RIGHT)
    _settle(screen)

    labels = [child for child in screen._win_banner.winfo_children() if isinstance(child, tk.Label)]
    texts = [child.cget("text") for child in labels]
    assert any(text.startswith("Solved in ") and text.endswith(".") for text in texts)


def test_continue_button_is_not_a_primary_pill(
    tk_root, fake_maze_repository, fake_settings_repository
):
    # Regression: a `GENERATED` maze's Save pill (`primary=True`) can still
    # be showing when the win banner appears -- winning doesn't hide it --
    # so Continue must not also be `primary=True`, per `PillButton`'s own
    # "at most one primary pill per screen" rule.
    maze = _open_maze(width=2)
    screen = GameplayScreen(
        tk_root,
        dataclasses.replace(maze, kind=MazeKind.GENERATED),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    screen._on_move(Direction.RIGHT)
    _settle(screen)

    continue_button = next(
        c for c in screen._win_banner.winfo_children() if isinstance(c, PillButton)
    )
    assert continue_button._primary is False


def test_solving_refreshes_elapsed_from_the_wall_clock_not_the_stale_last_tick(
    tk_root, fake_maze_repository, fake_settings_repository
):
    # `session.elapsed` otherwise only advances once per second via
    # `_on_tick()` -- solving must refresh it from `time.monotonic()`
    # directly so the win banner/Time chip don't under-report by up to ~1s.
    maze = _open_maze(width=2)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._start_time = time.monotonic() - 5.0  # 5s elapsed, no `_on_tick()` has run yet
    assert screen._session.elapsed.milliseconds == 0

    screen._on_move(Direction.RIGHT)
    _settle(screen)

    assert screen._session.elapsed.milliseconds >= 5000
    assert screen._time_chip._value_label.cget("text") == "00:05"


def test_reaching_the_exit_cancels_the_pending_tick_job(
    tk_root, fake_maze_repository, fake_settings_repository
):
    maze = _open_maze(width=2)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    assert screen._tick_job is not None

    screen._on_move(Direction.RIGHT)
    _settle(screen)

    assert screen._tick_job is None


def test_move_after_solved_is_a_no_op(tk_root, fake_maze_repository, fake_settings_repository):
    maze = _open_maze(width=2)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._on_move(Direction.RIGHT)
    _settle(screen)
    assert screen._session.solved is True
    solved_position = screen._session.position

    screen._on_move(Direction.LEFT)

    assert screen._session.position == solved_position
    assert screen._session.solved is True


def test_continue_click_destroys_the_banner_but_keeps_solved_true(
    tk_root, fake_maze_repository, fake_settings_repository
):
    maze = _open_maze(width=2)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._on_move(Direction.RIGHT)
    _settle(screen)
    banner = screen._win_banner

    screen._on_continue_clicked()

    assert screen._win_banner is None
    assert not banner.winfo_exists()
    assert screen._session.solved is True


# -- movement mode & speed (Story 2.5) ----------------------------------


def test_mode_toggle_flips_the_session_mode_and_persists(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    assert screen._session.mode is MovementMode.SMOOTH
    assert screen._mode_button.active is True

    screen._toggle_mode()

    assert screen._session.mode is MovementMode.DISCRETE
    assert screen._mode_button.active is False
    assert fake_settings_repository.get(SettingsScope.GAME, MOVEMENT_MODE) == "discrete"

    screen._toggle_mode()

    assert screen._session.mode is MovementMode.SMOOTH
    assert screen._mode_button.active is True
    assert fake_settings_repository.get(SettingsScope.GAME, MOVEMENT_MODE) == "smooth"


def test_mode_shortcut_m_is_registered(tk_root, fake_maze_repository, fake_settings_repository):
    GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    kb = keybinding("toggle_movement_mode")

    assert tk_root.bind_all(kb.event) != ""


def test_speed_button_cycles_through_the_tiers_and_relabels(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    assert screen._session.speed is MovementSpeed.NORMAL
    assert screen._speed_button._label.cget("text") == "Normal"

    screen._cycle_speed()

    assert screen._session.speed is MovementSpeed.FAST
    assert screen._speed_button._label.cget("text") == "Fast"
    assert fake_settings_repository.get(SettingsScope.GAME, MOVEMENT_SPEED) == "fast"

    screen._cycle_speed()

    assert screen._session.speed is MovementSpeed.SLOW
    assert screen._speed_button._label.cget("text") == "Slow"

    screen._cycle_speed()

    assert screen._session.speed is MovementSpeed.NORMAL
    assert screen._speed_button._label.cget("text") == "Normal"


def test_animation_per_step_delay_reflects_the_current_speed_and_recomputes_on_a_live_change(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _open_maze(width=3),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    recorded: list[int] = []
    screen.after = lambda delay, callback, *args: recorded.append(delay) or "job"

    screen._on_move(Direction.RIGHT)

    normal_per_step = cell_crossing_duration(MovementSpeed.NORMAL).milliseconds // STEPS_PER_CELL
    assert recorded == [normal_per_step]

    screen._cycle_speed()

    fast_per_step = cell_crossing_duration(MovementSpeed.FAST).milliseconds // STEPS_PER_CELL
    screen._reschedule_animation()

    assert recorded == [normal_per_step, fast_per_step]


def test_mode_toggle_is_a_no_op_while_focus_is_in_another_toplevel(
    tk_root, fake_maze_repository, fake_settings_repository
):
    # The `tk_root` fixture is withdrawn, so `focus_get()` returns None and
    # real focus can't be granted to a dialog widget headless -- stub it to
    # report a widget in a *separate* `Toplevel`, exactly the state a live
    # `SaveMazeDialog` with focus would produce.
    screen = GameplayScreen(
        tk_root,
        dataclasses.replace(_open_maze(width=3), kind=MazeKind.GENERATED),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    other = tk.Toplevel(tk_root)
    other_entry = tk.Entry(other)
    screen.focus_get = lambda: other_entry

    screen._toggle_mode()

    assert screen._session.mode is MovementMode.SMOOTH
    other.destroy()


def test_toplevel_has_focus_is_false_when_focus_is_elsewhere(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    other = tk.Toplevel(tk_root)
    other_entry = tk.Entry(other)
    screen.focus_get = lambda: other_entry

    assert screen._toplevel_has_focus() is False
    other.destroy()


def test_toplevel_has_focus_is_true_when_nothing_elsewhere_is_focused(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen.focus_get = lambda: None

    assert screen._toplevel_has_focus() is True


def test_destroying_the_screen_cancels_the_pending_animation_job(
    tk_root, fake_maze_repository, fake_settings_repository
):
    _use_discrete(fake_settings_repository)
    screen = GameplayScreen(
        tk_root,
        _open_maze(width=3),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._on_move(Direction.RIGHT)
    assert screen._animation_job is not None

    screen.destroy()
    tk_root.update()

    assert screen._animation_job is None


# -- elapsed-time ticking ------------------------------------------


def test_on_tick_updates_the_time_chip_and_reschedules(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    # Fake an elapsed 2.5s without depending on real wall-clock sleeps.
    screen._start_time = time.monotonic() - 2.5

    screen._on_tick()

    assert screen._time_chip._value_label.cget("text") == "00:02"
    assert screen._session.elapsed.milliseconds >= 2500
    assert screen._tick_job is not None


def test_destroying_the_screen_cancels_the_pending_tick_job(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    assert screen._tick_job is not None

    screen.destroy()
    tk_root.update()

    assert screen._tick_job is None


def test_destroying_the_screen_also_unregisters_the_movement_shortcuts(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    move_up = keybinding("move_up")
    toggle_mode = keybinding("toggle_movement_mode")
    assert tk_root.bind_all(move_up.event) != ""
    assert tk_root.bind_all(toggle_mode.event) != ""

    screen.destroy()
    tk_root.update()

    assert tk_root.bind_all(move_up.event) == ""
    assert tk_root.bind_all(toggle_mode.event) == ""


# -- save flow (Story 2.3, ported) -------------------------------------


def test_a_generated_maze_shows_the_save_button(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _generated_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    assert screen._save_button.winfo_exists()


def test_a_classic_maze_shows_no_save_button(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    assert not hasattr(screen, "_save_button")


def test_mounting_a_generated_maze_never_touches_the_repository(tk_root, fake_settings_repository):
    screen = GameplayScreen(
        tk_root,
        _generated_maze(),
        Theme.LIGHT,
        maze_repository=ExplodingMazeRepository(),
        settings_repository=fake_settings_repository,
    )

    assert screen._save_button.winfo_exists()


def test_clicking_save_opens_a_dialog_prefilled_with_existing_saved_random_names(
    tk_root, fake_maze_repository, fake_settings_repository
):
    existing = dataclasses.replace(_generated_maze(), kind=MazeKind.SAVED_RANDOM)
    fake_maze_repository.save(existing, "existing")
    screen = GameplayScreen(
        tk_root,
        _generated_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    screen._on_save_clicked()

    dialogs = [c for c in screen.winfo_children() if isinstance(c, SaveMazeDialog)]
    assert len(dialogs) == 1
    assert dialogs[0]._existing_names == ["existing"]


def test_confirming_save_calls_repository_save_once_with_the_transitioned_kind(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _generated_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    screen._on_save_confirmed("forest")

    assert fake_maze_repository.list_names(MazeKind.SAVED_RANDOM) == ["forest"]
    saved = fake_maze_repository.load("forest", MazeKind.SAVED_RANDOM)
    assert saved.kind == MazeKind.SAVED_RANDOM
    assert saved.id is not None


def test_confirming_save_updates_the_screens_own_maze_and_hides_save(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _generated_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    screen._on_save_confirmed("forest")

    assert screen._maze.kind == MazeKind.SAVED_RANDOM
    assert screen._maze.id is not None
    assert not hasattr(screen, "_save_button")


def test_confirming_save_also_updates_the_sessions_own_maze(
    tk_root, fake_maze_repository, fake_settings_repository
):
    # `self._session.maze` must not silently diverge from `self._maze` --
    # a future reader of `session.maze.kind`/`id` should see the same
    # post-save value either way.
    screen = GameplayScreen(
        tk_root,
        _generated_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    screen._on_save_confirmed("forest")

    assert screen._session.maze is screen._maze
    assert screen._session.maze.kind == MazeKind.SAVED_RANDOM


def test_confirming_save_notifies_on_kind_changed_with_the_new_kind(
    tk_root, fake_maze_repository, fake_settings_repository
):
    # Lets a caller (`screen.py`, for its kind-derived breadcrumb label)
    # stay in sync with `self._maze.kind` across a save, without
    # `GameplayScreen` needing to know anything about breadcrumbs itself.
    kinds_seen = []
    screen = GameplayScreen(
        tk_root,
        _generated_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
        on_kind_changed=kinds_seen.append,
    )

    screen._on_save_confirmed("forest")

    assert kinds_seen == [MazeKind.SAVED_RANDOM]


def test_on_kind_changed_defaults_to_none_and_a_save_still_succeeds(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _generated_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    screen._on_save_confirmed("forest")  # must not raise with no callback given

    assert screen._maze.kind == MazeKind.SAVED_RANDOM


def test_confirming_save_does_not_rebuild_the_hud_or_canvas(
    tk_root, fake_maze_repository, fake_settings_repository
):
    # Story 2.4's own addition: saving only rebuilds the save-zone, not the
    # whole screen -- the HUD chips and maze canvas built in `__init__`
    # must be the exact same widget instances afterward.
    screen = GameplayScreen(
        tk_root,
        _generated_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    canvas_before = screen._maze_canvas
    time_chip_before = screen._time_chip

    screen._on_save_confirmed("forest")

    assert screen._maze_canvas is canvas_before
    assert screen._time_chip is time_chip_before


def test_confirming_an_overwrite_through_the_full_dialog_flow_saves_once(
    tk_root, fake_maze_repository, fake_settings_repository
):
    existing = dataclasses.replace(_generated_maze(), kind=MazeKind.SAVED_RANDOM)
    fake_maze_repository.save(existing, "forest")
    screen = GameplayScreen(
        tk_root,
        _generated_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    screen._on_save_clicked()
    dialog = next(c for c in screen.winfo_children() if isinstance(c, SaveMazeDialog))
    dialog._name_entry.delete(0, "end")
    dialog._name_entry.insert(0, "forest")

    dialog._on_save_clicked()  # first click: arms, warns, does not save
    assert fake_maze_repository.list_names(MazeKind.SAVED_RANDOM) == ["forest"]
    dialog._on_save_clicked()  # second click: confirms the overwrite

    assert fake_maze_repository.list_names(MazeKind.SAVED_RANDOM) == ["forest"]
    saved = fake_maze_repository.load("forest", MazeKind.SAVED_RANDOM)
    assert saved.kind == MazeKind.SAVED_RANDOM
    assert screen._maze.kind == MazeKind.SAVED_RANDOM
    assert not hasattr(screen, "_save_button")


def test_repository_is_untouched_until_save_is_actually_confirmed(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _generated_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._on_save_clicked()

    assert fake_maze_repository.list_names(MazeKind.SAVED_RANDOM) == []


def test_save_shortcut_is_registered_while_the_save_button_exists(
    tk_root, fake_maze_repository, fake_settings_repository
):
    GameplayScreen(
        tk_root,
        _generated_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    save_kb = keybinding("save_maze")

    assert tk_root.bind_all(save_kb.event) != ""


def test_save_shortcut_unregisters_once_the_maze_is_saved_and_the_button_rebuilt(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _generated_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    save_kb = keybinding("save_maze")
    assert tk_root.bind_all(save_kb.event) != ""

    screen._on_save_confirmed("forest")
    tk_root.update()

    assert tk_root.bind_all(save_kb.event) == ""


# -- level & visibility (Story 2.6) ------------------------------------


def test_level_chip_and_sidebar_label_show_the_initial_level_one(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    assert screen._session.level is Level.ONE
    assert screen._level_chip._value_label.cget("text") == "1"
    assert screen._level_value_label.cget("text") == "1"


def test_cycling_the_level_updates_the_chip_and_sidebar_label_and_wraps(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    screen._cycle_level(1)  # ONE -> TWO
    assert screen._session.level is Level.TWO
    assert screen._level_chip._value_label.cget("text") == "2"
    assert screen._level_value_label.cget("text") == "2"

    screen._cycle_level(1)  # TWO -> THREE
    assert screen._session.level is Level.THREE
    assert screen._level_chip._value_label.cget("text") == "3"

    screen._cycle_level(1)  # THREE -> FOUR
    assert screen._session.level is Level.FOUR
    assert screen._level_chip._value_label.cget("text") == "4"

    screen._cycle_level(1)  # FOUR -> MAX
    assert screen._session.level is Level.MAX
    assert screen._level_chip._value_label.cget("text") == "Max"
    assert screen._level_value_label.cget("text") == "Max"

    screen._cycle_level(1)  # MAX -> ONE (wrapped)
    assert screen._session.level is Level.ONE
    assert screen._level_chip._value_label.cget("text") == "1"


def test_minus_cycling_wraps_from_one_to_max(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    screen._cycle_level(-1)

    assert screen._session.level is Level.MAX
    assert screen._level_chip._value_label.cget("text") == "Max"


def test_level_change_redraws_the_structure_without_restarting_the_run(
    tk_root, fake_maze_repository, fake_settings_repository
):
    _use_discrete(fake_settings_repository)
    maze = _corridor_maze()
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._on_move(Direction.RIGHT)
    _settle(screen)
    assert screen._session.position == Position(row=0, col=1)
    walls_at_level_one = len(screen._maze_canvas.find_withtag("wall"))
    assert len(screen._maze_canvas.find_withtag("contour")) == 0

    screen._cycle_level(1)  # ONE -> TWO

    assert screen._session.level is Level.TWO
    assert screen._session.position == Position(row=0, col=1)
    assert screen._session.solved is False
    assert len(screen._maze_canvas.find_withtag("wall")) < walls_at_level_one
    assert len(screen._maze_canvas.find_withtag("contour")) > 0


def test_level_four_blocked_at_rest_redraws_the_discovered_wall(
    tk_root, fake_maze_repository, fake_settings_repository
):
    _use_discrete(fake_settings_repository)
    maze = _corridor_maze()
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._cycle_level(3)  # ONE -> FOUR
    assert screen._session.level is Level.FOUR
    assert len(screen._maze_canvas.find_withtag("wall")) == 0

    screen._on_move(Direction.RIGHT)
    _settle(screen)
    assert screen._session.position == Position(row=0, col=1)

    screen._on_move(Direction.DOWN)  # blocked at rest: reveals Wall(1, 1, top)

    assert screen._session.visibility.discovered_walls == frozenset(
        {Wall(row=1, col=1, side="top")}
    )
    assert len(screen._maze_canvas.find_withtag("wall")) == 1


def test_level_two_partition_advance_redraws_the_structure(
    tk_root, fake_maze_repository, fake_settings_repository
):
    _use_discrete(fake_settings_repository)
    maze = _corridor_maze(width=5)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._cycle_level(1)  # ONE -> TWO
    walls_at_partition_zero = len(screen._maze_canvas.find_withtag("wall"))

    screen._on_move(Direction.RIGHT)  # (0, 0) -> (0, 1), still partition 0
    _settle(screen)
    assert screen._rendered_visibility is screen._session.visibility
    assert len(screen._maze_canvas.find_withtag("wall")) == walls_at_partition_zero

    screen._on_move(Direction.RIGHT)  # (0, 1) -> (0, 2), partition 1 entered
    _settle(screen)
    assert screen._session.visibility.visited == frozenset({0, 1})
    assert len(screen._maze_canvas.find_withtag("wall")) > walls_at_partition_zero


def test_level_two_threshold_reset_hides_all_partitions_but_the_current(
    tk_root, fake_maze_repository, fake_settings_repository
):
    _use_discrete(fake_settings_repository)
    # 6x2 corridor: 3 partitions (2x2), threshold = round(3/2) = 2, so the
    # third partition entered resets the visited set down to itself.
    maze = _corridor_maze(width=6)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._cycle_level(1)  # ONE -> TWO
    assert screen._session.visibility.visited == frozenset({0})

    screen._on_move(Direction.RIGHT)  # -> (0, 1), partition 0
    _settle(screen)
    screen._on_move(Direction.RIGHT)  # -> (0, 2), partition 1 entered
    _settle(screen)
    assert screen._session.visibility.visited == frozenset({0, 1})

    walls_before_reset = len(screen._maze_canvas.find_withtag("wall"))
    screen._on_move(Direction.RIGHT)  # -> (0, 3), partition 1
    _settle(screen)
    assert screen._session.visibility.visited == frozenset({0, 1})

    screen._on_move(Direction.RIGHT)  # -> (0, 4), partition 2 entered: reset
    _settle(screen)

    assert screen._session.visibility.visited == frozenset({2})
    assert len(screen._maze_canvas.find_withtag("wall")) < walls_before_reset


def test_level_three_redraws_only_the_current_partition(
    tk_root, fake_maze_repository, fake_settings_repository
):
    _use_discrete(fake_settings_repository)
    maze = _corridor_maze(width=5)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._cycle_level(2)  # ONE -> THREE

    screen._on_move(Direction.RIGHT)  # -> (0, 1), partition 0
    _settle(screen)

    screen._on_move(Direction.RIGHT)  # -> (0, 2), partition 1: only it shown
    _settle(screen)

    assert screen._session.visibility.current_partition == 1
    assert screen._session.visibility.visited == frozenset({1})
    assert len(screen._maze_canvas.find_withtag("wall")) == len(
        visible_walls(screen._session.visibility, maze.grid)
    )


def test_level_four_smooth_boundary_stop_redraws_the_discovered_wall(
    tk_root, fake_maze_repository, fake_settings_repository
):
    maze = _stopping_maze()
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._cycle_level(3)  # ONE -> FOUR
    assert screen._session.mode is MovementMode.SMOOTH

    screen._on_move(Direction.RIGHT)  # smooth leg (0,0) -> stops at (0,1)
    _settle(screen)

    assert screen._session.position == Position(row=0, col=1)
    assert screen._session.moving_direction is None
    assert screen._session.visibility.discovered_walls == frozenset(
        {Wall(row=0, col=2, side="left")}
    )
    assert len(screen._maze_canvas.find_withtag("wall")) == 1


def test_level_change_is_a_no_op_after_solve(
    tk_root, fake_maze_repository, fake_settings_repository
):
    maze = _open_maze(width=2)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._on_move(Direction.RIGHT)
    _settle(screen)
    assert screen._session.solved is True

    screen._cycle_level(1)

    assert screen._session.level is Level.ONE
    assert screen._session.solved is True
    assert screen._level_chip._value_label.cget("text") == "1"


def test_level_change_is_a_no_op_while_focus_is_in_another_toplevel(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    other = tk.Toplevel(tk_root)
    other_entry = tk.Entry(other)
    screen.focus_get = lambda: other_entry

    screen._cycle_level(1)

    assert screen._session.level is Level.ONE
    assert screen._level_chip._value_label.cget("text") == "1"
    other.destroy()


# -- difficulty (Story 2.7) --------------------------------------------


def test_difficulty_group_renders_disabled_at_level_one(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    assert screen._session.difficulty is Difficulty.ONE
    assert screen._difficulty_chip._value_label.cget("text") == "1"
    assert screen._difficulty_value_label.cget("text") == "1"
    assert screen._difficulty_minus_button._enabled is False
    assert screen._difficulty_plus_button._enabled is False


def test_cycling_difficulty_updates_session_chip_and_sidebar_and_wraps_both_directions(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._cycle_level(1)  # ONE -> TWO, unlocking the Difficulty control

    screen._cycle_difficulty(1)  # ONE -> TWO
    assert screen._session.difficulty is Difficulty.TWO
    assert screen._difficulty_chip._value_label.cget("text") == "2"
    assert screen._difficulty_value_label.cget("text") == "2"

    screen._cycle_difficulty(1)  # TWO -> THREE
    assert screen._session.difficulty is Difficulty.THREE
    assert screen._difficulty_chip._value_label.cget("text") == "3"

    screen._cycle_difficulty(1)  # THREE -> ONE (wrapped forward)
    assert screen._session.difficulty is Difficulty.ONE
    assert screen._difficulty_chip._value_label.cget("text") == "1"

    screen._cycle_difficulty(-1)  # ONE -> THREE (wrapped backward)
    assert screen._session.difficulty is Difficulty.THREE
    assert screen._difficulty_chip._value_label.cget("text") == "3"


def test_difficulty_change_redraws_the_structure_without_restarting_the_run(
    tk_root, fake_maze_repository, fake_settings_repository
):
    _use_discrete(fake_settings_repository)
    maze = _classic_maze(width=8, height=6)  # D1 -> 3x3 partitions, D2 -> 2x2
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._cycle_level(1)  # ONE -> TWO
    walls_at_d1 = len(screen._maze_canvas.find_withtag("wall"))
    assert walls_at_d1 > 0
    elapsed_before = screen._session.elapsed
    speed_before = screen._session.speed
    mode_before = screen._session.mode

    screen._cycle_difficulty(1)  # ONE -> TWO: 3x3 -> 2x2 partitions

    assert screen._session.difficulty is Difficulty.TWO
    assert screen._session.position == maze.entry
    assert screen._session.solved is False
    assert screen._session.level is Level.TWO
    assert screen._session.elapsed == elapsed_before
    assert screen._session.mode is mode_before
    assert screen._session.speed is speed_before
    assert screen._rendered_visibility is screen._session.visibility
    assert len(screen._maze_canvas.find_withtag("wall")) != walls_at_d1


def test_difficulty_controls_disable_at_level_max_and_at_level_one(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    colors = colors_for(Theme.LIGHT)
    assert screen._difficulty_plus_button._enabled is False
    assert screen._difficulty_value_label.cget("foreground") == colors.ghost

    screen._cycle_level(1)  # ONE -> TWO
    assert screen._difficulty_plus_button._enabled is True
    assert screen._difficulty_minus_button._enabled is True
    assert screen._difficulty_value_label.cget("foreground") == colors.ink

    screen._cycle_level(1)  # TWO -> THREE
    assert screen._difficulty_plus_button._enabled is True

    screen._cycle_level(1)  # THREE -> FOUR
    assert screen._difficulty_plus_button._enabled is True

    screen._cycle_level(1)  # FOUR -> MAX
    assert screen._difficulty_plus_button._enabled is False
    assert screen._difficulty_value_label.cget("foreground") == colors.ghost
    assert screen._difficulty_chip._value_label.cget("text") == "1"

    screen._cycle_level(1)  # MAX -> ONE (wrapped)
    assert screen._difficulty_plus_button._enabled is False


def test_difficulty_cycle_is_a_no_op_while_the_control_is_disabled(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    assert screen._session.level is Level.ONE

    screen._cycle_difficulty(1)

    assert screen._session.difficulty is Difficulty.ONE
    assert screen._difficulty_chip._value_label.cget("text") == "1"


def test_difficulty_change_is_a_no_op_once_solved(
    tk_root, fake_maze_repository, fake_settings_repository
):
    maze = _open_maze(width=2)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._cycle_level(1)  # ONE -> TWO, so the Difficulty control is enabled
    screen._on_move(Direction.RIGHT)
    _settle(screen)
    assert screen._session.solved is True

    screen._cycle_difficulty(1)

    assert screen._session.solved is True
    assert screen._session.difficulty is Difficulty.ONE


def test_difficulty_cycle_is_a_no_op_while_focus_is_in_another_toplevel(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._cycle_level(1)  # unlock: ONE -> TWO
    other = tk.Toplevel(tk_root)
    other_entry = tk.Entry(other)
    screen.focus_get = lambda: other_entry

    screen._cycle_difficulty(1)

    assert screen._session.difficulty is Difficulty.ONE
    other.destroy()


def test_difficulty_change_preserves_position_and_level_and_run_state(
    tk_root, fake_maze_repository, fake_settings_repository
):
    _use_discrete(fake_settings_repository)
    maze = _corridor_maze(width=5)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._cycle_level(1)  # ONE -> TWO
    screen._on_move(Direction.RIGHT)
    _settle(screen)
    assert screen._session.position == Position(row=0, col=1)
    assert screen._session.mode is MovementMode.DISCRETE

    screen._cycle_difficulty(1)

    assert screen._session.position == Position(row=0, col=1)
    assert screen._session.level is Level.TWO
    assert screen._session.solved is False
    assert screen._session.mode is MovementMode.DISCRETE
    assert screen._session.visibility.difficulty is Difficulty.TWO


# -- HARD mode (Story 2.8) --------------------------------------------


def test_hard_mode_starts_disabled_with_the_light_hidden(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    assert screen._session.hard_mode is False
    assert screen._mode_hard_button.active is False
    assert screen._status_light_frame.winfo_manager() == ""
    assert screen._maze_canvas.itemcget("fog", "state") == "hidden"


def test_toggling_hard_mode_on_activates_the_button_and_shows_the_ready_light(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    colors = colors_for(Theme.LIGHT)

    screen._toggle_hard_mode()

    assert screen._session.hard_mode is True
    assert screen._mode_hard_button.active is True
    assert screen._status_light_frame.winfo_manager() == "pack"
    ready_color = read_hard_mode_ready_color(fake_settings_repository, colors.accent)
    assert screen._status_light_canvas.itemcget(screen._status_light, "fill") == ready_color
    assert screen._status_label.cget("text") == "Ready"
    assert screen._maze_canvas.itemcget("fog", "state") == "hidden"


def test_hard_mode_moving_hides_the_ball_shows_the_fog_and_marks_the_light_moving(
    tk_root, fake_maze_repository, fake_settings_repository
):
    maze = _open_maze(width=3)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._toggle_hard_mode()
    colors = colors_for(Theme.LIGHT)
    ball = screen._maze_canvas.find_withtag("ball")[0]

    screen._on_move(Direction.RIGHT)  # mid-leg, no `_settle`

    assert screen._session.moving_direction is not None
    assert screen._maze_canvas.itemcget(ball, "state") == "hidden"
    assert screen._maze_canvas.itemcget("fog", "state") == "normal"
    moving_color = read_hard_mode_moving_color(fake_settings_repository, colors.exit)
    assert screen._status_light_canvas.itemcget(screen._status_light, "fill") == moving_color
    assert screen._status_label.cget("text") == "Moving"


def test_hard_mode_rest_restores_the_ball_and_switches_the_light_back_to_ready(
    tk_root, fake_maze_repository, fake_settings_repository
):
    maze = _open_maze(width=3)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._toggle_hard_mode()
    screen._on_move(Direction.RIGHT)
    assert screen._status_label.cget("text") == "Moving"

    _settle(screen)

    assert screen._session.moving_direction is None
    ball = screen._maze_canvas.find_withtag("ball")[0]
    assert screen._maze_canvas.itemcget(ball, "state") == "normal"
    assert screen._maze_canvas.itemcget("fog", "state") == "hidden"
    colors = colors_for(Theme.LIGHT)
    ready_color = read_hard_mode_ready_color(fake_settings_repository, colors.accent)
    assert screen._status_light_canvas.itemcget(screen._status_light, "fill") == ready_color
    assert screen._status_label.cget("text") == "Ready"


def test_deactivating_hard_mode_mid_leg_shows_the_ball_on_the_next_tick(
    tk_root, fake_maze_repository, fake_settings_repository
):
    maze = _open_maze(width=3)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._toggle_hard_mode()
    screen._on_move(Direction.RIGHT)
    ball = screen._maze_canvas.find_withtag("ball")[0]
    assert screen._maze_canvas.itemcget(ball, "state") == "hidden"

    screen._toggle_hard_mode()

    assert screen._session.hard_mode is False
    assert screen._mode_hard_button.active is False
    assert screen._status_light_frame.winfo_manager() == ""
    assert screen._maze_canvas.itemcget(ball, "state") == "normal"
    assert screen._maze_canvas.itemcget("fog", "state") == "hidden"


def test_changing_the_hard_mode_colors_recolors_both_states_from_the_new_values(
    tk_root, fake_maze_repository, fake_settings_repository
):
    # AC-4: both states always read the same current setting, so a color
    # change can't break the ready<->moving toggle -- no literal anywhere.
    write_hard_mode_ready_color(fake_settings_repository, "#111111")
    write_hard_mode_moving_color(fake_settings_repository, "#222222")
    maze = _open_maze(width=3)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    screen._toggle_hard_mode()

    assert screen._status_light_canvas.itemcget(screen._status_light, "fill") == "#111111"

    screen._on_move(Direction.RIGHT)

    assert screen._status_light_canvas.itemcget(screen._status_light, "fill") == "#222222"

    _settle(screen)

    assert screen._status_light_canvas.itemcget(screen._status_light, "fill") == "#111111"
    assert screen._status_label.cget("text") == "Ready"


def test_a_color_change_mid_session_is_picked_up_on_the_next_activation(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    colors = colors_for(Theme.LIGHT)
    screen._toggle_hard_mode()
    assert screen._status_light_canvas.itemcget(screen._status_light, "fill") == colors.accent

    write_hard_mode_ready_color(fake_settings_repository, "#111111")
    write_hard_mode_moving_color(fake_settings_repository, "#222222")
    screen._toggle_hard_mode()  # off
    screen._toggle_hard_mode()  # on again: `_hard_mode_colors()` re-reads both

    assert screen._status_light_canvas.itemcget(screen._status_light, "fill") == "#111111"


def test_hard_mode_toggle_is_a_no_op_while_focus_is_in_another_toplevel(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    other = tk.Toplevel(tk_root)
    other_entry = tk.Entry(other)
    screen.focus_get = lambda: other_entry

    screen._toggle_hard_mode()

    assert screen._session.hard_mode is False
    assert screen._status_light_frame.winfo_manager() == ""
    other.destroy()


def test_hard_mode_toggle_is_a_no_op_once_solved(
    tk_root, fake_maze_repository, fake_settings_repository
):
    maze = _open_maze(width=2)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._on_move(Direction.RIGHT)
    _settle(screen)
    assert screen._session.solved is True

    screen._toggle_hard_mode()

    # `session_set_hard_mode` is a no-op once solved (Story 2.5/2.6/2.7
    # convention), and `_sync_hard_mode_visuals` reads the unchanged session,
    # so HARD stays off, the light stays hidden, and the button mirrors the
    # session (stays inactive -- unlike `_toggle_mode`, which is also a no-op
    # but derives its button from the session too).
    assert screen._session.hard_mode is False
    assert screen._mode_hard_button.active is False
    assert screen._status_light_frame.winfo_manager() == ""


def test_hard_mode_solve_keeps_the_ball_visible_at_rest(
    tk_root, fake_maze_repository, fake_settings_repository
):
    maze = _open_maze(width=2)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._toggle_hard_mode()

    screen._on_move(Direction.RIGHT)
    _settle(screen)

    assert screen._session.solved is True
    ball = screen._maze_canvas.find_withtag("ball")[0]
    assert screen._maze_canvas.itemcget(ball, "state") == "normal"
    assert screen._maze_canvas.itemcget("fog", "state") == "hidden"
    assert screen._status_label.cget("text") == "Ready"


def test_hard_mode_shortcut_h_is_registered(
    tk_root, fake_maze_repository, fake_settings_repository
):
    GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    kb = keybinding("toggle_hard_mode")

    assert tk_root.bind_all(kb.event) != ""


def test_hard_mode_shortcut_h_invokes_the_toggle(
    tk_root, fake_maze_repository, fake_settings_repository
):
    # The `h` shortcut's wrapped handler (returned by `bind_shortcut`, which
    # cannot synthesize a real key on a withdrawn `tk_root`) must flip HARD
    # on exactly like clicking the button.
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    screen._hard_mode_handler()

    assert screen._session.hard_mode is True
    assert screen._mode_hard_button.active is True


def test_enabling_hard_mode_mid_leg_hides_the_ball_and_shows_the_fog_immediately(
    tk_root, fake_maze_repository, fake_settings_repository
):
    # Regression: a HARD toggle fired while a leg is in flight must apply the
    # moving-state visuals right away (the in-flight ball disappears and the
    # fog shows), not wait for the next `_on_animation_tick` -- the
    # `moving-state predicate includes hard_mode` edge-case (spec matrix).
    maze = _open_maze(width=3)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._on_move(Direction.RIGHT)
    assert screen._session.moving_direction is not None
    ball = screen._maze_canvas.find_withtag("ball")[0]
    assert screen._maze_canvas.itemcget(ball, "state") == "normal"

    screen._toggle_hard_mode()

    assert screen._session.hard_mode is True
    assert screen._maze_canvas.itemcget(ball, "state") == "hidden"
    assert screen._maze_canvas.itemcget("fog", "state") == "normal"
    assert screen._status_label.cget("text") == "Moving"


# -- time limit / timeout (Story 2.9) ----------------------------------


def test_mount_reads_the_time_limit_from_settings(
    tk_root, fake_maze_repository, fake_settings_repository
):
    write_time_limit(fake_settings_repository, Duration(milliseconds=90000))
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    assert screen._time_limit == Duration(milliseconds=90000)


def test_mount_with_no_limit_stored_reads_none(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    assert screen._time_limit is None


def test_mount_reads_none_for_a_corrupt_stored_limit(
    tk_root, fake_maze_repository, fake_settings_repository
):
    fake_settings_repository.set(SettingsScope.GAME, TIME_LIMIT_SECONDS, "garbage")
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    assert screen._time_limit is None


def test_on_tick_times_out_the_run_at_the_limit(
    tk_root, fake_maze_repository, fake_settings_repository
):
    write_time_limit(fake_settings_repository, Duration(milliseconds=5000))
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._start_time = time.monotonic() - 5.0

    screen._on_tick()

    assert screen._session.timed_out is True
    assert screen._tick_job is None
    assert screen._timeout_banner is not None
    labels = [
        child.cget("text")
        for child in screen._timeout_banner.winfo_children()
        if isinstance(child, tk.Label)
    ]
    assert any(text == "Time's up — the exit wasn't reached." for text in labels)
    assert screen._time_chip._value_label.cget("text") == "00:05"


def test_timeout_fires_at_exactly_the_limit_boundary(
    tk_root, fake_maze_repository, fake_settings_repository
):
    # The `>=` comparison: `elapsed_ms == limit.milliseconds` must already
    # time out, not a second late (spec I/O matrix "Timeout granularity").
    write_time_limit(fake_settings_repository, Duration(milliseconds=1000))
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._start_time = time.monotonic() - 1.0

    screen._on_tick()

    assert screen._session.timed_out is True
    assert screen._tick_job is None
    assert screen._timeout_banner is not None


def test_on_tick_with_no_limit_keeps_rescheduling_forever(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._start_time = time.monotonic() - 5.0

    screen._on_tick()

    assert screen._session.timed_out is False
    assert screen._tick_job is not None
    assert screen._timeout_banner is None


def test_timeout_cancels_an_in_flight_animation_job(
    tk_root, fake_maze_repository, fake_settings_repository
):
    write_time_limit(fake_settings_repository, Duration(milliseconds=5000))
    maze = _open_maze(width=3)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._on_move(Direction.RIGHT)  # starts a leg without settling
    screen._on_animation_tick()
    screen._on_animation_tick()  # ball mid-cell at step 2/5
    assert screen._session.moving_direction is not None
    ball = screen._maze_canvas.find_withtag("ball")[0]
    frozen_coords = screen._maze_canvas.coords(ball)
    screen._start_time = time.monotonic() - 5.0

    screen._on_tick()

    assert screen._session.timed_out is True
    assert screen._animation_job is None
    assert screen._tick_job is None
    assert screen._maze_canvas.coords(ball) == frozen_coords


def test_movement_after_timeout_is_a_no_op_at_the_screen_level(
    tk_root, fake_maze_repository, fake_settings_repository
):
    maze = _open_maze(width=3)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._time_limit = Duration(milliseconds=5000)
    screen._start_time = time.monotonic() - 5.0
    screen._on_tick()
    assert screen._session.timed_out is True

    screen._on_move(Direction.RIGHT)

    assert screen._session.moving_direction is None
    assert screen._animation_job is None


def test_solve_wins_the_race_against_a_timeout(
    tk_root, fake_maze_repository, fake_settings_repository
):
    write_time_limit(fake_settings_repository, Duration(milliseconds=5000))
    maze = _open_maze(width=2)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._on_move(Direction.RIGHT)
    _settle(screen)
    assert screen._session.solved is True
    screen._start_time = time.monotonic() - 5.0

    screen._on_tick()

    assert screen._session.timed_out is False
    assert screen._timeout_banner is None
    assert screen._win_banner is not None


def test_restart_from_the_timeout_banner_starts_a_fresh_run(
    tk_root, fake_maze_repository, fake_settings_repository
):
    write_time_limit(fake_settings_repository, Duration(milliseconds=5000))
    write_confirm_restart(fake_settings_repository, False)
    maze = _open_maze(width=3)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._start_time = time.monotonic() - 5.0
    screen._on_tick()
    assert screen._session.timed_out is True
    banner = screen._timeout_banner

    screen._restart_run()

    assert screen._session.timed_out is False
    assert screen._session.solved is False
    assert screen._session.position == maze.entry
    assert screen._session.elapsed == Duration(milliseconds=0)
    assert screen._time_chip._value_label.cget("text") == "00:00"
    assert screen._timeout_banner is None
    assert not banner.winfo_exists()
    assert screen._tick_job is not None
    screen._on_move(Direction.RIGHT)
    assert screen._session.moving_direction is not None


def test_restart_reads_a_fresh_time_limit(tk_root, fake_maze_repository, fake_settings_repository):
    write_time_limit(fake_settings_repository, Duration(milliseconds=5000))
    write_confirm_restart(fake_settings_repository, False)
    maze = _open_maze(width=3)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._start_time = time.monotonic() - 5.0
    screen._on_tick()
    assert screen._session.timed_out is True
    write_time_limit(fake_settings_repository, Duration(milliseconds=30000))

    screen._restart_run()

    assert screen._time_limit == Duration(milliseconds=30000)


def test_restart_resets_level_difficulty_chips_and_reapplies_persisted_mode_speed(
    tk_root, fake_maze_repository, fake_settings_repository
):
    _use_discrete(fake_settings_repository)
    write_confirm_restart(fake_settings_repository, False)
    write_time_limit(fake_settings_repository, Duration(milliseconds=5000))
    screen = GameplayScreen(
        tk_root,
        _corridor_maze(width=4),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._cycle_level(1)  # ONE -> TWO, unlocking the Difficulty control
    screen._cycle_difficulty(1)  # ONE -> TWO
    screen._cycle_speed()  # NORMAL -> FAST, persisted
    speed_before_timeout = screen._session.speed
    assert screen._session.level is Level.TWO
    assert screen._session.difficulty is Difficulty.TWO
    screen._start_time = time.monotonic() - 5.0
    screen._on_tick()
    assert screen._session.timed_out is True

    screen._restart_run()

    assert screen._session.level is Level.ONE
    assert screen._session.difficulty is Difficulty.ONE
    assert screen._session.mode is MovementMode.DISCRETE  # persisted mode re-applied
    assert screen._session.speed is speed_before_timeout  # persisted speed re-applied
    assert screen._level_chip._value_label.cget("text") == "1"
    assert screen._level_value_label.cget("text") == "1"
    assert screen._difficulty_chip._value_label.cget("text") == "1"
    assert screen._mode_button.active is False  # mirrors the re-applied DISCRETE mode


def test_restart_with_a_solved_win_banner_destroys_it_and_resets_the_run(
    tk_root, fake_maze_repository, fake_settings_repository
):
    write_confirm_restart(fake_settings_repository, False)
    maze = _open_maze(width=2)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._on_move(Direction.RIGHT)
    _settle(screen)
    assert screen._session.solved is True
    banner = screen._win_banner

    screen._restart_run()

    assert screen._win_banner is None
    assert not banner.winfo_exists()
    assert screen._session.solved is False
    assert screen._session.timed_out is False
    assert screen._session.position == maze.entry


def test_continue_from_the_timeout_banner_keeps_the_run_stopped(
    tk_root, fake_maze_repository, fake_settings_repository
):
    write_time_limit(fake_settings_repository, Duration(milliseconds=5000))
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._start_time = time.monotonic() - 5.0
    screen._on_tick()
    assert screen._session.timed_out is True
    banner = screen._timeout_banner

    screen._on_timeout_continue_clicked()

    assert screen._timeout_banner is None
    assert not banner.winfo_exists()
    assert screen._session.timed_out is True
    assert screen._tick_job is None


def test_continue_from_the_timeout_banner_keeps_a_mid_leg_frozen(
    tk_root, fake_maze_repository, fake_settings_repository
):
    write_time_limit(fake_settings_repository, Duration(milliseconds=5000))
    maze = _open_maze(width=3)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._on_move(Direction.RIGHT)
    screen._on_animation_tick()  # ball mid-cell
    ball = screen._maze_canvas.find_withtag("ball")[0]
    frozen_coords = screen._maze_canvas.coords(ball)
    screen._start_time = time.monotonic() - 5.0
    screen._on_tick()
    assert screen._session.timed_out is True

    screen._on_timeout_continue_clicked()

    assert screen._timeout_banner is None
    assert screen._session.timed_out is True
    assert screen._session.moving_direction is not None
    assert screen._maze_canvas.coords(ball) == frozen_coords


def test_timeout_banner_pills_are_not_primary_with_a_generated_maze(
    tk_root, fake_maze_repository, fake_settings_repository
):
    # Regression (mirrors `test_continue_button_is_not_a_primary_pill`): a
    # `GENERATED` maze's Save pill can still be showing below the banner, so
    # neither Restart nor Continue may be `primary=True` -- at most one
    # primary pill per screen.
    write_time_limit(fake_settings_repository, Duration(milliseconds=5000))
    screen = GameplayScreen(
        tk_root,
        dataclasses.replace(_open_maze(width=3), kind=MazeKind.GENERATED),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._start_time = time.monotonic() - 5.0
    screen._on_tick()
    assert screen._timeout_banner is not None

    pills = [c for c in screen._timeout_banner.winfo_children() if isinstance(c, PillButton)]
    assert len(pills) == 2
    assert all(pill._primary is False for pill in pills)


def test_timeout_banner_mirrors_the_win_banner_styling_and_placement(
    tk_root, fake_maze_repository, fake_settings_repository
):
    write_time_limit(fake_settings_repository, Duration(milliseconds=5000))
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._start_time = time.monotonic() - 5.0
    screen._on_tick()
    assert screen._timeout_banner is not None

    colors = colors_for(Theme.LIGHT)
    assert screen._timeout_banner.cget("background") == colors.accent_bg
    assert screen._timeout_banner.cget("highlightthickness") == 1
    assert screen._timeout_banner.cget("highlightbackground") == colors.accent
    assert screen._timeout_banner.cget("highlightcolor") == colors.accent
    assert screen._timeout_banner.pack_info()["fill"] == "x"
    pack_order = screen.pack_slaves()
    assert pack_order.index(screen._timeout_banner) < pack_order.index(screen._maze_frame)


def test_restart_resets_the_hard_mode_visual_state(
    tk_root, fake_maze_repository, fake_settings_repository
):
    write_time_limit(fake_settings_repository, Duration(milliseconds=5000))
    write_confirm_restart(fake_settings_repository, False)
    maze = _open_maze(width=3)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._toggle_hard_mode()
    screen._on_move(Direction.RIGHT)
    assert screen._maze_canvas.itemcget("fog", "state") == "normal"
    screen._start_time = time.monotonic() - 5.0
    screen._on_tick()
    assert screen._session.timed_out is True

    screen._restart_run()

    assert screen._session.hard_mode is False
    assert screen._session.timed_out is False
    assert screen._maze_canvas.itemcget("fog", "state") == "hidden"
    ball = screen._maze_canvas.find_withtag("ball")[0]
    assert screen._maze_canvas.itemcget(ball, "state") == "normal"
    assert screen._status_light_frame.winfo_manager() == ""
    assert screen._mode_hard_button.active is False


# -- Story 2.10: gated level change and restart -----------------------------------------


def test_level_change_opens_a_confirm_dialog_when_confirm_level_change_is_on(
    tk_root, fake_maze_repository, fake_settings_repository
):
    write_confirm_level_change(fake_settings_repository, True)
    screen = GameplayScreen(
        tk_root,
        _corridor_maze(width=4),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    screen._cycle_level(1)

    assert screen._confirm_dialog is not None
    assert screen._session.level is Level.ONE
    screen._confirm_dialog._on_confirm_clicked()
    assert screen._session.level is Level.TWO
    assert screen._confirm_dialog is None


def test_level_change_is_immediate_when_confirm_level_change_is_off(
    tk_root, fake_maze_repository, fake_settings_repository
):
    write_confirm_level_change(fake_settings_repository, False)
    screen = GameplayScreen(
        tk_root,
        _corridor_maze(width=4),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    screen._cycle_level(1)

    assert screen._confirm_dialog is None
    assert screen._session.level is Level.TWO


def test_cancelling_the_level_change_dialog_leaves_the_level_untouched(
    tk_root, fake_maze_repository, fake_settings_repository
):
    write_confirm_level_change(fake_settings_repository, True)
    screen = GameplayScreen(
        tk_root,
        _corridor_maze(width=4),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    screen._cycle_level(1)
    screen._confirm_dialog._on_cancel_clicked()

    assert screen._session.level is Level.ONE
    assert screen._confirm_dialog is None


def test_restart_opens_a_confirm_dialog_when_confirm_restart_is_on(
    tk_root, fake_maze_repository, fake_settings_repository
):
    write_confirm_restart(fake_settings_repository, True)
    maze = _open_maze(width=3)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._on_move(Direction.RIGHT)
    _settle(screen)
    assert screen._session.solved is True

    screen._restart_run()

    assert screen._confirm_dialog is not None
    assert screen._session.solved is True
    screen._confirm_dialog._on_confirm_clicked()
    assert screen._session.solved is False
    assert screen._session.position == maze.entry
    assert screen._confirm_dialog is None


def test_a_second_gated_trigger_while_a_dialog_is_open_is_a_no_op(
    tk_root, fake_maze_repository, fake_settings_repository
):
    write_confirm_level_change(fake_settings_repository, True)
    screen = GameplayScreen(
        tk_root,
        _corridor_maze(width=4),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._cycle_level(1)
    first = screen._confirm_dialog

    screen._cycle_level(1)

    assert screen._confirm_dialog is first
    first.destroy()
    screen._confirm_dialog = None
