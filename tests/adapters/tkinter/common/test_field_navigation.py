import tkinter as tk

from labyrinthes.adapters.tkinter.common.field_navigation import FieldNavigator, is_at_text_boundary


def _spy(widget):
    calls = []
    widget.focus_set = lambda: calls.append(widget)
    return calls


# -- FieldNavigator.focus_step ------------------------------------------------
# `tk_root` is withdrawn (unreliable real focus/X11 KeyPress synthesis, per
# this suite's convention) -- exercise `focus_step` directly and assert via a
# `focus_set` spy rather than reading back `focus_get()`.


def test_focus_step_moves_forward_to_the_next_field(tk_root):
    e1, e2, e3 = tk.Entry(tk_root), tk.Entry(tk_root), tk.Entry(tk_root)
    button = tk.Frame(tk_root)
    navigator = FieldNavigator([e1, e2, e3], button)
    calls = _spy(e2)

    navigator.focus_step(0, +1)

    assert calls == [e2]


def test_focus_step_moves_backward_to_the_previous_field(tk_root):
    e1, e2, e3 = tk.Entry(tk_root), tk.Entry(tk_root), tk.Entry(tk_root)
    button = tk.Frame(tk_root)
    navigator = FieldNavigator([e1, e2, e3], button)
    calls = _spy(e2)

    navigator.focus_step(2, -1)

    assert calls == [e2]


def test_focus_step_up_from_the_first_field_is_a_no_op(tk_root):
    e1, e2 = tk.Entry(tk_root), tk.Entry(tk_root)
    button = tk.Frame(tk_root)
    navigator = FieldNavigator([e1, e2], button)
    calls = _spy(e1)

    navigator.focus_step(0, -1)

    assert calls == []


def test_focus_step_down_from_the_last_field_reaches_the_confirm_widget(tk_root):
    e1, e2 = tk.Entry(tk_root), tk.Entry(tk_root)
    button = tk.Frame(tk_root)
    navigator = FieldNavigator([e1, e2], button)
    calls = _spy(button)

    navigator.focus_step(1, +1)

    assert calls == [button]


def test_focus_step_past_the_confirm_widget_is_a_no_op(tk_root):
    e1 = tk.Entry(tk_root)
    button = tk.Frame(tk_root)
    navigator = FieldNavigator([e1], button)
    calls = _spy(button)

    navigator.focus_step(1, +1)  # index 1 is already the confirm widget

    assert calls == []


# -- is_at_text_boundary -------------------------------------------------


def test_is_at_start_boundary_when_cursor_is_at_position_zero(tk_root):
    entry = tk.Entry(tk_root)
    entry.insert(0, "42")
    entry.icursor(0)

    assert is_at_text_boundary(entry, -1) is True
    assert is_at_text_boundary(entry, +1) is False


def test_is_at_end_boundary_when_cursor_is_after_the_last_character(tk_root):
    entry = tk.Entry(tk_root)
    entry.insert(0, "42")
    entry.icursor("end")

    assert is_at_text_boundary(entry, +1) is True
    assert is_at_text_boundary(entry, -1) is False


def test_is_at_neither_boundary_when_the_cursor_sits_mid_text(tk_root):
    entry = tk.Entry(tk_root)
    entry.insert(0, "123")
    entry.icursor(1)

    assert is_at_text_boundary(entry, -1) is False
    assert is_at_text_boundary(entry, +1) is False


def test_a_pending_selection_never_counts_as_at_the_boundary(tk_root):
    # Left/Right on a selection should collapse it via Entry's own class
    # binding, not hop fields -- even when the selection happens to span
    # from position 0 to the end.
    entry = tk.Entry(tk_root)
    entry.insert(0, "42")
    entry.select_range(0, "end")
    entry.icursor(0)

    assert is_at_text_boundary(entry, -1) is False
    entry.icursor("end")
    assert is_at_text_boundary(entry, +1) is False


# -- bindings --------------------------------------------------------------


def test_up_down_left_right_and_return_are_bound_on_every_field(tk_root):
    e1, e2 = tk.Entry(tk_root), tk.Entry(tk_root)
    button = tk.Frame(tk_root)

    FieldNavigator([e1, e2], button)

    for entry in (e1, e2):
        for sequence in ("<Up>", "<Down>", "<Left>", "<Right>", "<Return>"):
            assert entry.bind(sequence) != ""


def test_the_confirm_widget_itself_is_left_unbound(tk_root):
    # Navigation *onto* the confirm widget is handled by the last field's
    # Down/Return; navigation *off* it (e.g. back up) is out of scope here --
    # it stays reachable via Tab like any other focusable widget.
    e1 = tk.Entry(tk_root)
    button = tk.Frame(tk_root)

    FieldNavigator([e1], button)

    for sequence in ("<Up>", "<Down>", "<Left>", "<Right>", "<Return>"):
        assert button.bind(sequence) == ""
