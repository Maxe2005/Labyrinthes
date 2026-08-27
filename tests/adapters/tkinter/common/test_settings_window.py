import re
import tkinter as tk

from labyrinthes.adapters.tkinter.common.settings_window import SettingsWindow
from labyrinthes.adapters.tkinter.common.tokens import Theme
from labyrinthes.application.confirmation_settings import (
    read_confirm_level_change,
    read_confirm_redefine_marker,
    read_confirm_switch_maze,
    write_confirm_invalid_input,
    write_confirm_restart,
)

_CONFIRMATION_ROW_TEXTS = {
    "Confirm before switching/restarting mazes",
    "Confirm before restarting",
    "Confirm before changing level",
    "Alert me about invalid input",
    "Confirm before redefining an entry/exit",
}


def _all_widget_texts(widget: tk.Widget) -> list[str]:
    texts = []
    for child in widget.winfo_children():
        if isinstance(child, (tk.Label, tk.Button)):
            texts.append(child.cget("text"))
        texts.extend(_all_widget_texts(child))
    return texts


def _find_all(widget: tk.Widget, widget_type: type) -> list:
    found = []
    for child in widget.winfo_children():
        if isinstance(child, widget_type):
            found.append(child)
        found.extend(_find_all(child, widget_type))
    return found


def _window(tk_root, repository):
    return SettingsWindow(tk_root, theme=Theme.LIGHT, settings_repository=repository)


def test_settings_window_is_a_toplevel(tk_root, fake_settings_repository):
    window = _window(tk_root, fake_settings_repository)
    try:
        assert isinstance(window, tk.Toplevel)
    finally:
        window.destroy()


def test_center_on_screen_requests_a_geometry_string_centered_on_the_screen(
    tk_root, fake_settings_repository
):
    # Asserts on the exact `.geometry()` string `_center_on_screen()`
    # requests, not on `winfo_x()`/`winfo_y()` after the fact -- whether
    # that request is actually *honored* is up to the platform's window
    # manager (some ignore an app's own placement requests entirely), which
    # is outside this codebase's control and not what this story tests.
    window = _window(tk_root, fake_settings_repository)
    try:
        calls = []
        window.geometry = calls.append

        window._center_on_screen()

        assert len(calls) == 1
        match = re.fullmatch(r"\+(\d+)\+(\d+)", calls[0])
        assert match is not None
        x, y = (int(group) for group in match.groups())
        width = window.winfo_width()
        height = window.winfo_height()
        assert x == (window.winfo_screenwidth() - width) // 2
        assert y == (window.winfo_screenheight() - height) // 2
    finally:
        window.destroy()


def test_settings_window_is_resizable_in_both_directions(tk_root, fake_settings_repository):
    window = _window(tk_root, fake_settings_repository)
    try:
        assert window.resizable() == (1, 1)
    finally:
        window.destroy()


def test_f11_toggles_this_windows_own_fullscreen_attribute(tk_root, fake_settings_repository):
    window = _window(tk_root, fake_settings_repository)
    try:
        calls = []
        window.attributes = lambda *args: calls.append(args)

        window._toggle_fullscreen()
        window._toggle_fullscreen()

        assert calls == [("-fullscreen", True), ("-fullscreen", False)]
    finally:
        window.destroy()


def test_f11_handler_returns_break_to_stop_the_roots_global_toggle(
    tk_root, fake_settings_repository
):
    # Tk checks a focused widget's own toplevel bindtag (this local `<F11>`
    # binding) before the shared `"all"` bindtag (the root's global
    # toggle) -- returning `"break"` here is what stops that scan from
    # ever reaching the root's binding while this window has focus.
    window = _window(tk_root, fake_settings_repository)
    try:
        window.attributes = lambda *args: None

        assert window._toggle_fullscreen() == "break"
    finally:
        window.destroy()


def test_settings_window_is_non_modal(tk_root, fake_settings_repository):
    window = _window(tk_root, fake_settings_repository)
    try:
        assert window.grab_status() is None
    finally:
        window.destroy()


