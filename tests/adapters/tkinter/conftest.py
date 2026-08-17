"""Shared test helpers for screen `mount()` tests (Story 1.8).

Hoisted here per Story 1.7's precedent (the shared `tk_root` fixture in
`tests/conftest.py`), replacing three identical `_navigate_stub`/`_find_all`
copies across `tests/adapters/tkinter/{home,builder,player}/`.

Story 2.10 hoists `FakeSettingsRepository` here too (from
`player/conftest.py`, where it had lived since Story 2.2) so Home/Builder/
common settings tests can share the one in-memory `SettingsRepository`
double -- `player/conftest.py` imports and re-exports it.
"""

import tkinter as tk

import pytest

from labyrinthes.application.errors import SettingNotFoundError
from labyrinthes.application.settings_repository import SettingsRepository, SettingsScope


class FakeSettingsRepository(SettingsRepository):
    """In-memory `SettingsRepository` test double, keyed by `(scope, key)`."""

    def __init__(self) -> None:
        self._store: dict[tuple[SettingsScope, str], object] = {}

    def get(self, scope: SettingsScope, key: str):
        try:
            return self._store[(scope, key)]
        except KeyError:
            raise SettingNotFoundError(f"No {scope.value} setting named {key!r}") from None

    def set(self, scope: SettingsScope, key: str, value) -> None:
        self._store[(scope, key)] = value


@pytest.fixture
def fake_settings_repository() -> FakeSettingsRepository:
    """A bare `FakeSettingsRepository`, nothing seeded -- the FR-4 defaults apply."""
    return FakeSettingsRepository()


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
