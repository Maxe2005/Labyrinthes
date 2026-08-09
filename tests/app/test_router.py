import tkinter as tk

import pytest

from labyrinthes.app.errors import UnregisteredScreenError
from labyrinthes.app.router import Router, ScreenId
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


def test_navigate_calls_mount_with_container_and_state(tk_root):
    router = Router(tk_root)
    calls = []

    def mount(parent, state):
        calls.append((parent, state))
        return tk.Frame(parent)

    router.register(ScreenId.HOME, mount)
    router.navigate(ScreenId.HOME)

    assert calls == [(tk_root, None)]
    assert router.current_screen_id == ScreenId.HOME


def test_navigate_passes_the_exact_state_object_through(tk_root):
    router = Router(tk_root)
    maze = _maze()
    received = []

    def mount(parent, state):
        received.append(state)
        return tk.Frame(parent)

    router.register(ScreenId.PLAYER, mount)
    router.navigate(ScreenId.PLAYER, state=maze)

    assert received == [maze]
    assert received[0] is maze


def test_first_navigate_does_not_try_to_destroy_a_nonexistent_previous_frame(tk_root):
    router = Router(tk_root)
    router.register(ScreenId.HOME, lambda parent, state: tk.Frame(parent))

    router.navigate(ScreenId.HOME)

    assert router.current_screen_id == ScreenId.HOME


def test_navigating_a_second_time_destroys_the_previous_frame_after_packing_the_new_one(
    tk_root,
):
    router = Router(tk_root)
    frames = {}

    def mount_home(parent, state):
        frame = tk.Frame(parent)
        frames["home"] = frame
        return frame

    def mount_builder(parent, state):
        home_frame = frames["home"]
        # New-before-old: the previous frame must still exist and be packed
        # at the moment the new screen is mounted.
        assert home_frame.winfo_exists()
        frame = tk.Frame(parent)
        frames["builder"] = frame
        return frame

    router.register(ScreenId.HOME, mount_home)
    router.register(ScreenId.BUILDER, mount_builder)

    router.navigate(ScreenId.HOME)
    router.navigate(ScreenId.BUILDER)

    assert not frames["home"].winfo_exists()
    assert frames["builder"].winfo_exists()
    assert router.current_screen_id == ScreenId.BUILDER


def test_navigate_to_unregistered_screen_raises_and_leaves_current_screen_mounted(tk_root):
    router = Router(tk_root)
    home_frame_holder = {}

    def mount_home(parent, state):
        frame = tk.Frame(parent)
        home_frame_holder["frame"] = frame
        return frame

    router.register(ScreenId.HOME, mount_home)
    router.navigate(ScreenId.HOME)

    with pytest.raises(UnregisteredScreenError):
        router.navigate(ScreenId.PLAYER)

    assert router.current_screen_id == ScreenId.HOME
    assert home_frame_holder["frame"].winfo_exists()
