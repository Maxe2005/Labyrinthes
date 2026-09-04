from labyrinthes.adapters.tkinter.common.keybindings import bind_shortcut, keybinding
from labyrinthes.adapters.tkinter.common.tokens import Theme
from labyrinthes.adapters.tkinter.player.save_maze_dialog import SaveMazeDialog


def _confirm_stub():
    calls = []

    def on_confirm(name):
        calls.append(name)

    return on_confirm, calls


def _dialog(tk_root, on_confirm, existing_names=()):
    return SaveMazeDialog(
        tk_root, theme=Theme.LIGHT, existing_names=list(existing_names), on_confirm=on_confirm
    )


def _set_name(dialog, text):
    dialog._name_entry.delete(0, "end")
    dialog._name_entry.insert(0, text)


def test_saving_a_non_colliding_name_confirms_once_and_destroys_the_dialog(tk_root):
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm)
    _set_name(dialog, "forest")

    dialog._on_save_clicked()

    assert calls == ["forest"]
    assert not dialog.winfo_exists()


def test_empty_name_shows_inline_error_and_blocks_save(tk_root):
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm)
    _set_name(dialog, "")

    dialog._on_save_clicked()

    assert dialog._message_label.cget("text") == "Name is required."
    assert calls == []
    assert dialog.winfo_exists()


def test_name_with_a_forward_slash_shows_inline_error_and_blocks_save(tk_root):
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm)
    _set_name(dialog, "a/b")

    dialog._on_save_clicked()

    assert dialog._message_label.cget("text") == "Name must not contain a path separator."
    assert calls == []


def test_name_with_a_backslash_shows_inline_error_and_blocks_save(tk_root):
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm)
    _set_name(dialog, "a\\b")

    dialog._on_save_clicked()

    assert dialog._message_label.cget("text") == "Name must not contain a path separator."
    assert calls == []


def test_colliding_name_first_click_arms_and_warns_without_saving(tk_root):
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm, existing_names=["forest"])
    _set_name(dialog, "forest")

    dialog._on_save_clicked()

    assert calls == []
    assert dialog.winfo_exists()
    assert (
        dialog._message_label.cget("text")
        == "A maze named 'forest' already exists — Save again to overwrite it."
    )
    assert dialog._save_button._label.cget("text") == "Overwrite"


def test_colliding_name_second_click_unchanged_confirms_the_overwrite(tk_root):
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm, existing_names=["forest"])
    _set_name(dialog, "forest")
    dialog._on_save_clicked()  # first click: arms

    dialog._on_save_clicked()  # second click: confirms

    assert calls == ["forest"]
    assert not dialog.winfo_exists()


def test_editing_the_name_after_arming_resets_the_button_label(tk_root):
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm, existing_names=["forest"])
    _set_name(dialog, "forest")
    dialog._on_save_clicked()  # arms
    assert dialog._save_button._label.cget("text") == "Overwrite"

    _set_name(dialog, "forest2")
    dialog._on_name_changed()

    assert dialog._save_button._label.cget("text") == "Save"
    assert calls == []


def test_re_arming_after_an_edit_requires_a_fresh_second_click(tk_root):
    # Editing back to the exact same colliding name after an edit must not
    # carry the old arming forward -- it re-arms fresh rather than
    # confirming immediately.
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm, existing_names=["forest"])
    _set_name(dialog, "forest")
    dialog._on_save_clicked()  # arms
    _set_name(dialog, "forest2")
    dialog._on_name_changed()  # resets arming

    _set_name(dialog, "forest")
    dialog._on_save_clicked()  # re-arms, does not confirm yet

    assert calls == []
    assert dialog._save_button._label.cget("text") == "Overwrite"


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


def test_return_on_the_name_field_is_bound_to_trigger_save(tk_root):
    on_confirm, _ = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm)

    assert dialog._name_entry.bind("<Return>") != ""


def test_name_entry_has_no_local_keypress_s_guard(tk_root):
    # Story 4.12: the old per-dialog "s"/"S" `"break"` guards are deleted --
    # the centralized `bind_shortcut()` dispatch guard supersedes them (and
    # fixes the bug where a local "break" pre-empted the Entry class binding,
    # blocking "s"/"S" from ever being typed).
    on_confirm, _ = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm)

    assert dialog._name_entry.bind("<KeyPress-s>") == ""
    assert dialog._name_entry.bind("<KeyPress-S>") == ""


