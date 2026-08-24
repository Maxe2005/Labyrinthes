"""GameplayScreen: Level (Story 2.6) and Difficulty (Story 2.7) cycling,
visibility redraws, and their confirm-gating (Story 2.10)."""

import tkinter as tk

from labyrinthes.adapters.tkinter.common.tokens import Theme, colors_for
from labyrinthes.adapters.tkinter.player.gameplay import GameplayScreen
from labyrinthes.application.confirmation_settings import (
    write_confirm_level_change,
)
from labyrinthes.domain.difficulty import Difficulty
from labyrinthes.domain.level import Level
from labyrinthes.domain.level_visibility import Wall, visible_walls
from labyrinthes.domain.movement import Direction
from labyrinthes.domain.movement_mode import MovementMode
from labyrinthes.domain.position import Position
from tests.adapters.tkinter.player.gameplay._helpers import (
    _classic_maze,
    _corridor_maze,
    _open_maze,
    _settle,
    _stopping_maze,
    _use_discrete,
)


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
    assert screen._hud._level_chip._value_label.cget("text") == "1"
    assert screen._sidebar._level_value_label.cget("text") == "1"


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
    assert screen._hud._level_chip._value_label.cget("text") == "2"
    assert screen._sidebar._level_value_label.cget("text") == "2"

    screen._cycle_level(1)  # TWO -> THREE
    assert screen._session.level is Level.THREE
    assert screen._hud._level_chip._value_label.cget("text") == "3"

    screen._cycle_level(1)  # THREE -> FOUR
    assert screen._session.level is Level.FOUR
    assert screen._hud._level_chip._value_label.cget("text") == "4"

    screen._cycle_level(1)  # FOUR -> MAX
    assert screen._session.level is Level.MAX
    assert screen._hud._level_chip._value_label.cget("text") == "Max"
    assert screen._sidebar._level_value_label.cget("text") == "Max"

    screen._cycle_level(1)  # MAX -> ONE (wrapped)
    assert screen._session.level is Level.ONE
    assert screen._hud._level_chip._value_label.cget("text") == "1"


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
    assert screen._hud._level_chip._value_label.cget("text") == "Max"


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
    assert screen._hud._level_chip._value_label.cget("text") == "1"


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
    assert screen._hud._level_chip._value_label.cget("text") == "1"
    other.destroy()


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
    assert screen._hud._difficulty_chip._value_label.cget("text") == "1"
    assert screen._sidebar._difficulty_value_label.cget("text") == "1"
    assert screen._sidebar._difficulty_minus_button._enabled is False
    assert screen._sidebar._difficulty_plus_button._enabled is False


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
    assert screen._hud._difficulty_chip._value_label.cget("text") == "2"
    assert screen._sidebar._difficulty_value_label.cget("text") == "2"

    screen._cycle_difficulty(1)  # TWO -> THREE
    assert screen._session.difficulty is Difficulty.THREE
    assert screen._hud._difficulty_chip._value_label.cget("text") == "3"

    screen._cycle_difficulty(1)  # THREE -> ONE (wrapped forward)
    assert screen._session.difficulty is Difficulty.ONE
    assert screen._hud._difficulty_chip._value_label.cget("text") == "1"

    screen._cycle_difficulty(-1)  # ONE -> THREE (wrapped backward)
    assert screen._session.difficulty is Difficulty.THREE
    assert screen._hud._difficulty_chip._value_label.cget("text") == "3"


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
    assert screen._sidebar._difficulty_plus_button._enabled is False
    assert screen._sidebar._difficulty_value_label.cget("foreground") == colors.ghost

    screen._cycle_level(1)  # ONE -> TWO
    assert screen._sidebar._difficulty_plus_button._enabled is True
    assert screen._sidebar._difficulty_minus_button._enabled is True
    assert screen._sidebar._difficulty_value_label.cget("foreground") == colors.ink

    screen._cycle_level(1)  # TWO -> THREE
    assert screen._sidebar._difficulty_plus_button._enabled is True

    screen._cycle_level(1)  # THREE -> FOUR
    assert screen._sidebar._difficulty_plus_button._enabled is True

    screen._cycle_level(1)  # FOUR -> MAX
    assert screen._sidebar._difficulty_plus_button._enabled is False
    assert screen._sidebar._difficulty_value_label.cget("foreground") == colors.ghost
    assert screen._hud._difficulty_chip._value_label.cget("text") == "1"

    screen._cycle_level(1)  # MAX -> ONE (wrapped)
    assert screen._sidebar._difficulty_plus_button._enabled is False


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
    assert screen._hud._difficulty_chip._value_label.cget("text") == "1"


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
