"""Builder screen: mount() dispatch, chrome (breadcrumb/settings/theme),
and the New Maze dialog entry state (state=None)."""

import tkinter as tk

from labyrinthes.adapters.tkinter.builder.screen import mount
from labyrinthes.adapters.tkinter.common import (
    NewMazeDialog,
    PillButton,
    SettingsWindow,
    Theme,
    TopBar,
)
from labyrinthes.adapters.tkinter.common.navigation import ScreenId
from labyrinthes.application.confirmation_settings import (
    write_confirm_invalid_input,
)
from labyrinthes.domain.maze import MazeKind


def test_mount_returns_a_frame_parented_under_the_given_parent(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    assert isinstance(frame, tk.Frame)
    assert frame.master is tk_root


def test_mount_renders_a_home_builder_breadcrumb(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    breadcrumb = find_all(frame, TopBar)[0]._breadcrumb
    assert breadcrumb is not None
    assert [label.cget("text") for label in breadcrumb._labels] == ["Home", "Builder"]


def test_breadcrumb_home_segment_is_clickable_and_navigates_home(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, calls = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    breadcrumb = find_all(frame, TopBar)[0]._breadcrumb
    # `tk_root` is withdrawn, so real X11 button-press synthesis isn't
    # reliable; invoke the bound handler directly (see test_icon_btn.py).
    breadcrumb._segment_handlers[0]()

    assert calls == [(ScreenId.HOME, None)]


def test_breadcrumb_trailing_builder_segment_has_no_click_handler(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    breadcrumb = find_all(frame, TopBar)[0]._breadcrumb
    assert breadcrumb._segment_handlers[1] is None


def test_settings_icon_click_opens_a_non_modal_settings_window_leaving_builder_mounted(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    top_bar = find_all(frame, TopBar)[0]
    top_bar._settings_button._on_click()

    # `SettingsWindow` is parented to `tk_root` (the persistent container),
    # not to `frame` itself (Story 1.11) -- see
    # `test_destroying_the_screens_frame_leaves_an_open_settings_window_open`.
    settings_windows = [c for c in tk_root.winfo_children() if isinstance(c, SettingsWindow)]
    assert len(settings_windows) == 1
    assert settings_windows[0].grab_status() is None
    assert frame.winfo_exists()


def test_destroying_the_screens_frame_leaves_an_open_settings_window_open(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    top_bar = find_all(frame, TopBar)[0]
    top_bar._settings_button._on_click()

    settings_windows = [c for c in tk_root.winfo_children() if isinstance(c, SettingsWindow)]
    assert len(settings_windows) == 1
    settings_window = settings_windows[0]

    # The exact operation `Router.navigate()` performs on the
    # previously-mounted screen's frame (Story 1.11: `SettingsWindow` is
    # parented to the persistent container, not to `frame`, so this no
    # longer cascades into destroying it -- see `SettingsWindow`'s
    # docstring).
    frame.destroy()

    assert settings_window.winfo_exists() == 1


def test_theme_toggle_icon_click_invokes_the_passed_in_toggle_theme_callable(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, _ = navigate_stub
    toggle_theme, calls = toggle_theme_stub
    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    top_bar = find_all(frame, TopBar)[0]
    top_bar._theme_toggle_button._on_click()

    assert calls == [1]


def test_open_settings_from_builder_reflects_a_stored_confirmation_value(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    write_confirm_invalid_input(fake_settings_repository, False)
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    top_bar = find_all(frame, TopBar)[0]
    top_bar._settings_button._on_click()

    settings_windows = [c for c in tk_root.winfo_children() if isinstance(c, SettingsWindow)]
    assert len(settings_windows) == 1
    settings_windows[0]._select_category("Confirmation")
    assert settings_windows[0]._confirmation_rows["Alert me about invalid input"].get() is False
    settings_windows[0].destroy()


# -- state=None: New Maze Dialog entry state (Story 3.2) --------------------


def test_cold_open_with_state_none_opens_the_new_maze_dialog(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, calls = navigate_stub
    toggle_theme, _ = toggle_theme_stub

    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    dialogs = [c for c in frame.winfo_children() if isinstance(c, NewMazeDialog)]
    assert len(dialogs) == 1
    assert calls == []
    # I/O matrix, row "Builder in the New-Maze entry state": the Test in
    # Player pill lives only in `_BuilderEditArea` (the active-session
    # branch), so no active session means no such pill anywhere.
    test_pills = [
        b for b in find_all(frame, PillButton) if b._label.cget("text") == "Test in Player"
    ]
    assert test_pills == []


def test_confirming_new_maze_dialog_navigates_to_builder_with_the_new_sketch(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, calls = navigate_stub
    toggle_theme, _ = toggle_theme_stub

    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    dialog = next(c for c in frame.winfo_children() if isinstance(c, NewMazeDialog))
    dialog._entries["columns"].delete(0, "end")
    dialog._entries["columns"].insert(0, "20")
    dialog._entries["rows"].delete(0, "end")
    dialog._entries["rows"].insert(0, "15")
    dialog._on_confirm_clicked()

    assert len(calls) == 1
    screen_id, maze = calls[0]
    assert screen_id is ScreenId.BUILDER
    assert maze.kind is MazeKind.SKETCH
    assert maze.id is None
    assert maze.grid.width == 20
    assert maze.grid.height == 15


def test_cancelling_the_new_maze_dialog_destroys_it_and_leaves_the_frame_empty(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, calls = navigate_stub
    toggle_theme, _ = toggle_theme_stub

    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    dialog = next(c for c in frame.winfo_children() if isinstance(c, NewMazeDialog))
    dialog._on_cancel()

    assert not dialog.winfo_exists()
    assert calls == []
    assert [c for c in frame.winfo_children() if isinstance(c, NewMazeDialog)] == []
