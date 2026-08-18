import tkinter as tk

from labyrinthes.adapters.tkinter.common import (
    NewMazeDialog,
    PillButton,
    SettingsWindow,
    Theme,
    TopBar,
)
from labyrinthes.adapters.tkinter.common.keybindings import keybinding
from labyrinthes.adapters.tkinter.common.navigation import ScreenId
from labyrinthes.adapters.tkinter.home.screen import mount
from labyrinthes.application.confirmation_settings import write_confirm_switch_maze
from labyrinthes.domain.maze import MazeKind


def test_mount_returns_a_frame_parented_under_the_given_parent(
    tk_root, navigate_stub, toggle_theme_stub, fake_settings_repository
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
    )

    assert isinstance(frame, tk.Frame)
    assert frame.master is tk_root


def test_mount_renders_a_top_bar_with_no_breadcrumb(
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    )

    top_bars = find_all(frame, TopBar)
    assert len(top_bars) == 1
    assert top_bars[0]._breadcrumb is None


def test_mount_renders_the_brand_mark(
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    )

    labels = {label.cget("text") for label in find_all(frame, tk.Label)}
    assert "Labyrinthes" in labels


def test_mount_renders_open_builder_and_open_player_entry_points(
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    )

    labels = {button._label.cget("text") for button in find_all(frame, PillButton)}
    assert labels == {"Open Builder", "Open Player", "New Maze"}


def test_open_builder_button_navigates_to_builder_with_no_state(
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    )

    open_builder = next(
        b for b in find_all(frame, PillButton) if b._label.cget("text") == "Open Builder"
    )
    # `tk_root` is withdrawn, so real X11 button-press synthesis isn't
    # reliable; invoke the bound handler directly (see test_icon_btn.py).
    open_builder._on_click()

    assert calls == [(ScreenId.BUILDER, None)]


def test_open_player_button_navigates_to_player_with_no_state(
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    )

    open_player = next(
        b for b in find_all(frame, PillButton) if b._label.cget("text") == "Open Player"
    )
    open_player._on_click()

    assert calls == [(ScreenId.PLAYER, None)]


def test_settings_icon_click_opens_a_non_modal_settings_window_leaving_home_mounted(
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    )

    top_bar = find_all(frame, TopBar)[0]
    top_bar._theme_toggle_button._on_click()

    assert calls == [1]


def test_open_builder_kbd_tag_matches_the_canonical_keybinding_table(
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    )

    open_builder = next(
        b for b in find_all(frame, PillButton) if b._label.cget("text") == "Open Builder"
    )

    assert open_builder._kbd is not None
    assert open_builder._kbd.cget("text") == keybinding("open_builder").display


def test_open_player_kbd_tag_matches_the_canonical_keybinding_table(
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    )

    open_player = next(
        b for b in find_all(frame, PillButton) if b._label.cget("text") == "Open Player"
    )

    assert open_player._kbd is not None
    assert open_player._kbd.cget("text") == keybinding("open_player").display


def test_mount_registers_the_open_builder_shortcut(
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    )

    assert frame.bind_all(keybinding("open_builder").event) != ""


def test_mount_registers_the_open_player_shortcut(
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    )

    assert frame.bind_all(keybinding("open_player").event) != ""


def test_new_maze_kbd_tag_matches_the_canonical_keybinding_table(
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    )

    new_maze = next(b for b in find_all(frame, PillButton) if b._label.cget("text") == "New Maze")

    assert new_maze._kbd is not None
    assert new_maze._kbd.cget("text") == keybinding("open_new_maze").display


def test_mount_registers_the_open_new_maze_shortcut(
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    )

    assert frame.bind_all(keybinding("open_new_maze").event) != ""


def test_new_maze_button_click_opens_a_dialog_parented_to_the_calling_screen_frame(
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
):
    # `NewMazeDialog` is parented to `frame` (Home's own screen frame, the
    # calling widget), not `tk_root` (the app's persistent container) --
    # unlike `SettingsWindow`, nothing about this dialog is worth surviving
    # a navigate-away, mirroring `GenerateRandomDialog`'s (Story 2.2)
    # calling-widget parenting.
    navigate, calls = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
    )

    new_maze = next(b for b in find_all(frame, PillButton) if b._label.cget("text") == "New Maze")
    new_maze._on_click()

    dialogs = [c for c in frame.winfo_children() if isinstance(c, NewMazeDialog)]
    assert len(dialogs) == 1
    assert calls == []


def test_new_maze_dialog_confirm_navigates_to_player_with_the_new_sketch(
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    )

    new_maze = next(b for b in find_all(frame, PillButton) if b._label.cget("text") == "New Maze")
    new_maze._on_click()

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
    assert not dialog.winfo_exists()


def test_open_settings_from_home_reflects_a_stored_confirmation_value(
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
):
    write_confirm_switch_maze(fake_settings_repository, True)
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
    )

    top_bar = find_all(frame, TopBar)[0]
    top_bar._settings_button._on_click()

    settings_windows = [c for c in tk_root.winfo_children() if isinstance(c, SettingsWindow)]
    assert len(settings_windows) == 1
    settings_windows[0]._select_category("Confirmation")
    assert settings_windows[0]._confirmation_rows["Confirm before switching mazes"].get() is True
    settings_windows[0].destroy()
