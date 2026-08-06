import tkinter as tk

import pytest

from labyrinthes.app import composition_root
from labyrinthes.app.composition_root import App, build_app
from labyrinthes.app.router import Router, ScreenId


def test_build_app_creates_exactly_one_tk_root_with_home_mounted_first():
    app = build_app()
    try:
        app.root.withdraw()
        assert isinstance(app.root, tk.Tk)
        assert app.router.current_screen_id == ScreenId.HOME
    finally:
        app.root.destroy()


def test_build_app_destroys_the_root_if_wiring_fails_partway_through(monkeypatch):
    destroy_calls = []

    class FakeRoot:
        def destroy(self) -> None:
            destroy_calls.append(True)

    class FakeFrame:
        def pack(self, **kwargs) -> None:
            pass

    def failing_mount_home(parent, state, navigate):
        raise RuntimeError("boom")

    monkeypatch.setattr(composition_root.tk, "Tk", FakeRoot)
    monkeypatch.setattr(composition_root.tk, "Frame", lambda parent: FakeFrame())
    monkeypatch.setattr(composition_root, "mount_home", failing_mount_home)

    with pytest.raises(RuntimeError, match="boom"):
        build_app()

    assert destroy_calls == [True]


def test_navigate_closure_bound_into_a_screens_mount_drives_the_real_router(monkeypatch):
    captured_navigate = {}

    def capturing_mount_home(parent, state, navigate):
        captured_navigate["navigate"] = navigate
        return tk.Frame(parent)

    monkeypatch.setattr(composition_root, "mount_home", capturing_mount_home)
    app = build_app()

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
