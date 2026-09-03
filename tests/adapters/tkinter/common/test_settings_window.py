import re
import tkinter as tk

import pytest

from labyrinthes.adapters.tkinter.common.settings_window import SettingsWindow
from labyrinthes.adapters.tkinter.common.tokens import Theme, colors_for
from labyrinthes.application.confirmation_settings import (
    read_confirm_level_change,
    read_confirm_redefine_marker,
    read_confirm_switch_maze,
    write_confirm_invalid_input,
    write_confirm_restart,
)
from labyrinthes.application.errors import SettingNotFoundError
from labyrinthes.application.settings_repository import SettingsScope
from labyrinthes.application.window_settings import (
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    MIN_WINDOW_WIDTH,
    read_window_size,
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


def _dimension_entry(container: tk.Widget, label_text: str) -> tk.Entry:
    """The `tk.Entry` in the same row as the `tk.Label` reading `label_text`."""
    for label in _find_all(container, tk.Label):
        if label.cget("text") == label_text:
            for sibling in label.master.winfo_children():
                if isinstance(sibling, tk.Entry):
                    return sibling
    raise AssertionError(f"No dimension field labeled {label_text!r}")


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


# -- Defaults: window size (Story 4.10 follow-up) -----------------------------


def test_defaults_category_shows_a_window_size_field_pair_prefilled_with_current_values(
    tk_root, fake_settings_repository
):
    window = _window(tk_root, fake_settings_repository)
    try:
        window._select_category("Defaults")

        assert "Window size (applies on next launch)" in _all_widget_texts(window)
        width_entry = _dimension_entry(window, "Width")
        height_entry = _dimension_entry(window, "Height")
        assert width_entry.get() == str(DEFAULT_WINDOW_WIDTH)
        assert height_entry.get() == str(DEFAULT_WINDOW_HEIGHT)
    finally:
        window.destroy()


def test_defaults_category_prefills_the_window_size_fields_from_a_stored_value(
    tk_root, fake_settings_repository
):
    fake_settings_repository.set(SettingsScope.SHARED, "window_width", 1024)
    fake_settings_repository.set(SettingsScope.SHARED, "window_height", 768)
    window = _window(tk_root, fake_settings_repository)
    try:
        window._select_category("Defaults")

        assert _dimension_entry(window, "Width").get() == "1024"
        assert _dimension_entry(window, "Height").get() == "768"
    finally:
        window.destroy()


def test_add_default_dimension_field_in_clamp_mode_writes_an_in_range_value_with_no_error(
    tk_root, fake_settings_repository
):
    window = _window(tk_root, fake_settings_repository)
    try:
        written = []
        frame = tk.Frame(window)
        window._add_default_dimension_field(
            frame, "Width", "1280", written.append, min_value=800, max_value=1920, clamp=True
        )
        entry = next(iter(_find_all(frame, tk.Entry)))
        entry.delete(0, "end")
        entry.insert(0, "1440")

        window._validate_default_dimension(
            entry, written.append, min_value=800, max_value=1920, clamp=True
        )

        assert written == [1440]
        error_label = window._default_dimension_errors[entry]
        assert error_label.cget("text") == ""
    finally:
        window.destroy()


def test_add_default_dimension_field_in_clamp_mode_clamps_and_writes_an_out_of_range_value(
    tk_root, fake_settings_repository
):
    # I/O matrix: "User sets an out-of-bounds window size in Settings" --
    # clamped to the given bounds on write, with an inline note, never a
    # crash and never silently discarded (unlike the reject-only
    # `clamp=False` mode the New Maze/Random Maze fields still use).
    colors = colors_for(Theme.LIGHT)
    window = _window(tk_root, fake_settings_repository)
    try:
        written = []
        frame = tk.Frame(window)
        window._add_default_dimension_field(
            frame, "Width", "1280", written.append, min_value=800, max_value=1920, clamp=True
        )
        entry = next(iter(_find_all(frame, tk.Entry)))
        entry.delete(0, "end")
        entry.insert(0, "99999")

        window._validate_default_dimension(
            entry, written.append, min_value=800, max_value=1920, clamp=True
        )

        assert written == [1920]
        error_label = window._default_dimension_errors[entry]
        assert error_label.cget("text") == "Clamped to 1920."
        # The field's own displayed text must be rewritten to the clamped
        # value too -- otherwise it would keep showing the stray "99999"
        # the user typed, visibly disagreeing with what was actually
        # persisted until Settings is closed and reopened.
        assert entry.get() == "1920"
        # A distinct, non-error color from a genuine validation error
        # (below) -- the value *was* accepted and saved, not rejected, so
        # it must not read as "something went wrong."
        assert error_label.cget("foreground") == colors.ink_soft
        assert error_label.cget("foreground") != colors.exit

        # And the opposite direction, below the minimum.
        entry.delete(0, "end")
        entry.insert(0, "10")

        window._validate_default_dimension(
            entry, written.append, min_value=800, max_value=1920, clamp=True
        )

        assert written == [1920, 800]
        assert error_label.cget("text") == "Clamped to 800."
        assert entry.get() == "800"
        assert error_label.cget("foreground") == colors.ink_soft
    finally:
        window.destroy()


def test_add_default_dimension_field_shows_an_inline_error_and_does_not_write_for_non_numeric_input(
    tk_root, fake_settings_repository
):
    colors = colors_for(Theme.LIGHT)
    window = _window(tk_root, fake_settings_repository)
    try:
        written = []
        frame = tk.Frame(window)
        window._add_default_dimension_field(
            frame, "Width", "1280", written.append, min_value=800, max_value=1920, clamp=True
        )
        entry = next(iter(_find_all(frame, tk.Entry)))
        entry.delete(0, "end")
        entry.insert(0, "not-a-number")

        window._validate_default_dimension(
            entry, written.append, min_value=800, max_value=1920, clamp=True
        )

        assert written == []
        error_label = window._default_dimension_errors[entry]
        assert error_label.cget("text") == "Enter a whole number."
        # A genuine error (nothing was persisted) styles distinctly from
        # the clamp-mode's accepted-and-saved note above.
        assert error_label.cget("foreground") == colors.exit
    finally:
        window.destroy()


def test_add_default_dimension_field_in_reject_mode_never_writes_an_out_of_range_value(
    tk_root, fake_settings_repository
):
    # `clamp=False` (the default) preserves the original New Maze/Random
    # Maze dimension fields' own behavior: an out-of-bounds entry is
    # rejected outright -- the writer is never called and the previously
    # stored value is left untouched.
    window = _window(tk_root, fake_settings_repository)
    try:
        written = []
        frame = tk.Frame(window)
        window._add_default_dimension_field(frame, "Columns", "5", written.append)
        entry = next(iter(_find_all(frame, tk.Entry)))
        entry.delete(0, "end")
        entry.insert(0, "0")

        window._validate_default_dimension(entry, written.append)

        assert written == []
        error_label = window._default_dimension_errors[entry]
        assert error_label.cget("text") == "Must be a positive number."
    finally:
        window.destroy()


def _capture_real_dimension_writers(monkeypatch, window_cls: type[SettingsWindow]) -> dict:
    """Capture the *actual* `writer` closures `_build_defaults` passes into
    `_add_default_dimension_field` for every field, keyed by label.

    Wraps (rather than replaces) the real method -- the widgets are still
    built normally -- so a test calling `captured["Width"](...)`/
    `captured["Height"](...)` drives the exact bound closures the real
    `<KeyRelease>` handler would (`lambda v: write_window_width(...,
    screen_width)` / `lambda v: write_window_height(..., screen_height)`),
    not a hand-rolled stand-in. Guards against a copy-paste swap between the
    near-identical Width/Height blocks in `_build_defaults` (e.g. Height's
    writer accidentally calling `write_window_height(..., screen_width)`)
    that every other test here -- built against a reconstructed writer --
    would miss.
    """
    captured: dict = {}
    original = window_cls._add_default_dimension_field

    def spying(self, parent, label, initial_value, writer, **kwargs):
        captured[label] = writer
        return original(self, parent, label, initial_value, writer, **kwargs)

    monkeypatch.setattr(window_cls, "_add_default_dimension_field", spying)
    return captured


def test_the_real_width_and_height_field_writers_each_persist_only_their_own_dimension(
    tk_root, fake_settings_repository, monkeypatch
):
    captured = _capture_real_dimension_writers(monkeypatch, SettingsWindow)
    window = _window(tk_root, fake_settings_repository)
    try:
        window._select_category("Defaults")
        assert set(captured) >= {"Width", "Height"}

        captured["Width"](1440)

        assert fake_settings_repository.get(SettingsScope.SHARED, "window_width") == 1440
        with pytest.raises(SettingNotFoundError):
            fake_settings_repository.get(SettingsScope.SHARED, "window_height")

        captured["Height"](900)

        # The Width writer's earlier call must be untouched by the Height
        # writer -- proves the two closures are wired to distinct keys, not
        # a copy-paste-swapped pair sharing one.
        assert fake_settings_repository.get(SettingsScope.SHARED, "window_width") == 1440
        assert fake_settings_repository.get(SettingsScope.SHARED, "window_height") == 900
    finally:
        window.destroy()


def test_the_real_width_field_writer_clamps_to_this_windows_own_screen_width(
    tk_root, fake_settings_repository, monkeypatch
):
    captured = _capture_real_dimension_writers(monkeypatch, SettingsWindow)
    window = _window(tk_root, fake_settings_repository)
    try:
        window._select_category("Defaults")
        screen_width = window.winfo_screenwidth()

        captured["Width"](screen_width + 5000)

        assert fake_settings_repository.get(SettingsScope.SHARED, "window_width") == screen_width
    finally:
        window.destroy()


def test_persisting_a_window_size_change_through_the_real_field_then_reopening_reflects_it(
    tk_root, fake_settings_repository, monkeypatch
):
    captured = _capture_real_dimension_writers(monkeypatch, SettingsWindow)
    window = _window(tk_root, fake_settings_repository)
    try:
        window._select_category("Defaults")
        entry = _dimension_entry(window, "Width")

        # Drives the real registered widget *and* the real writer closure
        # end to end: types into the actual `Entry`, then calls
        # `_validate_default_dimension` with that same real
        # `write_window_width`-backed `writer` -- a real `<KeyRelease>`
        # isn't reliably synthesizable under a withdrawn `tk_root` (no
        # other test in this file relies on it either), so this is the
        # closest equivalent to a genuine keystroke.
        entry.delete(0, "end")
        entry.insert(0, "1024")
        window._validate_default_dimension(
            entry,
            captured["Width"],
            min_value=MIN_WINDOW_WIDTH,
            max_value=window.winfo_screenwidth(),
            clamp=True,
        )

        assert fake_settings_repository.get(SettingsScope.SHARED, "window_width") == 1024
    finally:
        window.destroy()

    reopened = _window(tk_root, fake_settings_repository)
    try:
        reopened._select_category("Defaults")
        assert _dimension_entry(reopened, "Width").get() == "1024"
        width, _height = read_window_size(
            fake_settings_repository, reopened.winfo_screenwidth(), reopened.winfo_screenheight()
        )
        assert width == 1024
    finally:
        reopened.destroy()
