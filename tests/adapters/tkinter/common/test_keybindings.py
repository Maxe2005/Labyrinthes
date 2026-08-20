import tkinter as tk

import pytest

from labyrinthes.adapters.tkinter.common.keybindings import (
    KEYBINDINGS,
    Keybinding,
    bind_shortcut,
    keybinding,
)
from labyrinthes.adapters.tkinter.common.navigation import ScreenId


def test_every_action_id_in_the_table_is_unique():
    action_ids = [kb.action_id for kb in KEYBINDINGS]
    assert len(action_ids) == len(set(action_ids))


def test_every_key_in_the_table_is_unique_case_insensitively():
    # Keys are unique *within* each scope group, not globally (Story 3.2):
    # `scope=None` entries are one group, each explicit `ScreenId` scope is
    # its own separate group -- e.g. Home's 'b' (open_builder, scope=None)
    # and Builder's 'b' (break_wall, scope=BUILDER) share a key but never
    # collide, since Home and Builder are never mounted simultaneously.
    by_scope: dict[object, list[str]] = {}
    for kb in KEYBINDINGS:
        by_scope.setdefault(kb.scope, []).append(kb.key.lower())

    for scope, keys in by_scope.items():
        assert len(keys) == len(set(keys)), f"duplicate key(s) in scope {scope!r}: {keys}"


def test_display_is_the_uppercased_key():
    kb = Keybinding("open_builder", "Open Builder", "b")

    assert kb.display == "B"


def test_event_is_the_tk_keypress_sequence_for_the_key():
    kb = Keybinding("open_builder", "Open Builder", "b")

    assert kb.event == "<KeyPress-b>"


def test_keybinding_lookup_returns_the_matching_entry():
    kb = keybinding("open_builder")

    assert kb.action_id == "open_builder"
    assert kb.label == "Open Builder"
    assert kb.key == "b"


def test_keybinding_lookup_raises_key_error_for_an_unknown_action_id():
    with pytest.raises(KeyError):
        keybinding("not_a_real_action")


def test_bind_shortcut_registers_the_key_sequence_globally(tk_root):
    kb = keybinding("open_builder")

    bind_shortcut(tk_root, kb, lambda: None)

    assert tk_root.bind_all(kb.event) != ""


def test_bind_shortcut_also_registers_the_uppercase_keysym(tk_root):
    # X11 delivers Shift+B or a CapsLock-typed "b" as the keysym "B", not
    # "b" -- the printed kbd-tag is always uppercase, so the shortcut must
    # fire under that keysym too, not only the lowercase one `.event` names.
    kb = keybinding("open_builder")

    bind_shortcut(tk_root, kb, lambda: None)

    assert tk_root.bind_all(f"<KeyPress-{kb.key.upper()}>") != ""


def test_bind_shortcut_returned_handler_invokes_the_callback_directly(tk_root):
    calls = []
    kb = keybinding("open_player")

    handler = bind_shortcut(tk_root, kb, lambda: calls.append(1))
    # `tk_root` is withdrawn, so real X11 key-press synthesis isn't
    # reliable; invoke the returned handler directly (mirrors every other
    # `common/` widget's `_on_click()` test convention).
    handler()

    assert calls == [1]


def test_destroying_the_widget_unregisters_the_bind_all_shortcut(tk_root):
    frame = tk.Frame(tk_root)
    kb = keybinding("open_builder")

    bind_shortcut(frame, kb, lambda: None)
    assert tk_root.bind_all(kb.event) != ""

    frame.destroy()
    tk_root.update()

    assert tk_root.bind_all(kb.event) == ""


def test_a_fresh_registration_for_the_same_key_survives_an_older_widgets_destroy(tk_root):
    # Reproduces `Router.navigate()`'s new-before-old teardown order (e.g.
    # Story 1.9's theme toggle re-navigating the current screen): a new
    # widget registers the same key *before* the old widget -- which
    # registered it first -- is destroyed. The old widget's <Destroy>
    # cleanup must not clobber the newer, still-live registration.
    calls = []
    kb = keybinding("open_builder")
    old_widget = tk.Frame(tk_root)
    bind_shortcut(old_widget, kb, lambda: calls.append("old"))

    new_widget = tk.Frame(tk_root)
    new_handler = bind_shortcut(new_widget, kb, lambda: calls.append("new"))

    old_widget.destroy()
    tk_root.update()

    assert tk_root.bind_all(kb.event) != ""
    new_handler()
    assert calls == ["new"]


