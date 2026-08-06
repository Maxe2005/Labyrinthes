"""`ThemeController` -- owns the current `Theme`, persisted via `shared` scope (Story 1.9).

`app/` is where a port (`SettingsRepository`) gets wired into a UI-facing
callback, exactly like `navigate` was bridged from `Router` in Story 1.8 --
screens never talk to `SettingsRepository` directly (AD-7). Reused
unchanged by Story 2.11/3.7 rather than reimplemented per screen (see the
epic's Cross-Story Dependencies).
"""

from __future__ import annotations

from collections.abc import Callable

from labyrinthes.adapters.tkinter.common.tokens import Theme
from labyrinthes.application.errors import SettingNotFoundError
from labyrinthes.application.settings_keys import THEME
from labyrinthes.application.settings_repository import SettingsRepository, SettingsScope

__all__ = ["ThemeController"]

ThemeListener = Callable[[Theme], None]


class ThemeController:
    """Holds the current `Theme`, persisting every change through `SettingsRepository`.

    Loads the persisted `shared`/`THEME` value at construction, defaulting
    to `Theme.LIGHT` if nothing has been stored yet (`SettingNotFoundError`)
    or if the stored value isn't a recognized `Theme` (`ValueError`, e.g. a
    hand-edited or otherwise corrupted settings file) -- neither is allowed
    to propagate, since this constructor now runs unconditionally on every
    real app launch (`composition_root.build_app()`), not just when a
    theme has already been explicitly chosen. `toggle()` flips the theme,
    persists it immediately, then notifies every `subscribe()`-d listener
    with the new `Theme` -- mirroring `SettingsRepository.set()`'s own
    write-immediately contract (AD-7), never a load-everything/
    dump-everything cycle.
    """

    def __init__(self, settings: SettingsRepository) -> None:
        self._settings = settings
        self._theme = self._load_theme()
        self._listeners: list[ThemeListener] = []

    def _load_theme(self) -> Theme:
        try:
            value = self._settings.get(SettingsScope.SHARED, THEME)
            return Theme(value)
        except (SettingNotFoundError, ValueError):
            return Theme.LIGHT

    @property
    def theme(self) -> Theme:
        """The currently active `Theme`."""
        return self._theme

    def subscribe(self, listener: ThemeListener) -> None:
        """Register `listener` to be called with the new `Theme` on every `toggle()`."""
        self._listeners.append(listener)

    def toggle(self) -> None:
        """Flip the current theme, persist it immediately, then notify subscribers."""
        new_theme = Theme.DARK if self._theme is Theme.LIGHT else Theme.LIGHT
        self._settings.set(SettingsScope.SHARED, THEME, new_theme.value)
        self._theme = new_theme
        for listener in self._listeners:
            listener(new_theme)
