"""`read_maze_size_bounds` -- settings-backed `MazeSizeBounds` reader with per-field fallback.

Mirrors `ThemeController._load_theme()`'s established pattern (Story 1.9):
each of the four `shared`-scope bound settings falls back to
`DEFAULT_MAZE_SIZE_BOUNDS`'s matching field independently on
`SettingNotFoundError`/`SettingCorruptError`/`ValueError`/`TypeError`,
rather than the whole read failing -- or the caller (`GenerateRandomDialog`)
ever seeing an exception -- just because one of the four keys is unset or
corrupt. Never writes: this only reads-with-fallback, it never calls
`settings.set(...)` to seed the bounds.

A per-field stored value is also rejected (falls back to the default) when
it is not a positive integer -- a stored `0`/negative value would otherwise
parse "successfully" as a nonsensical bound (e.g. `min_columns=0` lets
`validate_dimensions` wave through `width=0`, which `generate_random_maze`
then rejects with an uncaught `DomainValidationError`). After all four
fields are resolved, an inverted pair (`min_columns > max_columns` or
`min_rows > max_rows` -- reachable even with two individually-valid stored
values, e.g. only `min_columns` overridden past the still-default
`max_columns`) falls the *whole* pair back to `DEFAULT_MAZE_SIZE_BOUNDS`
rather than handing `GenerateRandomDialog` a range no width/height can ever
satisfy, which would silently and permanently soft-lock "Generate" with no
diagnostic (found in review; both cases reproduced directly against
`read_maze_size_bounds` before this fix).
"""

from __future__ import annotations

from labyrinthes.application.errors import SettingCorruptError, SettingNotFoundError
from labyrinthes.application.settings_keys import (
    MAZE_MAX_COLUMNS,
    MAZE_MAX_ROWS,
    MAZE_MIN_COLUMNS,
    MAZE_MIN_ROWS,
)
from labyrinthes.application.settings_repository import SettingsRepository, SettingsScope
from labyrinthes.domain.maze_size_bounds import DEFAULT_MAZE_SIZE_BOUNDS, MazeSizeBounds

__all__ = ["read_maze_size_bounds"]


def _read_bound(settings: SettingsRepository, key: str, default: int) -> int:
    try:
        value = settings.get(SettingsScope.SHARED, key)
        if isinstance(value, tuple):
            raise TypeError
        value = int(value)
    except (SettingNotFoundError, SettingCorruptError, ValueError, TypeError):
        return default
    # A non-positive stored value is not "corrupt" in the sense `int()`
    # objects to, but it's still nonsensical as a column/row bound -- treat
    # it the same as unset/corrupt rather than letting it through.
    return value if value >= 1 else default


def read_maze_size_bounds(settings: SettingsRepository) -> MazeSizeBounds:
    """The `shared`-scope `MazeSizeBounds`, each field independently defaulted.

    Never raises: an unset, corrupt, non-numeric, or non-positive stored
    value for any one of the four keys falls back to
    `DEFAULT_MAZE_SIZE_BOUNDS`'s matching field, independently of the other
    three. If the resolved columns or rows pair still ends up inverted
    (`min > max`), that whole pair falls back to
    `DEFAULT_MAZE_SIZE_BOUNDS` instead of returning a range no dimension
    can ever satisfy.
    """
    min_columns = _read_bound(settings, MAZE_MIN_COLUMNS, DEFAULT_MAZE_SIZE_BOUNDS.min_columns)
    max_columns = _read_bound(settings, MAZE_MAX_COLUMNS, DEFAULT_MAZE_SIZE_BOUNDS.max_columns)
    min_rows = _read_bound(settings, MAZE_MIN_ROWS, DEFAULT_MAZE_SIZE_BOUNDS.min_rows)
    max_rows = _read_bound(settings, MAZE_MAX_ROWS, DEFAULT_MAZE_SIZE_BOUNDS.max_rows)

    if min_columns > max_columns:
        min_columns = DEFAULT_MAZE_SIZE_BOUNDS.min_columns
        max_columns = DEFAULT_MAZE_SIZE_BOUNDS.max_columns
    if min_rows > max_rows:
        min_rows = DEFAULT_MAZE_SIZE_BOUNDS.min_rows
        max_rows = DEFAULT_MAZE_SIZE_BOUNDS.max_rows

    return MazeSizeBounds(
        min_columns=min_columns, max_columns=max_columns, min_rows=min_rows, max_rows=max_rows
    )
