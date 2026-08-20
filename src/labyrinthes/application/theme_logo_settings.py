"""Theme logo -- `game`-scoped reader/writer (Story 2.11).

The stored value is a logo name string (e.g. `"default"`, `"dragon"`,
`"butterfly"`). Falls back to `"default"` when unset or corrupt rather than
raising -- the Gameplay screen itself only reads, never writes directly.
"""

from __future__ import annotations

from labyrinthes.application.errors import SettingNotFoundError
from labyrinthes.application.settings_keys import THEME_LOGO
from labyrinthes.application.settings_repository import SettingsRepository, SettingsScope

__all__ = [
    "read_theme_logo",
    "write_theme_logo",
]


def _read_logo(settings: SettingsRepository, default: str) -> str:
    try:
        value = settings.get(SettingsScope.GAME, THEME_LOGO)
    except SettingNotFoundError:
        return default
    if not isinstance(value, str):
        return default
    return value


def read_theme_logo(settings: SettingsRepository, default: str = "default") -> str:
    """The `game`-scope theme logo, defaulting to `default`. Never raises."""
    return _read_logo(settings, default)


def write_theme_logo(settings: SettingsRepository, logo: str) -> None:
    """Persist `logo` as the `game`-scope theme logo."""
    settings.set(SettingsScope.GAME, THEME_LOGO, logo)
