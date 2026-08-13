"""Movement mode/speed settings -- `game`-scoped readers/writers (Story 2.5).

Mirrors `maze_size_bounds._read_bound`'s per-field fallback pattern: each of
the two `game`-scope settings falls back independently to `SMOOTH`/`NORMAL`
on `SettingNotFoundError`/`SettingCorruptError`/`ValueError`/`TypeError` --
and on any stored value that isn't a valid member name -- rather than the
whole read failing, or the caller ever seeing an exception, just because one
key is unset or corrupt. Never writes on read. `write_*` persists the
member's string `.value` via `settings.set(SettingsScope.GAME, ...)`.
"""

from __future__ import annotations

from labyrinthes.application.errors import SettingCorruptError, SettingNotFoundError
from labyrinthes.application.settings_keys import MOVEMENT_MODE, MOVEMENT_SPEED
from labyrinthes.application.settings_repository import SettingsRepository, SettingsScope
from labyrinthes.domain.movement_mode import MovementMode
from labyrinthes.domain.movement_speed import MovementSpeed

__all__ = [
    "read_movement_mode",
    "read_movement_speed",
    "write_movement_mode",
    "write_movement_speed",
]


def _read_member(settings: SettingsRepository, key: str, members, default):
    try:
        value = settings.get(SettingsScope.GAME, key)
        return members(value)
    except (SettingNotFoundError, SettingCorruptError, ValueError, TypeError):
        return default


def read_movement_mode(settings: SettingsRepository) -> MovementMode:
    """The `game`-scope `MovementMode`, defaulting to `SMOOTH`. Never raises."""
    return _read_member(settings, MOVEMENT_MODE, MovementMode, MovementMode.SMOOTH)


def read_movement_speed(settings: SettingsRepository) -> MovementSpeed:
    """The `game`-scope `MovementSpeed`, defaulting to `NORMAL`. Never raises."""
    return _read_member(settings, MOVEMENT_SPEED, MovementSpeed, MovementSpeed.NORMAL)


def write_movement_mode(settings: SettingsRepository, mode: MovementMode) -> None:
    """Persist `mode` as the `game`-scope movement mode."""
    settings.set(SettingsScope.GAME, MOVEMENT_MODE, mode.value)


def write_movement_speed(settings: SettingsRepository, speed: MovementSpeed) -> None:
    """Persist `speed` as the `game`-scope movement speed."""
    settings.set(SettingsScope.GAME, MOVEMENT_SPEED, speed.value)
