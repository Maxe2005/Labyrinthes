"""GameplayScreen: initial render, movement, and elapsed-time ticking."""

import dataclasses
import time

from labyrinthes.adapters.tkinter.common.keybindings import keybinding
from labyrinthes.adapters.tkinter.common.tokens import Theme
from labyrinthes.adapters.tkinter.player.gameplay import GameplayScreen
from labyrinthes.adapters.tkinter.player.maze_canvas import MazeCanvas
from labyrinthes.adapters.tkinter.player.save_maze_dialog import SaveMazeDialog
from labyrinthes.application.settings_keys import (
    MOVEMENT_MODE,
    MOVEMENT_SPEED,
)
from labyrinthes.application.settings_repository import SettingsScope
from labyrinthes.domain.maze import MazeKind
from labyrinthes.domain.movement import Direction
from labyrinthes.domain.movement_mode import MovementMode
from labyrinthes.domain.movement_speed import MovementSpeed
from labyrinthes.domain.position import Position
from tests.adapters.tkinter.player.gameplay._helpers import (
    _classic_maze,
    _open_maze,
    _settle,
    _use_discrete,
)


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

    assert screen._hud._level_chip._value_label.cget("text") == "1"
    assert screen._hud._difficulty_chip._value_label.cget("text") == "1"
    assert screen._hud._time_chip._value_label.cget("text") == "00:00"
    assert screen._hud._pos_chip._value_label.cget("text") == "(0, 0)"


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
    assert screen._hud._pos_chip._value_label.cget("text") == "(0, 1)"
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
    assert screen._hud._pos_chip._value_label.cget("text") == "(0, 0)"
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

    assert screen._hud._time_chip._value_label.cget("text") == "00:02"
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
