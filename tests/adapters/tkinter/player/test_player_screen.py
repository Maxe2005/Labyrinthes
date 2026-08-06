import tkinter as tk

from labyrinthes.adapters.tkinter.common import SettingsWindow, TopBar
from labyrinthes.adapters.tkinter.common.navigation import ScreenId
from labyrinthes.adapters.tkinter.player.screen import mount
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.position import Position


def _maze() -> Maze:
    return Maze(
        grid=Grid.filled(width=4, height=3),
        entry=Position(row=0, col=0),
        exit=Position(row=2, col=3),
        kind=MazeKind.CLASSIC,
        id=None,
    )


def test_mount_returns_a_frame_parented_under_the_given_parent(tk_root, navigate_stub):
    navigate, _ = navigate_stub
    frame = mount(tk_root, None, navigate)

    assert isinstance(frame, tk.Frame)
    assert frame.master is tk_root


def test_mount_accepts_a_real_maze_as_state_without_raising(tk_root, navigate_stub):
    navigate, _ = navigate_stub
    frame = mount(tk_root, _maze(), navigate)

    assert isinstance(frame, tk.Frame)


def test_mount_renders_a_home_player_breadcrumb(tk_root, navigate_stub, find_all):
    navigate, _ = navigate_stub
    frame = mount(tk_root, None, navigate)

    breadcrumb = find_all(frame, TopBar)[0]._breadcrumb
    assert breadcrumb is not None
    assert [label.cget("text") for label in breadcrumb._labels] == ["Home", "Player"]


def test_breadcrumb_home_segment_is_clickable_and_navigates_home(tk_root, navigate_stub, find_all):
    navigate, calls = navigate_stub
    frame = mount(tk_root, None, navigate)

    breadcrumb = find_all(frame, TopBar)[0]._breadcrumb
    # `tk_root` is withdrawn, so real X11 button-press synthesis isn't
    # reliable; invoke the bound handler directly (see test_icon_btn.py).
    breadcrumb._segment_handlers[0]()

    assert calls == [(ScreenId.HOME, None)]


def test_breadcrumb_trailing_player_segment_has_no_click_handler(tk_root, navigate_stub, find_all):
    navigate, _ = navigate_stub
    frame = mount(tk_root, None, navigate)

    breadcrumb = find_all(frame, TopBar)[0]._breadcrumb
    assert breadcrumb._segment_handlers[1] is None


def test_settings_icon_click_opens_a_non_modal_settings_window_leaving_player_mounted(
    tk_root, navigate_stub, find_all
):
    navigate, _ = navigate_stub
    frame = mount(tk_root, None, navigate)

    top_bar = find_all(frame, TopBar)[0]
    top_bar._settings_button._on_click()

    settings_windows = [c for c in frame.winfo_children() if isinstance(c, SettingsWindow)]
    assert len(settings_windows) == 1
    assert settings_windows[0].grab_status() is None
    assert frame.winfo_exists()