def test_movement_action_ids_are_registered_in_the_table():
    action_ids = {kb.action_id for kb in KEYBINDINGS}
    assert {"move_up", "move_down", "move_left", "move_right"} <= action_ids


def test_movement_keybindings_use_the_real_tk_arrow_keysyms():
    assert keybinding("move_up").key == "Up"
    assert keybinding("move_down").key == "Down"
    assert keybinding("move_left").key == "Left"
    assert keybinding("move_right").key == "Right"
    assert keybinding("move_up").event == "<KeyPress-Up>"


def test_toggle_movement_mode_is_registered_on_the_m_keysym():
    assert keybinding("toggle_movement_mode").action_id == "toggle_movement_mode"
    assert keybinding("toggle_movement_mode").label == "Toggle movement mode"
    assert keybinding("toggle_movement_mode").key == "m"
    assert keybinding("toggle_movement_mode").display == "M"
    assert keybinding("toggle_movement_mode").event == "<KeyPress-m>"


def test_toggle_movement_mode_key_does_not_collide_with_any_other_key():
    keys = [kb.key.lower() for kb in KEYBINDINGS]
    assert keys.count("m") == 1


def test_toggle_hard_mode_is_registered_on_the_h_keysym():
    assert keybinding("toggle_hard_mode").action_id == "toggle_hard_mode"
    assert keybinding("toggle_hard_mode").label == "Toggle HARD mode"
    assert keybinding("toggle_hard_mode").key == "h"
    assert keybinding("toggle_hard_mode").display == "H"
    assert keybinding("toggle_hard_mode").event == "<KeyPress-h>"


def test_toggle_hard_mode_key_does_not_collide_with_any_other_key():
    keys = [kb.key.lower() for kb in KEYBINDINGS]
    assert keys.count("h") == 1


def test_set_entry_keybinding_is_registered_on_the_e_keysym_in_builder_scope():
    kb = keybinding("set_entry")

    assert kb.label == "Set Entry"
    assert kb.key == "e"
    assert kb.display == "E"
    assert kb.event == "<KeyPress-e>"
    assert kb.scope is ScreenId.BUILDER


def test_set_exit_keybinding_is_registered_on_the_x_keysym_in_builder_scope():
    kb = keybinding("set_exit")

    assert kb.label == "Set Exit"
    assert kb.key == "x"
    assert kb.display == "X"
    assert kb.event == "<KeyPress-x>"
    assert kb.scope is ScreenId.BUILDER


def test_set_entry_and_set_exit_keys_are_unique_within_the_builder_scope():
    builder_keys = [kb.key.lower() for kb in KEYBINDINGS if kb.scope is ScreenId.BUILDER]
    assert "e" in builder_keys
    assert "x" in builder_keys
    assert len(builder_keys) == len(set(builder_keys))


def test_test_in_player_keybinding_is_registered_on_the_t_keysym_in_builder_scope():
    kb = keybinding("test_in_player")

    assert kb.label == "Test in Player"
    assert kb.key == "t"
    assert kb.display == "T"
    assert kb.event == "<KeyPress-t>"
    assert kb.scope is ScreenId.BUILDER


def test_bind_shortcut_does_not_register_an_uppercase_variant_for_a_multi_char_keysym(tk_root):
    # Regression: an unguarded `f"<KeyPress-{kb.key.upper()}>"` on a
    # multi-char keysym like "Up" produces "<KeyPress-UP>", which is not a
    # valid Tk keysym -- `bind_all()` would raise `TclError: bad event
    # type or keysym "UP"`. `bind_shortcut` must not attempt it at all.
    kb = keybinding("move_up")

    bind_shortcut(tk_root, kb, lambda: None)  # must not raise

    assert tk_root.bind_all("<KeyPress-Up>") != ""
    assert tk_root.bind_all("<KeyPress-UP>") == ""


def test_bind_shortcut_for_a_multi_char_keysym_still_invokes_its_callback(tk_root):
    calls = []
    kb = keybinding("move_left")

    handler = bind_shortcut(tk_root, kb, lambda: calls.append(1))
    handler()

    assert calls == [1]


def test_destroying_the_newer_widget_still_unregisters_the_shortcut(tk_root):
    kb = keybinding("open_builder")
    old_widget = tk.Frame(tk_root)
    bind_shortcut(old_widget, kb, lambda: None)

    new_widget = tk.Frame(tk_root)
    bind_shortcut(new_widget, kb, lambda: None)

    old_widget.destroy()
    tk_root.update()
    new_widget.destroy()
    tk_root.update()

    assert tk_root.bind_all(kb.event) == ""
