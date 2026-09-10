import tkinter as tk

import pytest

from labyrinthes.adapters.tkinter.common.new_maze_dialog import NewMazeDialog
from labyrinthes.adapters.tkinter.common.tokens import Theme
from labyrinthes.application.settings_keys import (
    MAZE_MAX_COLUMNS,
    MAZE_MAX_ROWS,
    MAZE_MIN_COLUMNS,
    MAZE_MIN_ROWS,
)
from labyrinthes.application.settings_repository import SettingsScope
from labyrinthes.domain.maze import MazeKind
from labyrinthes.domain.position import Position


def _confirm_stub():
    calls = []

    def on_confirm(maze):
        calls.append(maze)

    return on_confirm, calls


def _set_field(dialog, key, text):
    entry = dialog._entries[key]
    entry.delete(0, "end")
    entry.insert(0, text)


def _dialog(tk_root, on_confirm, settings_repository):
    return NewMazeDialog(
        tk_root,
        theme=Theme.LIGHT,
        settings_repository=settings_repository,
        on_confirm=on_confirm,
    )


def test_cold_open_prefills_the_minimum_bounds_with_no_inline_errors(
    tk_root, fake_settings_repository
):
    on_confirm, _ = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm, fake_settings_repository)

    assert dialog._entries["columns"].get() == "3"
    assert dialog._entries["rows"].get() == "3"
    assert all(label.cget("text") == "" for label in dialog._error_labels.values())


def test_columns_below_the_minimum_shows_inline_error_and_blocks_create(
    tk_root, fake_settings_repository
):
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm, fake_settings_repository)
    _set_field(dialog, "columns", "2")

    dialog._on_confirm_clicked()

    assert dialog._error_labels["columns"].cget("text") == "Columns must be between 3 and 50."
    assert calls == []
    assert dialog.winfo_exists()


def test_columns_above_the_maximum_shows_inline_error_and_blocks_create(
    tk_root, fake_settings_repository
):
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm, fake_settings_repository)
    _set_field(dialog, "columns", "99")

    dialog._on_confirm_clicked()

    assert dialog._error_labels["columns"].cget("text") == "Columns must be between 3 and 50."
    assert calls == []


def test_rows_below_the_minimum_shows_inline_error_and_blocks_create(
    tk_root, fake_settings_repository
):
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm, fake_settings_repository)
    _set_field(dialog, "rows", "2")

    dialog._on_confirm_clicked()

    assert dialog._error_labels["rows"].cget("text") == "Rows must be between 3 and 35."
    assert calls == []


def test_rows_above_the_maximum_shows_inline_error_and_blocks_create(
    tk_root, fake_settings_repository
):
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm, fake_settings_repository)
    _set_field(dialog, "rows", "99")

    dialog._on_confirm_clicked()

    assert dialog._error_labels["rows"].cget("text") == "Rows must be between 3 and 35."
    assert calls == []


def test_non_numeric_field_shows_inline_error_and_blocks_create(tk_root, fake_settings_repository):
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm, fake_settings_repository)
    _set_field(dialog, "columns", "abc")

    dialog._on_confirm_clicked()

    assert dialog._error_labels["columns"].cget("text") == "Enter a whole number."
    assert calls == []


def test_create_button_has_no_disabled_state_gate(tk_root, fake_settings_repository):
    # The spec explicitly rules out a disabled/greyed-out Create button --
    # errors stay visible instead, with no widget state change. `PillButton`
    # is a plain `tk.Frame` with no Tk `-state` option at all, so there is
    # structurally no way to grey it out -- confirmed by `cget("state")`
    # itself raising rather than reporting "disabled".
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm, fake_settings_repository)
    _set_field(dialog, "columns", "2")
    dialog._on_field_changed()

    with pytest.raises(tk.TclError):
        dialog._confirm_button.cget("state")
    assert calls == []


