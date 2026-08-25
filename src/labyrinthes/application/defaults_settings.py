"""Default value settings — scoped readers/writers (Story 4.6).

The two `builder`-scope settings (`BUILDER_DEFAULT_TOOL`, `NEW_MAZE_DEFAULT_*`)
and two `game`-scope settings (`RANDOM_MAZE_DEFAULT_*`) fall back
independently to their documented defaults on `SettingNotFoundError`/
`SettingCorruptError`/`ValueError`/`TypeError` -- and on any stored value
that isn't valid for its type -- rather than the whole read failing, or the
caller ever seeing an exception, just because one key is unset or corrupt.
Never writes on read. `write_*` persists the raw value via
`settings.set(scope, ...)` and are the tested persistence seam the Settings
window consumes.
"""

from __future__ import annotations

from labyrinthes.application.builder_session import BuilderTool
from labyrinthes.application.errors import SettingCorruptError, SettingNotFoundError
from labyrinthes.application.settings_keys import (
    BUILDER_DEFAULT_TOOL,
    NEW_MAZE_DEFAULT_COLUMNS,
    NEW_MAZE_DEFAULT_ROWS,
    RANDOM_MAZE_DEFAULT_COLUMNS,
    RANDOM_MAZE_DEFAULT_ROWS,
)
from labyrinthes.application.settings_repository import SettingsRepository, SettingsScope
from labyrinthes.domain.maze_size_bounds import DEFAULT_MAZE_SIZE_BOUNDS

__all__ = [
    "read_builder_default_tool",
    "write_builder_default_tool",
    "read_new_maze_defaults",
    "write_new_maze_default_columns",
    "write_new_maze_default_rows",
    "read_random_maze_defaults",
    "write_random_maze_default_columns",
    "write_random_maze_default_rows",
]


def _read_enum(
    settings: SettingsRepository,
    key: str,
    default: BuilderTool,
    scope: SettingsScope,
    valid_values: frozenset[str],
) -> BuilderTool:
    try:
        value = settings.get(scope, key)
    except (SettingNotFoundError, SettingCorruptError, TypeError):
        return default
    if not isinstance(value, str) or value not in valid_values:
        return default
    return BuilderTool(value)


def _read_int(
    settings: SettingsRepository,
    key: str,
    default: int,
    scope: SettingsScope,
    min_value: int,
    max_value: int,
) -> int:
    try:
        value = settings.get(scope, key)
    except (SettingNotFoundError, SettingCorruptError, TypeError):
        return default
    if not isinstance(value, int) or value < min_value or value > max_value:
        return default
    return value


def read_builder_default_tool(settings: SettingsRepository) -> BuilderTool:
    """The default Builder tool. Defaults to `BuilderTool.BREAK`. Never raises."""
    return _read_enum(
        settings,
        BUILDER_DEFAULT_TOOL,
        BuilderTool.BREAK,
        SettingsScope.BUILDER,
        frozenset(t.value for t in BuilderTool),
    )


def write_builder_default_tool(settings: SettingsRepository, tool: BuilderTool) -> None:
    """Persist `tool` as the `builder`-scope default tool setting."""
    settings.set(SettingsScope.BUILDER, BUILDER_DEFAULT_TOOL, tool.value)


def read_new_maze_defaults(settings: SettingsRepository) -> tuple[int, int]:
    """The default new-maze columns and rows, clamped to FR-4 bounds.
    
    Each field independently falls back to the bounds' minimum (3).
    Never raises.
    """
    columns = _read_int(
        settings,
        NEW_MAZE_DEFAULT_COLUMNS,
        DEFAULT_MAZE_SIZE_BOUNDS.min_columns,
        SettingsScope.BUILDER,
        DEFAULT_MAZE_SIZE_BOUNDS.min_columns,
        DEFAULT_MAZE_SIZE_BOUNDS.max_columns,
    )
    rows = _read_int(
        settings,
        NEW_MAZE_DEFAULT_ROWS,
        DEFAULT_MAZE_SIZE_BOUNDS.min_rows,
        SettingsScope.BUILDER,
        DEFAULT_MAZE_SIZE_BOUNDS.min_rows,
        DEFAULT_MAZE_SIZE_BOUNDS.max_rows,
    )
    return columns, rows


def write_new_maze_default_columns(settings: SettingsRepository, columns: int) -> None:
    """Persist `columns` as the `builder`-scope new-maze default columns setting."""
    settings.set(SettingsScope.BUILDER, NEW_MAZE_DEFAULT_COLUMNS, columns)


def write_new_maze_default_rows(settings: SettingsRepository, rows: int) -> None:
    """Persist `rows` as the `builder`-scope new-maze default rows setting."""
    settings.set(SettingsScope.BUILDER, NEW_MAZE_DEFAULT_ROWS, rows)


def read_random_maze_defaults(settings: SettingsRepository) -> tuple[int, int]:
    """The default random-maze columns and rows, clamped to FR-4 bounds.
    
    Each field independently falls back to the bounds' minimum (3).
    Never raises.
    """
    columns = _read_int(
        settings,
        RANDOM_MAZE_DEFAULT_COLUMNS,
        DEFAULT_MAZE_SIZE_BOUNDS.min_columns,
        SettingsScope.GAME,
        DEFAULT_MAZE_SIZE_BOUNDS.min_columns,
        DEFAULT_MAZE_SIZE_BOUNDS.max_columns,
    )
    rows = _read_int(
        settings,
        RANDOM_MAZE_DEFAULT_ROWS,
        DEFAULT_MAZE_SIZE_BOUNDS.min_rows,
        SettingsScope.GAME,
        DEFAULT_MAZE_SIZE_BOUNDS.min_rows,
        DEFAULT_MAZE_SIZE_BOUNDS.max_rows,
    )
    return columns, rows


def write_random_maze_default_columns(settings: SettingsRepository, columns: int) -> None:
    """Persist `columns` as the `game`-scope random-maze default columns setting."""
    settings.set(SettingsScope.GAME, RANDOM_MAZE_DEFAULT_COLUMNS, columns)


def write_random_maze_default_rows(settings: SettingsRepository, rows: int) -> None:
    """Persist `rows` as the `game`-scope random-maze default rows setting."""
    settings.set(SettingsScope.GAME, RANDOM_MAZE_DEFAULT_ROWS, rows)