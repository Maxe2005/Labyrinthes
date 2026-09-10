from labyrinthes.adapters.tkinter.common.tokens import Theme
from labyrinthes.adapters.tkinter.player.generate_random_dialog import GenerateRandomDialog
from labyrinthes.domain.maze_size_bounds import MazeSizeBounds
from labyrinthes.domain.position import Position

_BOUNDS = MazeSizeBounds(min_columns=3, max_columns=50, min_rows=3, max_rows=35)


def _confirm_stub():
    calls = []

    def on_confirm(width, height, position):
        calls.append((width, height, position))

    return on_confirm, calls


def _set_field(dialog, key, text):
    entry = dialog._entries[key]
    entry.delete(0, "end")
    entry.insert(0, text)


def _dialog(tk_root, on_confirm, bounds=_BOUNDS):
    return GenerateRandomDialog(tk_root, theme=Theme.LIGHT, bounds=bounds, on_confirm=on_confirm)


def test_cold_open_prefills_valid_defaults_with_no_inline_errors(tk_root):
    on_confirm, _ = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm)

    assert dialog._entries["columns"].get() == "3"
    assert dialog._entries["rows"].get() == "3"
    assert dialog._entries["start_col"].get() == "0"
    assert dialog._entries["start_row"].get() == "0"
    assert all(label.cget("text") == "" for label in dialog._error_labels.values())


def test_columns_below_the_minimum_shows_inline_error_and_blocks_generate(tk_root):
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm)
    _set_field(dialog, "columns", "2")

    dialog._on_generate_clicked()

    assert dialog._error_labels["columns"].cget("text") == "Columns must be between 3 and 50."
    assert calls == []
    assert dialog.winfo_exists()


def test_columns_above_the_maximum_shows_inline_error_and_blocks_generate(tk_root):
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm)
    _set_field(dialog, "columns", "99")

    dialog._on_generate_clicked()

    assert dialog._error_labels["columns"].cget("text") == "Columns must be between 3 and 50."
    assert calls == []


def test_non_numeric_field_shows_inline_error_and_blocks_generate(tk_root):
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm)
    _set_field(dialog, "rows", "abc")

    dialog._on_generate_clicked()

    assert dialog._error_labels["rows"].cget("text") == "Enter a whole number."
    assert calls == []


def test_start_position_outside_the_entered_grid_shows_inline_error(tk_root):
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm)
    _set_field(dialog, "columns", "10")
    _set_field(dialog, "rows", "8")
    _set_field(dialog, "start_col", "15")

    dialog._on_generate_clicked()

    assert dialog._error_labels["start_col"].cget("text") == "Start column must be between 0 and 9."
    assert calls == []


def test_field_changed_revalidates_all_four_fields_live(tk_root):
    # Cross-field validation: changing columns re-checks start_col's
    # bounds too, not just its own field (Design Notes).
    on_confirm, _ = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm)
    _set_field(dialog, "columns", "10")
    _set_field(dialog, "rows", "8")
    _set_field(dialog, "start_col", "9")

    dialog._on_field_changed()
    assert dialog._error_labels["start_col"].cget("text") == ""

    _set_field(dialog, "columns", "5")
    dialog._on_field_changed()

    assert dialog._error_labels["start_col"].cget("text") == "Start column must be between 0 and 4."


def test_valid_input_confirms_once_and_destroys_the_dialog(tk_root):
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm)
    _set_field(dialog, "columns", "10")
    _set_field(dialog, "rows", "8")
    _set_field(dialog, "start_col", "0")
    _set_field(dialog, "start_row", "0")

    dialog._on_generate_clicked()

    assert calls == [(10, 8, Position(row=0, col=0))]
    assert not dialog.winfo_exists()


def test_cancel_destroys_the_dialog_without_confirming(tk_root):
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm)

    dialog._on_cancel()

    assert calls == []
    assert not dialog.winfo_exists()


def test_escape_binding_is_registered(tk_root):
    on_confirm, _ = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm)

    assert dialog.bind("<Escape>") != ""


def test_fields_are_wired_to_a_field_navigator_ending_at_the_generate_button(tk_root):
    # `tk_root` is withdrawn (unreliable real X11 KeyPress synthesis, per
    # this suite's convention) -- assert the wiring and binding registration
    # here, and exercise `FieldNavigator`'s actual step/boundary behavior
    # directly in `test_field_navigation.py`.
    on_confirm, _ = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm)

    assert dialog._navigator._order == [
        dialog._entries["columns"],
        dialog._entries["rows"],
        dialog._entries["start_col"],
        dialog._entries["start_row"],
        dialog._generate_button,
    ]
    for entry in dialog._entries.values():
        for sequence in ("<Up>", "<Down>", "<Left>", "<Right>", "<Return>"):
            assert entry.bind(sequence) != ""


def test_every_entry_locally_consumes_n_before_the_global_generate_random_shortcut(tk_root):
    on_confirm, _ = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm)

    for entry in dialog._entries.values():
        assert entry.bind("<KeyPress-n>") != ""
        assert entry.bind("<KeyPress-N>") != ""


def test_defaults_are_read_from_the_given_bounds_not_hardcoded(tk_root):
    on_confirm, _ = _confirm_stub()
    custom_bounds = MazeSizeBounds(min_columns=5, max_columns=40, min_rows=4, max_rows=20)

    dialog = _dialog(tk_root, on_confirm, bounds=custom_bounds)

    assert dialog._entries["columns"].get() == "5"
    assert dialog._entries["rows"].get() == "4"


# -- regression: review finding on cross-field error masking -----------------


def test_a_non_numeric_rows_field_does_not_mask_an_out_of_bounds_columns_error(tk_root):
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm)
    _set_field(dialog, "columns", "99")  # out of bounds (max 50)
    _set_field(dialog, "rows", "abc")  # fails to parse

    dialog._on_generate_clicked()

    assert dialog._error_labels["columns"].cget("text") == "Columns must be between 3 and 50."
    assert dialog._error_labels["rows"].cget("text") == "Enter a whole number."
    assert calls == []


def test_a_non_numeric_columns_field_does_not_mask_an_out_of_bounds_rows_error(tk_root):
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm)
    _set_field(dialog, "columns", "abc")  # fails to parse
    _set_field(dialog, "rows", "99")  # out of bounds (max 35)

    dialog._on_generate_clicked()

    assert dialog._error_labels["columns"].cget("text") == "Enter a whole number."
    assert dialog._error_labels["rows"].cget("text") == "Rows must be between 3 and 35."
    assert calls == []


def test_a_non_numeric_start_row_does_not_mask_an_out_of_grid_start_column_error(tk_root):
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm)
    _set_field(dialog, "columns", "10")
    _set_field(dialog, "rows", "8")
    _set_field(dialog, "start_col", "15")  # out of the 10-wide grid
    _set_field(dialog, "start_row", "abc")  # fails to parse

    dialog._on_generate_clicked()

    assert dialog._error_labels["start_col"].cget("text") == "Start column must be between 0 and 9."
    assert dialog._error_labels["start_row"].cget("text") == "Enter a whole number."
    assert calls == []
