"""HARD-mode status-light colors -- `game`-scoped readers/writers (Story 2.8).

Each of the two `game`-scope color settings (`HARD_MODE_READY_COLOR` for the
resting "ready" state, `HARD_MODE_MOVING_COLOR` for the "moving" state)
falls back independently to the caller-supplied `default` on
`SettingNotFoundError`/`SettingCorruptError`/`TypeError` -- and on any
stored value that isn't a string or doesn't look like a Tk color name --
rather than the whole read failing, or the caller ever seeing an exception,
just because one key is unset or corrupt. Never writes on read. The
`default` is the screen's theme-derived color (`colors.accent` for ready,
`colors.exit` for moving), passed in as a parameter so this module stays
theme-agnostic; no color literal ever lives here. `write_*` persists the
color via `settings.set(SettingsScope.GAME, ...)` and are the tested
persistence seam a future Settings color picker calls -- the Story 2.8
screen itself only reads.
"""

from __future__ import annotations

import re

from labyrinthes.application.errors import SettingCorruptError, SettingNotFoundError
from labyrinthes.application.settings_keys import HARD_MODE_MOVING_COLOR, HARD_MODE_READY_COLOR
from labyrinthes.application.settings_repository import SettingsRepository, SettingsScope

__all__ = [
    "read_hard_mode_moving_color",
    "read_hard_mode_ready_color",
    "write_hard_mode_moving_color",
    "write_hard_mode_ready_color",
]

# A Tk `#`-prefixed hex color: `#RGB`/`#RRGGBB`/`#RRRRGGGGBBBB` (3, 6, 9, or
# 12 hex digits -- verified against a live `Canvas.itemconfigure`, which
# rejects any other length). Named colors can't be validated here without
# importing `tkinter` (AD-1), so a non-hex stored value -- `""`, `"garbage"`,
# `"green"`, `"#zzz"` -- is treated as corrupt and falls back to `default`
# rather than reaching `itemconfigure(fill=...)` and raising `TclError`. The
# theme tokens and the future color picker (`tkinter.colorchooser`) both use
# hex, so rejecting named colors is not a practical regression.
_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3}){0,3}$")


def _read_color(settings: SettingsRepository, key: str, default: str) -> str:
    try:
        value = settings.get(SettingsScope.GAME, key)
    except (SettingNotFoundError, SettingCorruptError, TypeError):
        return default
    if not isinstance(value, str) or _COLOR_RE.fullmatch(value) is None:
        return default
    return value


def read_hard_mode_ready_color(settings: SettingsRepository, default: str) -> str:
    """The `game`-scope ready-state color, defaulting to `default`. Never raises."""
    return _read_color(settings, HARD_MODE_READY_COLOR, default)


def read_hard_mode_moving_color(settings: SettingsRepository, default: str) -> str:
    """The `game`-scope moving-state color, defaulting to `default`. Never raises."""
    return _read_color(settings, HARD_MODE_MOVING_COLOR, default)


def write_hard_mode_ready_color(settings: SettingsRepository, color: str) -> None:
    """Persist `color` as the `game`-scope ready-state color."""
    settings.set(SettingsScope.GAME, HARD_MODE_READY_COLOR, color)


def write_hard_mode_moving_color(settings: SettingsRepository, color: str) -> None:
    """Persist `color` as the `game`-scope moving-state color."""
    settings.set(SettingsScope.GAME, HARD_MODE_MOVING_COLOR, color)
