"""Optional per-run time limit -- `game`-scoped reader/writer (Story 2.9).

The time limit scopes a run the same way `MOVEMENT_MODE`/`MOVEMENT_SPEED`
do: read once at mount, applied for the whole run. `read_time_limit` returns
the limit as a `Duration` (the domain's one time type, AC-4) only when the
stored value is a positive whole-second integer; `None`/`0`/absent/invalid
all read back as `None` -- "no limit", the default. Never raises and never
writes on read. `write_time_limit` persists the whole-second count
(`limit.milliseconds // 1000`); a `None` limit persists `0`, the documented
on-disk sentinel for "no limit" (the port has no delete). The writer is the
tested persistence seam a future Settings time-limit picker consumes -- the
Story 2.9 screen itself only reads, exactly like the HARD-color writers in
Story 2.8.
"""

from __future__ import annotations

from labyrinthes.application.errors import SettingCorruptError, SettingNotFoundError
from labyrinthes.application.settings_keys import TIME_LIMIT_SECONDS
from labyrinthes.application.settings_repository import SettingsRepository, SettingsScope
from labyrinthes.domain.duration import Duration

__all__ = [
    "read_time_limit",
    "write_time_limit",
]


def read_time_limit(settings: SettingsRepository) -> Duration | None:
    """The `game`-scope time limit as a `Duration`, or `None` for no limit.

    Returns `Duration(milliseconds=seconds * 1000)` only when the stored
    value is an actual positive `int`. Any other value -- absent, corrupt,
    `bool`/`float`/`str`, `0`, negative -- reads back as `None`. The strict
    `type(value) is int` check rejects `True` (which would otherwise parse
    as 1s) and silently-truncated floats, matching the `_read_color`
    strictness precedent from Story 2.8. Never raises, never writes.
    """
    try:
        value = settings.get(SettingsScope.GAME, TIME_LIMIT_SECONDS)
    except (SettingNotFoundError, SettingCorruptError, TypeError):
        return None
    if type(value) is not int or value <= 0:
        return None
    return Duration(milliseconds=value * 1000)


def write_time_limit(settings: SettingsRepository, limit: Duration | None) -> None:
    """Persist `limit` as the `game`-scope time limit, in whole seconds.

    The stored value is the whole-second *floor* of `limit.milliseconds`:
    `Duration(75000)` persists `75`. A sub-second duration floors to `0` --
    the no-limit sentinel -- so a `Duration(500)` limit silently writes "no
    limit" and reads back `None`; callers must pass whole-second durations.
    A `None` limit persists `0` -- the documented on-disk sentinel for "no
    limit", since the port has no delete operation.
    """
    seconds = 0 if limit is None else limit.milliseconds // 1000
    settings.set(SettingsScope.GAME, TIME_LIMIT_SECONDS, seconds)
