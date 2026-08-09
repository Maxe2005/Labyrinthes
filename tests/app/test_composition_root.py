import tkinter as tk

import pytest

from labyrinthes.adapters.storage.json_settings_repository import JsonSettingsRepository
from labyrinthes.adapters.tkinter.common import SettingsWindow, TopBar
from labyrinthes.adapters.tkinter.common.tokens import Theme
from labyrinthes.app import composition_root
from labyrinthes.app.composition_root import App, build_app
from labyrinthes.app.router import Router, ScreenId


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

    class FakeFrame:
        def pack(self, **kwargs) -> None:
            pass

    def failing_mount_home(parent, state, navigate, theme, toggle_theme):
        raise RuntimeError("boom")

    monkeypatch.setattr(composition_root.tk, "Tk", FakeRoot)
    monkeypatch.setattr(composition_root.tk, "Frame", lambda parent: FakeFrame())
    monkeypatch.setattr(composition_root, "mount_home", failing_mount_home)

    with pytest.raises(RuntimeError, match="boom"):
        build_app(settings_repository=JsonSettingsRepository(root=tmp_path))

    assert destroy_calls == [True]


def test_navigate_closure_bound_into_a_screens_mount_drives_the_real_router(monkeypatch, tmp_path):
    captured_navigate = {}

    def capturing_mount_home(parent, state, navigate, theme, toggle_theme):
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

    def capturing_mount_home(parent, state, navigate, theme, toggle_theme):
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

    def capturing_mount_home(parent, state, navigate, theme, toggle_theme):
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

    def capturing_mount_home_2(parent, state, navigate, theme, toggle_theme):
        captured_theme["theme"] = theme
        return tk.Frame(parent)

    monkeypatch.setattr(composition_root, "mount_home", capturing_mount_home_2)
    second_app = build_app(settings_repository=repository)
    try:
        second_app.root.withdraw()
        assert captured_theme["theme"] == Theme.DARK
    finally:
        second_app.root.destroy()


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
