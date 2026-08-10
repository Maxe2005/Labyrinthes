import tkinter as tk

import pytest

from labyrinthes.adapters.tkinter.common import SettingsWindow, Theme, TopBar
from labyrinthes.adapters.tkinter.common.navigation import ScreenId
from labyrinthes.adapters.tkinter.player.classic_gallery import ClassicMazeGallery
from labyrinthes.adapters.tkinter.player.gameplay_screen import GameplayScreen
from labyrinthes.adapters.tkinter.player.screen import mount
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.position import Position


def _maze(kind: MazeKind = MazeKind.CLASSIC) -> Maze:
    return Maze(
        grid=Grid.filled(width=4, height=3),
        entry=Position(row=0, col=0),
        exit=Position(row=2, col=3),
        kind=kind,
        id=None,
    )


def test_mount_returns_a_frame_parented_under_the_given_parent(
    tk_root, navigate_stub, toggle_theme_stub, fake_maze_repository, fake_settings_repository
):
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    assert isinstance(frame, tk.Frame)
    assert frame.master is tk_root


def test_mount_accepts_a_real_maze_as_state_without_raising(
    tk_root, navigate_stub, toggle_theme_stub, fake_maze_repository, fake_settings_repository
):
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        _maze(),
        navigate,
        Theme.LIGHT,
        toggle_theme,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    assert isinstance(frame, tk.Frame)


def test_mount_renders_a_home_player_breadcrumb(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_maze_repository,
    fake_settings_repository,
):
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    breadcrumb = find_all(frame, TopBar)[0]._breadcrumb
    assert breadcrumb is not None
    assert [label.cget("text") for label in breadcrumb._labels] == ["Home", "Player"]


def test_breadcrumb_home_segment_is_clickable_and_navigates_home(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_maze_repository,
    fake_settings_repository,
):
    navigate, calls = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    breadcrumb = find_all(frame, TopBar)[0]._breadcrumb
    # `tk_root` is withdrawn, so real X11 button-press synthesis isn't
    # reliable; invoke the bound handler directly (see test_icon_btn.py).
    breadcrumb._segment_handlers[0]()

    assert calls == [(ScreenId.HOME, None)]


def test_breadcrumb_trailing_player_segment_has_no_click_handler(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_maze_repository,
    fake_settings_repository,
):
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    breadcrumb = find_all(frame, TopBar)[0]._breadcrumb
    assert breadcrumb._segment_handlers[1] is None


@pytest.mark.parametrize(
    ("kind", "expected_label"),
    [
        (MazeKind.CLASSIC, "Classic Maze"),
        (MazeKind.SAVED_RANDOM, "Saved Random Maze"),
        (MazeKind.GENERATED, "Random Maze"),
        (MazeKind.SKETCH, "Sketch"),
    ],
)
def test_breadcrumb_grows_to_three_segments_in_the_gameplay_view_with_a_kind_derived_label(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_maze_repository,
    fake_settings_repository,
    kind,
    expected_label,
):
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        _maze(kind),
        navigate,
        Theme.LIGHT,
        toggle_theme,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    breadcrumb = find_all(frame, TopBar)[0]._breadcrumb
    assert [label.cget("text") for label in breadcrumb._labels] == [
        "Home",
        "Player",
        expected_label,
    ]


def test_breadcrumb_trailing_label_updates_after_saving_a_generated_maze(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_maze_repository,
    fake_settings_repository,
):
    # Regression: saving a `GENERATED` maze transitions its `kind` to
    # `SAVED_RANDOM` mid-session -- the breadcrumb's trailing label (built
    # once, from the *original* kind) must follow, not keep showing
    # "Random Maze" forever.
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        _maze(MazeKind.GENERATED),
        navigate,
        Theme.LIGHT,
        toggle_theme,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    breadcrumb = find_all(frame, TopBar)[0]._breadcrumb
    assert breadcrumb._labels[2].cget("text") == "Random Maze"
    gameplay = find_all(frame, GameplayScreen)[0]

    gameplay._on_save_confirmed("forest")

    assert breadcrumb._labels[2].cget("text") == "Saved Random Maze"


