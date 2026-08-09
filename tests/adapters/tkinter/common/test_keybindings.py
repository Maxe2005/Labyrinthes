import tkinter as tk

import pytest

from labyrinthes.adapters.tkinter.common.keybindings import (
    KEYBINDINGS,
    Keybinding,
    bind_shortcut,
    keybinding,
)


def test_every_action_id_in_the_table_is_unique():
    action_ids = [kb.action_id for kb in KEYBINDINGS]
    assert len(action_ids) == len(set(action_ids))


def test_every_key_in_the_table_is_unique_case_insensitively():
    keys = [kb.key.lower() for kb in KEYBINDINGS]
    assert len(keys) == len(set(keys))


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
