"""GameplayScreen: the optional time limit, the timeout banner, and Restart (Stories 2.9/2.10)."""

import dataclasses
import time
import tkinter as tk

from labyrinthes.adapters.tkinter.common.pill_btn import PillButton
from labyrinthes.adapters.tkinter.common.tokens import Theme, colors_for
from labyrinthes.adapters.tkinter.player.gameplay import GameplayScreen
from labyrinthes.application.confirmation_settings import (
    write_confirm_level_change,
    write_confirm_restart,
)
from labyrinthes.application.settings_keys import (
    TIME_LIMIT_SECONDS,
)
from labyrinthes.application.settings_repository import SettingsScope
from labyrinthes.application.time_limit_settings import write_time_limit
from labyrinthes.domain.difficulty import Difficulty
from labyrinthes.domain.duration import Duration
from labyrinthes.domain.level import Level
from labyrinthes.domain.maze import MazeKind
from labyrinthes.domain.movement import Direction
from labyrinthes.domain.movement_mode import MovementMode
from tests.adapters.tkinter.player.gameplay._helpers import (
    _classic_maze,
    _corridor_maze,
    _open_maze,
    _settle,
    _use_discrete,
)


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
    assert screen._hud._time_chip._value_label.cget("text") == "00:05"


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
    assert screen._hud._time_chip._value_label.cget("text") == "00:00"
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
    assert screen._hud._level_chip._value_label.cget("text") == "1"
    assert screen._left_panel._level_value_label.cget("text") == "1"
    assert screen._hud._difficulty_chip._value_label.cget("text") == "1"
    assert screen._right_panel._mode_button.active is False  # mirrors the re-applied DISCRETE mode


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
    # Both are packed inside `self._stage.content` (Story 4.10) -- see
    # `_show_timeout_banner`'s `before=self._maze_frame` requiring a shared
    # master.
    pack_order = screen._stage.content.pack_slaves()
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
    assert screen._hud._status_light_frame.winfo_manager() == ""
    assert screen._left_panel._mode_hard_button.active is False


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
