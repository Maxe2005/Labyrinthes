"""GameplayScreen: Smooth/Discrete movement mode and ball speed (Story 2.5)."""

import dataclasses
import tkinter as tk

from labyrinthes.adapters.tkinter.common.keybindings import keybinding
from labyrinthes.adapters.tkinter.common.tokens import Theme
from labyrinthes.adapters.tkinter.player.gameplay import GameplayScreen
from labyrinthes.application.player_session import STEPS_PER_CELL
from labyrinthes.application.settings_keys import (
    MOVEMENT_MODE,
    MOVEMENT_SPEED,
)
from labyrinthes.application.settings_repository import SettingsScope
from labyrinthes.domain.maze import MazeKind
from labyrinthes.domain.movement import Direction
from labyrinthes.domain.movement_mode import MovementMode
from labyrinthes.domain.movement_speed import MovementSpeed, cell_crossing_duration
from tests.adapters.tkinter.player.gameplay._helpers import (
    _classic_maze,
    _open_maze,
    _use_discrete,
)


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
    assert screen._sidebar._mode_button.active is True

    screen._toggle_mode()

    assert screen._session.mode is MovementMode.DISCRETE
    assert screen._sidebar._mode_button.active is False
    assert fake_settings_repository.get(SettingsScope.GAME, MOVEMENT_MODE) == "discrete"

    screen._toggle_mode()

    assert screen._session.mode is MovementMode.SMOOTH
    assert screen._sidebar._mode_button.active is True
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
    assert screen._sidebar._speed_button._label.cget("text") == "Normal"

    screen._cycle_speed()

    assert screen._session.speed is MovementSpeed.FAST
    assert screen._sidebar._speed_button._label.cget("text") == "Fast"
    assert fake_settings_repository.get(SettingsScope.GAME, MOVEMENT_SPEED) == "fast"

    screen._cycle_speed()

    assert screen._session.speed is MovementSpeed.SLOW
    assert screen._sidebar._speed_button._label.cget("text") == "Slow"

    screen._cycle_speed()

    assert screen._session.speed is MovementSpeed.NORMAL
    assert screen._sidebar._speed_button._label.cget("text") == "Normal"


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
