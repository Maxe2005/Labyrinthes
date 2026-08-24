"""GameplayScreen: HARD mode -- invisible ball, fog overlay, status light (Story 2.8)."""

import tkinter as tk

from labyrinthes.adapters.tkinter.common.keybindings import keybinding
from labyrinthes.adapters.tkinter.common.tokens import Theme, colors_for
from labyrinthes.adapters.tkinter.player.gameplay import GameplayScreen
from labyrinthes.application.hard_mode_settings import (
    read_hard_mode_moving_color,
    read_hard_mode_ready_color,
    write_hard_mode_moving_color,
    write_hard_mode_ready_color,
)
from labyrinthes.domain.movement import Direction
from tests.adapters.tkinter.player.gameplay._helpers import (
    _classic_maze,
    _open_maze,
    _settle,
)


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
    assert screen._sidebar._mode_hard_button.active is False
    assert screen._hud._status_light_frame.winfo_manager() == ""
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
    assert screen._sidebar._mode_hard_button.active is True
    assert screen._hud._status_light_frame.winfo_manager() == "pack"
    ready_color = read_hard_mode_ready_color(fake_settings_repository, colors.accent)
    assert (
        screen._hud._status_light_canvas.itemcget(screen._hud._status_light, "fill") == ready_color
    )
    assert screen._hud._status_label.cget("text") == "Ready"
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
    assert (
        screen._hud._status_light_canvas.itemcget(screen._hud._status_light, "fill") == moving_color
    )
    assert screen._hud._status_label.cget("text") == "Moving"


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
    assert screen._hud._status_label.cget("text") == "Moving"

    _settle(screen)

    assert screen._session.moving_direction is None
    ball = screen._maze_canvas.find_withtag("ball")[0]
    assert screen._maze_canvas.itemcget(ball, "state") == "normal"
    assert screen._maze_canvas.itemcget("fog", "state") == "hidden"
    colors = colors_for(Theme.LIGHT)
    ready_color = read_hard_mode_ready_color(fake_settings_repository, colors.accent)
    assert (
        screen._hud._status_light_canvas.itemcget(screen._hud._status_light, "fill") == ready_color
    )
    assert screen._hud._status_label.cget("text") == "Ready"


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
    assert screen._sidebar._mode_hard_button.active is False
    assert screen._hud._status_light_frame.winfo_manager() == ""
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

    assert screen._hud._status_light_canvas.itemcget(screen._hud._status_light, "fill") == "#111111"

    screen._on_move(Direction.RIGHT)

    assert screen._hud._status_light_canvas.itemcget(screen._hud._status_light, "fill") == "#222222"

    _settle(screen)

    assert screen._hud._status_light_canvas.itemcget(screen._hud._status_light, "fill") == "#111111"
    assert screen._hud._status_label.cget("text") == "Ready"


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
    assert (
        screen._hud._status_light_canvas.itemcget(screen._hud._status_light, "fill")
        == colors.accent
    )

    write_hard_mode_ready_color(fake_settings_repository, "#111111")
    write_hard_mode_moving_color(fake_settings_repository, "#222222")
    screen._toggle_hard_mode()  # off
    screen._toggle_hard_mode()  # on again: `_hard_mode_colors()` re-reads both

    assert screen._hud._status_light_canvas.itemcget(screen._hud._status_light, "fill") == "#111111"


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
    assert screen._hud._status_light_frame.winfo_manager() == ""
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
    assert screen._sidebar._mode_hard_button.active is False
    assert screen._hud._status_light_frame.winfo_manager() == ""


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
    assert screen._hud._status_label.cget("text") == "Ready"


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
    assert screen._sidebar._mode_hard_button.active is True


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
    assert screen._hud._status_label.cget("text") == "Moving"