def test_typing_s_via_the_real_shortcut_handler_does_not_fire_save_while_the_name_entry_is_focused(
    tk_root,
):
    # The real `bind_shortcut()`-registered `save_maze` handler must not
    # invoke the confirm callback while `_name_entry` holds focus -- the
    # centralized focus-aware guard in `keybindings.py` is what prevents a
    # save-name that happens to contain "s" from reopening a second dialog.
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm)
    dialog._name_entry.update()
    dialog._name_entry.focus_force()
    dialog._name_entry.update()

    kb = keybinding("save_maze")
    handler = bind_shortcut(tk_root, kb, lambda: on_confirm("shortcut-fired"))
    handler()

    assert calls == []


# Story 2.4's `move_up`/`move_down`/`move_left`/`move_right` global
# shortcuts are deliberately *not* guarded with a per-key "break" binding
# here the way `save_maze`'s "s"/"S" guard above is: an instance-level
# "break" on the entry would stop Tk's bindtag scan before the `Entry`
# *class* binding (cursor movement/self-insert) ever runs, silently
# disabling the field's own arrow-key cursor navigation -- confirmed live.
# `GameplayScreen._on_move` guards itself instead by checking
# `self.focus_get()`; see `test_move_is_a_no_op_while_a_text_entry_holds_focus`
# in `test_gameplay/test_screen.py`.


def test_whitespace_only_name_is_rejected_as_required(tk_root):
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm)
    _set_name(dialog, "   ")

    dialog._on_save_clicked()

    assert dialog._message_label.cget("text") == "Name is required."
    assert calls == []


def test_leading_and_trailing_whitespace_is_stripped_before_confirming(tk_root):
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm)
    _set_name(dialog, "  forest  ")

    dialog._on_save_clicked()

    assert calls == ["forest"]


def test_trailing_whitespace_still_collides_with_the_stripped_existing_name(tk_root):
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm, existing_names=["forest"])
    _set_name(dialog, "forest ")

    dialog._on_save_clicked()

    assert calls == []
    assert dialog._save_button._label.cget("text") == "Overwrite"


def test_cursor_only_key_release_while_armed_does_not_reset_arming(tk_root):
    # A `<KeyRelease>` from a non-content key (e.g. an arrow key) fires
    # `_on_name_changed` too, but leaves the field's text unchanged --
    # arming must survive it, not force a third click.
    on_confirm, calls = _confirm_stub()
    dialog = _dialog(tk_root, on_confirm, existing_names=["forest"])
    _set_name(dialog, "forest")
    dialog._on_save_clicked()  # arms
    assert dialog._save_button._label.cget("text") == "Overwrite"

    dialog._on_name_changed()  # text unchanged -- e.g. an arrow-key release

    assert dialog._save_button._label.cget("text") == "Overwrite"
    # Regression: the overwrite warning message must survive it too, not
    # just the button label -- otherwise "Overwrite" is left with no
    # visible explanation of what it's about to overwrite.
    assert (
        dialog._message_label.cget("text")
        == "A maze named 'forest' already exists — Save again to overwrite it."
    )

    dialog._on_save_clicked()  # second click: confirms

    assert calls == ["forest"]


def test_dialog_destroys_itself_before_on_confirm_is_invoked(tk_root):
    # Regression: `on_confirm` typically triggers the owning widget's own
    # re-render (`GameplayScreen._build_save_zone()`, which destroys its
    # children including this dialog) -- so this dialog must already be
    # gone via its own `destroy()` by the time `on_confirm` runs, not rely
    # on the parent's rebuild to tear it down as a side effect.
    seen_dialog_exists = []

    def on_confirm(_name):
        seen_dialog_exists.append(dialog.winfo_exists())

    dialog = _dialog(tk_root, on_confirm)
    _set_name(dialog, "forest")

    dialog._on_save_clicked()

    assert seen_dialog_exists == [0]