def test_breadcrumb_player_segment_is_clickable_and_navigates_back_to_the_gallery(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_maze_repository,
    fake_settings_repository,
):
    navigate, calls = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        _maze(),
        navigate,
        Theme.LIGHT,
        toggle_theme,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    breadcrumb = find_all(frame, TopBar)[0]._breadcrumb
    breadcrumb._segment_handlers[1]()

    assert calls == [(ScreenId.PLAYER, None)]


def test_breadcrumb_trailing_kind_label_segment_has_no_click_handler_in_the_gameplay_view(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_maze_repository,
    fake_settings_repository,
):
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        _maze(),
        navigate,
        Theme.LIGHT,
        toggle_theme,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    breadcrumb = find_all(frame, TopBar)[0]._breadcrumb
    assert breadcrumb._segment_handlers[2] is None


def test_settings_icon_click_opens_a_non_modal_settings_window_leaving_player_mounted(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_maze_repository,
    fake_settings_repository,
):
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        maze_repository=fake_maze_repository,
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
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_maze_repository,
    fake_settings_repository,
):
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        maze_repository=fake_maze_repository,
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
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_maze_repository,
    fake_settings_repository,
):
    navigate, _ = navigate_stub
    toggle_theme, calls = toggle_theme_stub
    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    top_bar = find_all(frame, TopBar)[0]
    top_bar._theme_toggle_button._on_click()

    assert calls == [1]


def test_state_is_none_mounts_the_classic_maze_gallery(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    seeded_maze_repository,
    fake_settings_repository,
):
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        maze_repository=seeded_maze_repository,
        settings_repository=fake_settings_repository,
    )

    galleries = find_all(frame, ClassicMazeGallery)
    assert len(galleries) == 1


def test_state_not_none_mounts_the_gameplay_screen_not_the_gallery(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    seeded_maze_repository,
    fake_settings_repository,
):
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        _maze(),
        navigate,
        Theme.LIGHT,
        toggle_theme,
        maze_repository=seeded_maze_repository,
        settings_repository=fake_settings_repository,
    )

    assert find_all(frame, ClassicMazeGallery) == []


def test_state_not_none_mounts_a_gameplay_screen_holding_that_maze(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    seeded_maze_repository,
    fake_settings_repository,
):
    # Story 2.4: `screen.py` swapped `GameplayPlaceholder` for
    # `GameplayScreen`, which holds the mounted `Maze` as `self._maze`
    # (mutable, so a save can swap it in place -- see that module's
    # docstring).
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    maze = _maze()
    frame = mount(
        tk_root,
        maze,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        maze_repository=seeded_maze_repository,
        settings_repository=fake_settings_repository,
    )

    screens = find_all(frame, GameplayScreen)
    assert len(screens) == 1
    assert screens[0]._maze == maze


def test_state_not_none_never_reads_the_maze_repository(
    tk_root, navigate_stub, toggle_theme_stub, fake_settings_repository
):
    # "Re-navigate with state" row of the I/O matrix: the gameplay view
    # receives its `Maze` directly through `state`, it never touches
    # `maze_repository` -- a repository whose every method raises proves no
    # read happens.
    class ExplodingMazeRepository:
        def save(self, maze, name):
            raise AssertionError("save() must not be called")

        def load(self, name, kind):
            raise AssertionError("load() must not be called")

        def find_by_id(self, maze_id):
            raise AssertionError("find_by_id() must not be called")

        def list_names(self, kind):
            raise AssertionError("list_names() must not be called")

    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub

    frame = mount(
        tk_root,
        _maze(),
        navigate,
        Theme.LIGHT,
        toggle_theme,
        maze_repository=ExplodingMazeRepository(),
        settings_repository=fake_settings_repository,
    )

    assert isinstance(frame, tk.Frame)


def test_confirming_a_pick_in_the_gallery_hands_the_maze_off_via_navigate(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    seeded_maze_repository,
    fake_settings_repository,
):
    navigate, calls = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        maze_repository=seeded_maze_repository,
        settings_repository=fake_settings_repository,
    )

    gallery = find_all(frame, ClassicMazeGallery)[0]
    gallery._on_play()

    assert len(calls) == 1
    screen_id, maze = calls[0]
    assert screen_id == ScreenId.PLAYER
    assert isinstance(maze, Maze)
