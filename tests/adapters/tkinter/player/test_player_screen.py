import tkinter as tk

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


def test_mount_returns_a_frame_parented_under_the_given_parent(tk_root):
    frame = mount(tk_root, None)

    assert isinstance(frame, tk.Frame)
    assert frame.master is tk_root


def test_mount_accepts_a_real_maze_as_state_without_raising(tk_root):
    frame = mount(tk_root, _maze())

    assert isinstance(frame, tk.Frame)
