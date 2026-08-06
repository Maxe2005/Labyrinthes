import tkinter as tk

from labyrinthes.adapters.tkinter.builder.screen import mount


def test_mount_returns_a_frame_parented_under_the_given_parent(tk_root):
    frame = mount(tk_root, None)

    assert isinstance(frame, tk.Frame)
    assert frame.master is tk_root
