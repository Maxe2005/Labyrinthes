"""Per-action confirmation-prompt settings -- `game`-scoped readers/writers (Story 2.10).

Each of the four `game`-scope bool settings (`CONFIRM_SWITCH_MAZE`,
`CONFIRM_RESTART`, `CONFIRM_LEVEL_CHANGE`, `CONFIRM_INVALID_INPUT`) falls
back independently to its documented legacy default on
`SettingNotFoundError`/`SettingCorruptError`/`TypeError` -- and on any
stored value that isn't an actual `bool` (`type(value) is bool`, rejecting
`1`/`0`/`"true"`/`"false"`/`None`, the strictness precedent set by
`hard_mode_settings._read_color` in Story 2.8) -- rather than the whole
read failing, or the caller ever seeing an exception, just because one key
is unset or corrupt. Never writes on read. `write_*` persists the raw bool
via `settings.set(SettingsScope.GAME, ...)` (no encoding), and are the
tested persistence seam the Settings confirmation toggles consume.
"""

from __future__ import annotations

from labyrinthes.application.errors import SettingCorruptError, SettingNotFoundError
from labyrinthes.application.settings_keys import (
    CONFIRM_INVALID_INPUT,
    CONFIRM_LEVEL_CHANGE,
    CONFIRM_RESTART,
    CONFIRM_SWITCH_MAZE,
)
from labyrinthes.application.settings_repository import SettingsRepository, SettingsScope

__all__ = [
    "read_confirm_invalid_input",
    "read_confirm_level_change",
    "read_confirm_restart",
    "read_confirm_switch_maze",
    "write_confirm_invalid_input",
    "write_confirm_level_change",
    "write_confirm_restart",
    "write_confirm_switch_maze",
]


def _read_bool(settings: SettingsRepository, key: str, default: bool) -> bool:
    try:
        value = settings.get(SettingsScope.GAME, key)
    except (SettingNotFoundError, SettingCorruptError, TypeError):
        return default
    if type(value) is not bool:
        return default
    return value


def read_confirm_switch_maze(settings: SettingsRepository) -> bool:
    """`True` if switching mazes should prompt first. Defaults to `False` (legacy). Never raises."""
    return _read_bool(settings, CONFIRM_SWITCH_MAZE, False)


def read_confirm_restart(settings: SettingsRepository) -> bool:
    """`True` if restarting should prompt first. Defaults to `True` (legacy). Never raises."""
    return _read_bool(settings, CONFIRM_RESTART, True)


def read_confirm_level_change(settings: SettingsRepository) -> bool:
    """`True` if changing Level should prompt first. Defaults to `False` (legacy). Never raises."""
    return _read_bool(settings, CONFIRM_LEVEL_CHANGE, False)


def read_confirm_invalid_input(settings: SettingsRepository) -> bool:
    """`True` if invalid input should alert. Defaults to `True` (legacy). Never raises."""
    return _read_bool(settings, CONFIRM_INVALID_INPUT, True)


def write_confirm_switch_maze(settings: SettingsRepository, enabled: bool) -> None:
    """Persist `enabled` as the `game`-scope switch-maze confirmation setting."""
    settings.set(SettingsScope.GAME, CONFIRM_SWITCH_MAZE, enabled)


def write_confirm_restart(settings: SettingsRepository, enabled: bool) -> None:
    """Persist `enabled` as the `game`-scope restart confirmation setting."""
    settings.set(SettingsScope.GAME, CONFIRM_RESTART, enabled)


def write_confirm_level_change(settings: SettingsRepository, enabled: bool) -> None:
    """Persist `enabled` as the `game`-scope level-change confirmation setting."""
    settings.set(SettingsScope.GAME, CONFIRM_LEVEL_CHANGE, enabled)


def write_confirm_invalid_input(settings: SettingsRepository, enabled: bool) -> None:
    """Persist `enabled` as the `game`-scope invalid-input alert setting."""
    settings.set(SettingsScope.GAME, CONFIRM_INVALID_INPUT, enabled)