def test_settings_window_opens_on_the_appearance_category_with_placeholder_content(
    tk_root, fake_settings_repository
):
    window = _window(tk_root, fake_settings_repository)
    try:
        texts = _all_widget_texts(window)
        assert "Appearance" in texts
        # Logo picker shows navigation buttons and current logo key
        assert "◀" in texts
        assert "▶" in texts
        assert "default" in texts
    finally:
        window.destroy()


def test_confirmation_category_is_present_in_the_nav(tk_root, fake_settings_repository):
    window = _window(tk_root, fake_settings_repository)
    try:
        assert "Confirmation" in _all_widget_texts(window)
    finally:
        window.destroy()


def test_selecting_confirmation_swaps_the_content_pane_to_five_toggle_rows_and_back(
    tk_root, fake_settings_repository
):
    window = _window(tk_root, fake_settings_repository)
    try:
        window._select_category("Confirmation")

        texts = set(window._confirmation_rows)
        assert texts == _CONFIRMATION_ROW_TEXTS

        window._select_category("Appearance")
        assert window._confirmation_rows == {}
        # Logo picker shows navigation buttons and current logo key
        texts = _all_widget_texts(window)
        assert "◀" in texts
        assert "▶" in texts
        assert "default" in texts
    finally:
        window.destroy()


def test_toggling_a_row_calls_the_matching_writer(tk_root, fake_settings_repository):
    window = _window(tk_root, fake_settings_repository)
    try:
        window._select_category("Confirmation")
        row = next(
            cb
            for cb in _find_all(window, tk.Checkbutton)
            if cb.cget("text") == "Confirm before switching/restarting mazes"
        )

        row.invoke()

        assert read_confirm_switch_maze(fake_settings_repository) is True
    finally:
        window.destroy()


def test_toggling_the_redefine_marker_row_calls_its_writer(tk_root, fake_settings_repository):
    window = _window(tk_root, fake_settings_repository)
    try:
        window._select_category("Confirmation")
        row = next(
            cb
            for cb in _find_all(window, tk.Checkbutton)
            if cb.cget("text") == "Confirm before redefining an entry/exit"
        )

        row.invoke()

        assert read_confirm_redefine_marker(fake_settings_repository) is False
    finally:
        window.destroy()


def test_a_stored_value_is_reflected_in_the_rows_initial_state(tk_root, fake_settings_repository):
    write_confirm_restart(fake_settings_repository, False)
    write_confirm_invalid_input(fake_settings_repository, False)
    window = _window(tk_root, fake_settings_repository)
    try:
        window._select_category("Confirmation")

        assert window._confirmation_rows["Confirm before switching/restarting mazes"].get() is False
        assert window._confirmation_rows["Confirm before restarting"].get() is False
        assert window._confirmation_rows["Confirm before changing level"].get() is False
        assert window._confirmation_rows["Alert me about invalid input"].get() is False
        assert window._confirmation_rows["Confirm before redefining an entry/exit"].get() is True
    finally:
        window.destroy()


def test_category_nav_is_keyboard_operable(tk_root, fake_settings_repository):
    window = _window(tk_root, fake_settings_repository)
    try:
        confirmation_label = next(
            label for label in _find_all(window, tk.Label) if label.cget("text") == "Confirmation"
        )
        assert confirmation_label.cget("takefocus") == 1
        assert confirmation_label.bind("<Return>") != ""
        assert confirmation_label.bind("<space>") != ""
        assert confirmation_label.bind("<Button-1>") != ""
    finally:
        window.destroy()


def test_persisting_a_toggle_then_reopening_the_window_reflects_the_stored_value(
    tk_root, fake_settings_repository
):
    window = _window(tk_root, fake_settings_repository)
    try:
        window._select_category("Confirmation")
        row = next(
            cb
            for cb in _find_all(window, tk.Checkbutton)
            if cb.cget("text") == "Confirm before changing level"
        )
        row.invoke()
    finally:
        window.destroy()

    reopened = _window(tk_root, fake_settings_repository)
    try:
        reopened._select_category("Confirmation")
        assert reopened._confirmation_rows["Confirm before changing level"].get() is True
        assert read_confirm_level_change(fake_settings_repository) is True
    finally:
        reopened.destroy()
