import re
import tkinter as tk

import pytest

from labyrinthes.adapters.storage.csv_maze_repository import CsvMazeRepository
from labyrinthes.adapters.storage.json_settings_repository import JsonSettingsRepository
from labyrinthes.adapters.tkinter.common import SettingsWindow, TopBar
from labyrinthes.adapters.tkinter.common.tokens import Theme
from labyrinthes.adapters.tkinter.player.classic_gallery import ClassicMazeGallery
from labyrinthes.app import composition_root
from labyrinthes.app.composition_root import App, build_app
from labyrinthes.app.router import Router, ScreenId
from labyrinthes.application.settings_repository import SettingsScope
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.position import Position


def _find_all(widget: tk.Widget, widget_type: type) -> list:
    """Recursively collect every `widget_type` descendant of `widget`."""
    found = []
    for child in widget.winfo_children():
        if isinstance(child, widget_type):
            found.append(child)
        found.extend(_find_all(child, widget_type))
    return found


def test_build_app_creates_exactly_one_tk_root_with_home_mounted_first(tmp_path):
    app = build_app(settings_repository=JsonSettingsRepository(root=tmp_path))
    try:
        app.root.withdraw()
        assert isinstance(app.root, tk.Tk)
        assert app.router.current_screen_id == ScreenId.HOME
    finally:
        app.root.destroy()


