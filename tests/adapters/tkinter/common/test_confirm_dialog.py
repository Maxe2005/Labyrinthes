import tkinter as tk

from labyrinthes.adapters.tkinter.common.confirm_dialog import ConfirmDialog
from labyrinthes.adapters.tkinter.common.pill_btn import PillButton
from labyrinthes.adapters.tkinter.common.tokens import Theme, colors_for


def _all_label_texts(widget: tk.Widget) -> list[str]:
    texts = []
    for child in widget.winfo_children():
        if isinstance(child, tk.Label):
            texts.append(child.cget("text"))
        texts.extend(_all_label_texts(child))
    return texts


def _pill_labels(dialog: ConfirmDialog) -> set[str]:
    pills = _find_all(dialog, PillButton)
    return {pill._label.cget("text") for pill in pills}


def _find_all(widget: tk.Widget, widget_type: type) -> list:
    found = []
    for child in widget.winfo_children():
        if isinstance(child, widget_type):
            found.append(child)
        found.extend(_find_all(child, widget_type))
    return found


def test_is_a_toplevel_with_the_message_and_default_pills(tk_root):
    dialog = ConfirmDialog(tk_root, theme=Theme.LIGHT, message="Restart the run?")
    try:
        assert isinstance(dialog, tk.Toplevel)
        assert dialog.title() == "Confirm"
        assert dialog.cget("background") == colors_for(Theme.LIGHT).window
        assert "Restart the run?" in _all_label_texts(dialog)
        assert _pill_labels(dialog) == {"Confirm", "Cancel"}
    finally:
        dialog.destroy()


def test_is_non_modal(tk_root):
    dialog = ConfirmDialog(tk_root, theme=Theme.LIGHT, message="Restart the run?")
    try:
        assert dialog.grab_status() is None
    finally:
        dialog.destroy()


def test_confirm_pill_invokes_on_confirm_and_destroys(tk_root):
    calls = []
    dialog = ConfirmDialog(
        tk_root,
        theme=Theme.LIGHT,
        message="Restart the run?",
        on_confirm=lambda: calls.append("confirmed"),
    )

    dialog._on_confirm_clicked()

    assert calls == ["confirmed"]
    assert not dialog.winfo_exists()


def test_cancel_pill_destroys_without_on_confirm(tk_root):
    calls = []
    dialog = ConfirmDialog(
        tk_root,
        theme=Theme.LIGHT,
        message="Restart the run?",
        on_confirm=lambda: calls.append("confirmed"),
    )

    dialog._on_cancel_clicked()

    assert calls == []
    assert not dialog.winfo_exists()


def test_return_binding_confirms_and_escape_cancels(tk_root):
    confirm_calls = []
    cancel_calls = []
    dialog = ConfirmDialog(
        tk_root,
        theme=Theme.LIGHT,
        message="Restart the run?",
        on_confirm=lambda: confirm_calls.append("confirmed"),
        on_close=lambda: cancel_calls.append("closed"),
    )
    dialog._on_confirm_clicked()
    assert confirm_calls == ["confirmed"]
    assert cancel_calls == ["closed"]
    assert not dialog.winfo_exists()

    dialog = ConfirmDialog(
        tk_root,
        theme=Theme.LIGHT,
        message="Restart the run?",
        on_confirm=lambda: confirm_calls.append("confirmed"),
        on_close=lambda: cancel_calls.append("closed"),
    )
    dialog._on_cancel_clicked()
    assert confirm_calls == ["confirmed"]
    assert cancel_calls == ["closed", "closed"]
    assert not dialog.winfo_exists()


def test_escape_binding_and_wm_delete_protocol_are_registered(tk_root):
    dialog = ConfirmDialog(tk_root, theme=Theme.LIGHT, message="Restart the run?")
    try:
        assert dialog.bind("<Escape>") != ""
        assert dialog.bind("<Return>") != ""
        assert dialog.protocol("WM_DELETE_WINDOW") != ""
    finally:
        dialog.destroy()


def test_on_close_is_invoked_on_every_close_path(tk_root):
    for close in ("confirm", "cancel"):
        close_calls = []
        dialog = ConfirmDialog(
            tk_root,
            theme=Theme.LIGHT,
            message="Restart the run?",
            on_close=lambda calls=close_calls: calls.append("closed"),
        )
        if close == "confirm":
            dialog._on_confirm_clicked()
        else:
            dialog._on_cancel_clicked()
        assert close_calls == ["closed"]
        assert not dialog.winfo_exists()


def test_on_close_is_skipped_when_none(tk_root):
    dialog = ConfirmDialog(tk_root, theme=Theme.LIGHT, message="Restart the run?")
    dialog._on_confirm_clicked()
    assert not dialog.winfo_exists()


def test_cancel_label_none_renders_no_cancel_pill(tk_root):
    dialog = ConfirmDialog(
        tk_root,
        theme=Theme.LIGHT,
        message="Restart the run?",
        cancel_label=None,
    )
    try:
        assert _pill_labels(dialog) == {"Confirm"}
    finally:
        dialog.destroy()


def test_alert_mode_dismisses_without_invoking_anything(tk_root):
    confirm_calls = []
    close_calls = []
    dialog = ConfirmDialog(
        tk_root,
        theme=Theme.LIGHT,
        message="That's not a valid maze number.",
        on_confirm=None,
        confirm_label="OK",
        cancel_label=None,
        on_close=lambda: close_calls.append("closed"),
    )

    assert _pill_labels(dialog) == {"OK"}
    dialog._on_confirm_clicked()

    assert confirm_calls == []
    assert close_calls == ["closed"]
    assert not dialog.winfo_exists()
