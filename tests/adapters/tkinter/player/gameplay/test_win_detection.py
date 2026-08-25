"""GameplayScreen: reaching the exit marks the run solved and shows the win banner."""

import dataclasses
import time
import tkinter as tk
from unittest.mock import Mock

from labyrinthes.adapters.tkinter.common.pill_btn import PillButton
from labyrinthes.adapters.tkinter.common.tokens import Theme
from labyrinthes.adapters.tkinter.player.gameplay import GameplayScreen
from labyrinthes.domain.maze import MazeKind
from labyrinthes.domain.movement import Direction
from tests.adapters.tkinter.player.gameplay._helpers import (
    _open_maze,
    _settle,
)


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
    assert screen._hud._time_chip._value_label.cget("text") == "00:05"


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


def test_win_banner_continue_label_is_new_random_maze_for_generated_maze(
    tk_root, fake_maze_repository, fake_settings_repository
):
    # FR-33: the win banner's Continue button shows "New random maze" for
    # generated mazes, distinguishing it from classic/saved-random.
    # Use a solvable maze (straight corridor) but with GENERATED kind.
    maze = dataclasses.replace(_open_maze(width=2), kind=MazeKind.GENERATED)
    screen = GameplayScreen(
        tk_root,
        maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._on_move(Direction.RIGHT)
    _settle(screen)

    # Find the PillButton in the win banner
    continue_button = next(
        c for c in screen._win_banner.winfo_children() if isinstance(c, PillButton)
    )
    # PillButton stores its label text in an internal _label attribute
    assert continue_button._label.cget("text") == "New random maze"


def test_continue_on_generated_maze_navigates_to_new_generated_maze_with_same_params(
    tk_root, fake_maze_repository, fake_settings_repository
):
    # FR-33: clicking Continue on a generated maze regenerates a new random
    # maze with the same width, height, and entry position.
    # Use a solvable maze (straight corridor) but with GENERATED kind.
    original_maze = dataclasses.replace(_open_maze(width=2), kind=MazeKind.GENERATED)
    from labyrinthes.adapters.tkinter.common.navigation import ScreenId

    navigate_mock = Mock()
    screen = GameplayScreen(
        tk_root,
        original_maze,
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
        navigate=navigate_mock,
    )
    screen._on_move(Direction.RIGHT)
    _settle(screen)

    # Click Continue
    screen._on_continue_clicked()

    # Verify navigate was called with ScreenId.PLAYER and a new Maze
    assert navigate_mock.call_count == 1
    call_args = navigate_mock.call_args
    assert call_args[0][0] == ScreenId.PLAYER
    new_maze = call_args[0][1]
    assert new_maze.kind is MazeKind.GENERATED
    assert new_maze.id is None
    assert new_maze.grid.width == original_maze.grid.width
    assert new_maze.grid.height == original_maze.grid.height
    assert new_maze.entry == original_maze.entry
    # Exit will be different (farthest cell from entry), so don't assert on it