def test_build_app_destroys_the_root_if_wiring_fails_partway_through(monkeypatch, tmp_path):
    destroy_calls = []

    class FakeRoot:
        def destroy(self) -> None:
            destroy_calls.append(True)

        def winfo_screenwidth(self) -> int:
            return 1920

        def winfo_screenheight(self) -> int:
            return 1080

        def geometry(self, spec: str | None = None) -> str:
            return ""

    class FakeFrame:
        def pack(self, **kwargs) -> None:
            pass

    def failing_mount_home(parent, state, navigate, theme, toggle_theme, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(composition_root.tk, "Tk", FakeRoot)
    monkeypatch.setattr(composition_root.tk, "Frame", lambda parent: FakeFrame())
    monkeypatch.setattr(composition_root, "mount_home", failing_mount_home)

    with pytest.raises(RuntimeError, match="boom"):
        build_app(settings_repository=JsonSettingsRepository(root=tmp_path))

    assert destroy_calls == [True]


def test_navigate_closure_bound_into_a_screens_mount_drives_the_real_router(monkeypatch, tmp_path):
    captured_navigate = {}

    def capturing_mount_home(parent, state, navigate, theme, toggle_theme, **kwargs):
        captured_navigate["navigate"] = navigate
        return tk.Frame(parent)

    monkeypatch.setattr(composition_root, "mount_home", capturing_mount_home)
    app = build_app(settings_repository=JsonSettingsRepository(root=tmp_path))

    try:
        app.root.withdraw()
        assert "navigate" in captured_navigate

        captured_navigate["navigate"](ScreenId.BUILDER, None)

        assert app.router.current_screen_id == ScreenId.BUILDER
    finally:
        app.root.destroy()


def test_theme_toggle_keeps_a_handed_off_maze_mounted_on_the_player(monkeypatch, tmp_path):
    # I/O matrix, row "Theme toggled while the handed-off maze is in the
    # Player" (Story 3.8): a `navigate(ScreenId.PLAYER, maze)` hand-off
    # records that maze as `last_state`, so a theme-triggered re-navigate
    # re-mounts the Player with the *same* handed-off `Maze` -- the test
    # run restarts, but the maze itself stays mounted (no home-bypass lost).
    handed_off = Maze(
        grid=Grid.filled(4, 3),
        entry=Position(row=0, col=0),
        exit=Position(row=2, col=3),
        kind=MazeKind.CLASSIC,
        id=None,
    )
    captured = {}
    captured_navigate = {}
    captured_toggle_theme = {}

    def capturing_mount_home(parent, state, navigate, theme, toggle_theme, **kwargs):
        captured_navigate["navigate"] = navigate
        captured_toggle_theme["toggle_theme"] = toggle_theme
        return tk.Frame(parent)

    def capturing_mount_player(parent, state, navigate, theme, toggle_theme, **kwargs):
        captured["maze"] = state
        return tk.Frame(parent)

    monkeypatch.setattr(composition_root, "mount_home", capturing_mount_home)
    monkeypatch.setattr(composition_root, "mount_player", capturing_mount_player)
    app = build_app(settings_repository=JsonSettingsRepository(root=tmp_path))
    try:
        app.root.withdraw()

        captured_navigate["navigate"](ScreenId.PLAYER, handed_off)
        assert captured["maze"] is handed_off

        captured_toggle_theme["toggle_theme"]()

        assert app.router.current_screen_id == ScreenId.PLAYER
        assert captured["maze"] is handed_off
    finally:
        app.root.destroy()


def test_main_builds_the_app_and_calls_mainloop_on_its_root(monkeypatch):
    mainloop_calls = []

    class FakeRoot:
        def mainloop(self) -> None:
            mainloop_calls.append(True)

    fake_app = App(root=FakeRoot(), router=Router(container=None))
    monkeypatch.setattr(composition_root, "build_app", lambda: fake_app)

    composition_root.main()

    assert mainloop_calls == [True]


def test_toggling_theme_bound_into_a_screens_mount_rerenders_the_current_screen(
    monkeypatch, tmp_path
):
    captured = []

    def capturing_mount_home(parent, state, navigate, theme, toggle_theme, **kwargs):
        frame = tk.Frame(parent)
        captured.append({"theme": theme, "toggle_theme": toggle_theme, "frame": frame})
        return frame

    monkeypatch.setattr(composition_root, "mount_home", capturing_mount_home)
    app = build_app(settings_repository=JsonSettingsRepository(root=tmp_path))

    try:
        app.root.withdraw()
        assert len(captured) == 1
        first_call = captured[0]

        first_call["toggle_theme"]()

        assert len(captured) == 2
        second_call = captured[1]
        assert second_call["theme"] != first_call["theme"]
        assert second_call["frame"] is not first_call["frame"]
        # The old frame isn't just replaced but actually torn down --
        # otherwise a regression could leave two overlapping `TopBar`s
        # mounted side by side and this test would still pass.
        assert not first_call["frame"].winfo_exists()
        assert app.router.current_screen_id == ScreenId.HOME
    finally:
        app.root.destroy()


def test_theme_persisted_by_one_build_app_call_is_seen_by_a_second_build_app_call(
    monkeypatch, tmp_path
):
    # Same idiom as
    # `test_shared_scope_observed_identically_across_two_repository_instances`
    # (`tests/adapters/storage/test_json_settings_repository.py`): two
    # separate `App`s built sequentially against the same underlying
    # repository, no running mainloop needed.
    repository = JsonSettingsRepository(root=tmp_path)
    captured_toggle_theme = {}

    def capturing_mount_home(parent, state, navigate, theme, toggle_theme, **kwargs):
        captured_toggle_theme["toggle_theme"] = toggle_theme
        return tk.Frame(parent)

    monkeypatch.setattr(composition_root, "mount_home", capturing_mount_home)
    first_app = build_app(settings_repository=repository)
    try:
        first_app.root.withdraw()
        captured_toggle_theme["toggle_theme"]()
    finally:
        first_app.root.destroy()

    captured_theme = {}

    def capturing_mount_home_2(parent, state, navigate, theme, toggle_theme, **kwargs):
        captured_theme["theme"] = theme
        return tk.Frame(parent)

    monkeypatch.setattr(composition_root, "mount_home", capturing_mount_home_2)
    second_app = build_app(settings_repository=repository)
    try:
        second_app.root.withdraw()
        assert captured_theme["theme"] == Theme.DARK
    finally:
        second_app.root.destroy()


def test_player_registration_is_reachable_and_uses_the_injected_maze_repository(tmp_path):
    # Player's `mount()` requires a keyword-only `maze_repository` that
    # Home/Builder don't take (Story 2.1) -- this exercises the real
    # `functools.partial` wiring end to end: navigating to Player must not
    # raise `TypeError: mount() missing ... maze_repository`, and the
    # `tmp_path`-rooted repository actually reaches the mounted screen (an
    # empty classic library renders the gallery's empty state, not a crash).
    app = build_app(
        settings_repository=JsonSettingsRepository(root=tmp_path / "settings"),
        maze_repository=CsvMazeRepository(root=tmp_path / "mazes"),
    )
    try:
        app.root.withdraw()

        app.router.navigate(ScreenId.PLAYER)

        assert app.router.current_screen_id == ScreenId.PLAYER
        # Not just "navigation didn't raise" -- the injected repository must
        # actually have reached `ClassicMazeGallery`: an empty `tmp_path`
        # library renders the gallery's empty state (no `_play_button`), not
        # some other content a broken `functools.partial` binding could
        # still coincidentally produce a `Frame` for.
        galleries = _find_all(app.root, ClassicMazeGallery)
        assert len(galleries) == 1
        assert not hasattr(galleries[0], "_play_button")
    finally:
        app.root.destroy()


def test_build_app_defaults_maze_repository_to_a_real_csv_maze_repository(tmp_path):
    app = build_app(settings_repository=JsonSettingsRepository(root=tmp_path))
    try:
        app.root.withdraw()

        # No explicit `maze_repository` passed -- must not raise navigating
        # to Player, proving `build_app()` supplied its own default.
        app.router.navigate(ScreenId.PLAYER)

        assert app.router.current_screen_id == ScreenId.PLAYER
    finally:
        app.root.destroy()


def test_root_window_is_given_a_fixed_size_and_centered_on_screen_at_startup_exactly_once(
    monkeypatch, tmp_path
):
    # Story 4.10 follow-up: unlike Story 4.8's natural-post-mount-size
    # `_center_on_screen()`, the window's size *and* position are now set
    # together, once, before Home is ever mounted -- asserts on the exact
    # `.geometry()` string requested, not on `winfo_x()`/`winfo_y()` after
    # the fact (whether that request is actually *honored* is up to the
    # platform's window manager, outside this codebase's control -- mirrors
    # `test_f11_is_bound_on_the_root_...`'s same rationale for
    # `-fullscreen`).
    calls = []
    original_geometry = tk.Tk.geometry

    def spying_geometry(self, spec=None):
        if spec is not None:
            calls.append(spec)
        return original_geometry(self, spec)

    monkeypatch.setattr(tk.Tk, "geometry", spying_geometry)
    app = build_app(settings_repository=JsonSettingsRepository(root=tmp_path))
    try:
        # Exactly one `.geometry(...)` call for the entire build -- the
        # window never auto-resizes across navigation.
        assert len(calls) == 1
        match = re.fullmatch(r"(\d+)x(\d+)\+(\d+)\+(\d+)", calls[0])
        assert match is not None
        width, height, x, y = (int(group) for group in match.groups())
        # No stored setting: defaults to 1280x800 (clamped to the screen).
        screen_width = app.root.winfo_screenwidth()
        screen_height = app.root.winfo_screenheight()
        assert width == min(1280, max(800, screen_width))
        assert height == min(800, max(600, screen_height))
        assert x == (screen_width - width) // 2
        assert y == (screen_height - height) // 2
    finally:
        app.root.destroy()


def test_root_window_size_reads_the_stored_shared_scope_setting(monkeypatch, tmp_path):
    calls = []
    original_geometry = tk.Tk.geometry

    def spying_geometry(self, spec=None):
        if spec is not None:
            calls.append(spec)
        return original_geometry(self, spec)

    monkeypatch.setattr(tk.Tk, "geometry", spying_geometry)
    repository = JsonSettingsRepository(root=tmp_path)
    repository.set(SettingsScope.SHARED, "window_width", 900)
    repository.set(SettingsScope.SHARED, "window_height", 700)

    app = build_app(settings_repository=repository)
    try:
        assert len(calls) == 1
        match = re.fullmatch(r"(\d+)x(\d+)\+(\d+)\+(\d+)", calls[0])
        assert match is not None
        width, height, _x, _y = (int(group) for group in match.groups())
        assert width == 900
        assert height == 700
    finally:
        app.root.destroy()


def test_root_window_never_resizes_across_navigation(tmp_path):
    app = build_app(settings_repository=JsonSettingsRepository(root=tmp_path))
    try:
        app.root.withdraw()
        initial_geometry = app.root.geometry()

        app.router.navigate(ScreenId.BUILDER)
        app.router.navigate(ScreenId.PLAYER)
        app.router.navigate(ScreenId.HOME)

        assert app.root.geometry() == initial_geometry
    finally:
        app.root.destroy()


def test_root_window_is_resizable_in_both_directions(tmp_path):
    app = build_app(settings_repository=JsonSettingsRepository(root=tmp_path))
    try:
        assert app.root.resizable() == (1, 1)
    finally:
        app.root.destroy()


def test_f11_is_bound_on_the_root_and_toggles_its_fullscreen_attribute(monkeypatch, tmp_path):
    # `bind_shortcut` is monkeypatched here (rather than a real F11
    # keypress) for the same reason `test_navigate_closure_bound_...`
    # monkeypatches `mount_home` to capture `navigate`: it hands back the
    # real closure `build_app()` wires up, so the toggle can be exercised
    # and asserted on directly instead of relying on unreliable real X11
    # key-event synthesis under a withdrawn root (see `keybindings.py`'s
    # own test file for that convention).
    captured = {}

    def capturing_bind_shortcut(widget, kb, callback):
        captured[kb.action_id] = (widget, callback)
        return lambda event=None: None

    monkeypatch.setattr(composition_root, "bind_shortcut", capturing_bind_shortcut)
    app = build_app(settings_repository=JsonSettingsRepository(root=tmp_path))
    try:
        app.root.withdraw()
        assert "toggle_fullscreen" in captured
        widget, toggle = captured["toggle_fullscreen"]
        # AD-10: F11 is bound on the root itself, not some other widget.
        assert widget is app.root

        # `.attributes("-fullscreen")` has no reliable getter under a
        # headless/no-window-manager `Xvfb` (confirmed live: it reads back
        # `0` even right after being set `True`) -- asserting on the calls
        # `toggle_root_fullscreen()` makes is the only way this story's own
        # Design Notes ("track fullscreen per-window as a bool flag, no Tk
        # getter") lets the toggle be verified at all.
        calls = []
        monkeypatch.setattr(app.root, "attributes", lambda *args: calls.append(args))

        toggle()
        toggle()

        assert calls == [("-fullscreen", True), ("-fullscreen", False)]
    finally:
        app.root.destroy()


def test_resizing_the_root_while_a_screen_without_a_maze_canvas_is_mounted_raises_nothing(
    tmp_path,
):
    # I/O matrix row (spec-4-8): `<Configure>` is bound directly on each
    # maze canvas widget (`edit_area.py`/`gameplay/screen.py`), never on the
    # root or a screen's frame -- so resizing while Home (no canvas) is
    # mounted has no handler to reach at all, by construction.
    app = build_app(settings_repository=JsonSettingsRepository(root=tmp_path))
    try:
        app.root.withdraw()
        assert app.router.current_screen_id == ScreenId.HOME

        app.root.event_generate("<Configure>", width=900, height=700)
        app.root.update_idletasks()

        assert app.router.current_screen_id == ScreenId.HOME
    finally:
        app.root.destroy()


def test_f11_on_a_focused_settings_window_does_not_also_toggle_the_roots_fullscreen(
    tmp_path,
):
    # Integration regression for the Design Notes' F11 cross-window
    # scoping claim: with both the root's global F11 binding (`bind_all`,
    # interpreter-wide) and `SettingsWindow`'s own local override live at
    # once, a real F11 dispatched while the Settings `Toplevel` has focus
    # must invoke only its own handler -- the local binding's `"break"`
    # return must stop Tk's bindtag scan before it reaches the root's.
    # Unlike `test_f11_is_bound_on_the_root_...` (which monkeypatches
    # `bind_shortcut` to inspect the closure directly) and
    # `test_f11_handler_returns_break_...` (which calls the Settings
    # handler directly), this drives both real bindings through a real
    # dispatched event to prove the cross-widget mechanism itself.
    app = build_app(settings_repository=JsonSettingsRepository(root=tmp_path))
    try:
        app.root.withdraw()
        top_bar = _find_all(app.root, TopBar)[0]
        top_bar._settings_button._on_click()
        settings_window = _find_all(app.root, SettingsWindow)[0]

        root_calls = []
        app.root.attributes = lambda *args: root_calls.append(args)

        settings_window.update()
        settings_window.focus_force()
        settings_window.update()
        settings_window.event_generate("<F11>")
        app.root.update()

        assert root_calls == []
    finally:
        app.root.destroy()


def test_settings_window_opened_on_home_survives_a_real_navigate_to_builder(tmp_path):
    # End-to-end regression for Story 1.11: exercises the real `Router` and
    # real screen `mount()`s (no `navigate_stub`), unlike the per-screen
    # tests that only mirror `Router.navigate()`'s `frame.destroy()` call
    # in isolation.
    app = build_app(settings_repository=JsonSettingsRepository(root=tmp_path))
    try:
        app.root.withdraw()
        assert app.router.current_screen_id == ScreenId.HOME

        top_bar = _find_all(app.root, TopBar)[0]
        top_bar._settings_button._on_click()

        settings_windows = _find_all(app.root, SettingsWindow)
        assert len(settings_windows) == 1
        settings_window = settings_windows[0]

        app.router.navigate(ScreenId.BUILDER)

        assert app.router.current_screen_id == ScreenId.BUILDER
        assert settings_window.winfo_exists() == 1
    finally:
        app.root.destroy()
