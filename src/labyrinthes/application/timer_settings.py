"""Timer limit settings -- `game`-scoped readers/writers (Story 2.9).

Mirrors `movement_settings.py`'s per-field fallback pattern: each of the two
`game`-scope settings falls back independently to `False`/`60` on
`SettingNotFoundError`/`SettingCorruptError`/`ValueError`/`TypeError` -- and on
any stored value that isn't a valid member name -- rather than the whole read
failing, or the caller ever seeing an exception, just because one key is unset
or corrupt. Never writes on read. `write_*` persists the member's string `.value`
via `settings.set(SettingsScope.GAME, ...)`.
"""

from __future__ import annotations

from labyrinthes.application.errors import SettingCorruptError, SettingNotFoundError
from labyrinthes.application.settings_keys import TIMER_LIMIT_ENABLED, TIMER_LIMIT_SECONDS
from labyrinthes.application.settings_repository import SettingsRepository, SettingsScope

__all__ = [
    "read_timer_limit_enabled",
    "read_timer_limit_seconds",
    "write_timer_limit_enabled",
    "write_timer_limit_seconds",
]


def _read_member(settings: SettingsRepository, key: str, default):
    """Read a setting value, falling back to `default` on any error."""
    try:
        value = settings.get(SettingsScope.GAME, key)
        return value
    except (SettingNotFoundError, SettingCorruptError, ValueError, TypeError):
        return default


def _to_bool(value) -> bool:
    """Convert a stored string representation to bool."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    return False


def _to_int(value, default: int) -> int:
    """Convert a stored value to int, falling back to `default` on failure."""
    if isinstance(value, bool):
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def read_timer_limit_enabled(settings: SettingsRepository) -> bool:
    """The `game`-scope `timer_limit_enabled`, defaulting to `False`. Never raises."""
    raw = _read_member(settings, TIMER_LIMIT_ENABLED, False)
    return _to_bool(raw)


def read_timer_limit_seconds(settings: SettingsRepository) -> int:
    """The `game`-scope `timer_limit_seconds`, defaulting to `60`. Never raises."""
    raw = _read_member(settings, TIMER_LIMIT_SECONDS, 60)
    return _to_int(raw, 60)


def write_timer_limit_enabled(settings: SettingsRepository, enabled: bool) -> None:
    """Persist `enabled` as the `game`-scope timer limit enabled flag."""
    settings.set(SettingsScope.GAME, TIMER_LIMIT_ENABLED, str(enabled).lower())


def write_timer_limit_seconds(settings: SettingsRepository, seconds: int) -> None:
    """Persist `seconds` as the `game`-scope timer limit duration."""
    settings.set(SettingsScope.GAME, TIMER_LIMIT_SECONDS, str(seconds))