def test_valid_dimensions_create_a_sketch_maze_and_confirm_once(tk_root, fake_settings_repository):
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm, fake_settings_repository)
    _set_field(dialog, "columns", "20")
    _set_field(dialog, "rows", "15")

    dialog._on_confirm_clicked()

    assert len(calls) == 1
    maze = calls[0]
    assert maze.kind is MazeKind.SKETCH
    assert maze.id is None
    assert maze.entry == Position(row=0, col=0)
    assert maze.exit == Position(row=14, col=19)
    assert maze.grid.width == 20
    assert maze.grid.height == 15
    assert not dialog.winfo_exists()


def test_cancel_destroys_the_dialog_without_confirming(tk_root, fake_settings_repository):
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm, fake_settings_repository)

    dialog._on_cancel()

    assert calls == []
    assert not dialog.winfo_exists()


def test_escape_binding_is_registered(tk_root, fake_settings_repository):
    on_confirm, _ = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm, fake_settings_repository)

    assert dialog.bind("<Escape>") != ""


def test_fields_are_wired_to_a_field_navigator_ending_at_the_create_button(
    tk_root, fake_settings_repository
):
    # `tk_root` is withdrawn (unreliable real X11 KeyPress synthesis, per
    # this suite's convention) -- assert the wiring and binding registration
    # here, and exercise `FieldNavigator`'s actual step/boundary behavior
    # directly in `test_field_navigation.py`.
    on_confirm, _ = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm, fake_settings_repository)

    assert dialog._navigator._order == [
        dialog._entries["columns"],
        dialog._entries["rows"],
        dialog._confirm_button,
    ]
    for entry in dialog._entries.values():
        for sequence in ("<Up>", "<Down>", "<Left>", "<Right>", "<Return>"):
            assert entry.bind(sequence) != ""


def test_bounds_are_read_from_settings_not_hardcoded(tk_root, fake_settings_repository):
    fake_settings_repository.set(SettingsScope.SHARED, MAZE_MIN_COLUMNS, 5)
    fake_settings_repository.set(SettingsScope.SHARED, MAZE_MAX_COLUMNS, 40)
    fake_settings_repository.set(SettingsScope.SHARED, MAZE_MIN_ROWS, 4)
    fake_settings_repository.set(SettingsScope.SHARED, MAZE_MAX_ROWS, 20)
    on_confirm, _ = _confirm_stub()

    dialog = _dialog(tk_root, on_confirm, fake_settings_repository)

    assert dialog._entries["columns"].get() == "5"
    assert dialog._entries["rows"].get() == "4"

    _set_field(dialog, "columns", "45")
    dialog._on_field_changed()
    assert dialog._error_labels["columns"].cget("text") == "Columns must be between 5 and 40."


def test_a_non_numeric_rows_field_does_not_mask_an_out_of_bounds_columns_error(
    tk_root, fake_settings_repository
):
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm, fake_settings_repository)
    _set_field(dialog, "columns", "99")  # out of bounds (max 50)
    _set_field(dialog, "rows", "abc")  # fails to parse

    dialog._on_confirm_clicked()

    assert dialog._error_labels["columns"].cget("text") == "Columns must be between 3 and 50."
    assert dialog._error_labels["rows"].cget("text") == "Enter a whole number."
    assert calls == []


def test_every_entry_locally_consumes_b_c_p_before_the_global_home_shortcuts(
    tk_root, fake_settings_repository
):
    # `NewMazeDialog` is opened from Home while Home's frame -- and its
    # `open_builder`/`open_new_maze`/`open_player` ("b"/"c"/"p") global
    # `bind_all()` shortcuts -- are still live. Without a local guard,
    # typing any of those letters into a field (e.g. the "abc" non-numeric
    # scenario) would stack a second dialog or navigate away mid-edit.
    # Mirrors `GenerateRandomDialog`'s identical `<KeyPress-n>` guard test.
    on_confirm, _ = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm, fake_settings_repository)

    for entry in dialog._entries.values():
        for letter in ("b", "B", "c", "C", "p", "P"):
            assert entry.bind(f"<KeyPress-{letter}>") != ""
