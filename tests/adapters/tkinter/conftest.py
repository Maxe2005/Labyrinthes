"""Shared test helpers for screen `mount()` tests (Story 1.8).

Hoisted here per Story 1.7's precedent (the shared `tk_root` fixture in
`tests/conftest.py`), replacing three identical `_navigate_stub`/`_find_all`
copies across `tests/adapters/tkinter/{home,builder,player}/`.
"""

import tkinter as tk

import pytest


@pytest.fixture
def navigate_stub():
    """A `NavigateFn` stub plus the list of `(screen_id, state)` calls it recorded."""
    calls = []

    def navigate(screen_id, state):
        calls.append((screen_id, state))

    return navigate, calls


@pytest.fixture
def toggle_theme_stub():
    """A `ToggleThemeFn` stub plus the list of calls it recorded."""
    calls = []

    def toggle_theme():
        calls.append(1)

    return toggle_theme, calls


@pytest.fixture
def find_all():
    """A function that recursively collects every `widget_type` descendant of a widget."""

    def _find_all(widget: tk.Widget, widget_type: type) -> list:
        found = []
        for child in widget.winfo_children():
            if isinstance(child, widget_type):
                found.append(child)
            found.extend(_find_all(child, widget_type))
        return found

    return _find_all
