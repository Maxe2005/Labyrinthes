"""Window size -- `shared`-scope reader/writer (Story 4.10 follow-up).

The root `Tk` window's initial size, read exactly once at startup
(`app/composition_root.py::build_app()`, before `root` is ever mounted) and
never re-read afterward -- the window's `.geometry()` is set once and the
app never auto-resizes it across navigation (see the spec's Boundaries).
`shared`-scope (not `builder`/`game`) since both apps share the one `Tk()`
root.

Mirrors `defaults_settings.py`/`confirmation_settings.py`'s numeric-reader
shape (a `_read_*` helper plus thin `read_*`/`write_*` functions, falling
back on `(SettingNotFoundError, SettingCorruptError, TypeError)` rather
than raising) -- not `theme_logo_settings.py`'s, which only guards
`SettingNotFoundError` since a string setting has no "wrong type but still
parses" failure mode the way a numeric one does. Each dimension defaults to
`DEFAULT_WINDOW_WIDTH`/`DEFAULT_WINDOW_HEIGHT` (1280x800) on unset/corrupt
storage or a non-`int` stored value (including a stored `bool` -- `bool` is
an `int` subclass in Python, so it's explicitly excluded rather than
silently accepted as `0`/`1`), and is independently clamped to
`[MIN_WINDOW_WIDTH, screen_width]`/`[MIN_WINDOW_HEIGHT, screen_height]` --
the caller's own physical screen bounds, passed in as plain ints so this
module stays `Tk`-agnostic (`app/` supplies `winfo_screenwidth()`/
`winfo_screenheight()`, `common/settings_window.py` supplies the Settings
`Toplevel`'s own). `write_window_width`/`write_window_height` clamp before
persisting too, so a value written directly through this module (bypassing
`SettingsWindow`'s own inline-error UI validation) can still never end up
larger than the screen it would be centered on.
"""

from __future__ import annotations

from labyrinthes.application.errors import SettingCorruptError, SettingNotFoundError
from labyrinthes.application.settings_keys import WINDOW_HEIGHT, WINDOW_WIDTH
from labyrinthes.application.settings_repository import SettingsRepository, SettingsScope

__all__ = [
    "DEFAULT_WINDOW_HEIGHT",
    "DEFAULT_WINDOW_WIDTH",
    "MIN_WINDOW_HEIGHT",
    "MIN_WINDOW_WIDTH",
    "clamp_window_height",
    "clamp_window_width",
    "read_window_size",
    "write_window_height",
    "write_window_width",
]

DEFAULT_WINDOW_WIDTH = 1280
DEFAULT_WINDOW_HEIGHT = 800
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600


def clamp_window_width(value: int, screen_width: int) -> int:
    """`value` clamped to `[MIN_WINDOW_WIDTH, screen_width]`.

    `screen_width` is itself floored at `MIN_WINDOW_WIDTH` first, so an
    (unrealistic, but possible under a tiny virtual display) screen
    narrower than the minimum never produces an inverted `max > min` range.
    """
    return max(MIN_WINDOW_WIDTH, min(value, max(MIN_WINDOW_WIDTH, screen_width)))


def clamp_window_height(value: int, screen_height: int) -> int:
    """`value` clamped to `[MIN_WINDOW_HEIGHT, screen_height]` -- see `clamp_window_width`."""
    return max(MIN_WINDOW_HEIGHT, min(value, max(MIN_WINDOW_HEIGHT, screen_height)))


def _read_dimension(settings: SettingsRepository, key: str, default: int) -> int:
    try:
        value = settings.get(SettingsScope.SHARED, key)
    except (SettingNotFoundError, SettingCorruptError, TypeError):
        return default
    # `bool` is an `int` subclass in Python (`isinstance(True, int)` is
    # `True`), so a corrupted/migrated boolean-typed stored value must be
    # excluded explicitly -- otherwise it would silently pass as `1`/`0`
    # instead of falling back to `default`.
    if not isinstance(value, int) or isinstance(value, bool):
        return default
    return value


def read_window_size(
    settings: SettingsRepository, screen_width: int, screen_height: int
) -> tuple[int, int]:
    """The `shared`-scope `(width, height)`, each clamped to the given screen bounds.

    Falls back independently to `DEFAULT_WINDOW_WIDTH`/`DEFAULT_WINDOW_HEIGHT`
    on unset/corrupt storage, then clamps whatever value results (stored or
    default) to the screen bounds -- so a default that happens to exceed a
    small screen is still clamped down, never raises.
    """
    width = clamp_window_width(
        _read_dimension(settings, WINDOW_WIDTH, DEFAULT_WINDOW_WIDTH), screen_width
    )
    height = clamp_window_height(
        _read_dimension(settings, WINDOW_HEIGHT, DEFAULT_WINDOW_HEIGHT), screen_height
    )
    return width, height


def write_window_width(settings: SettingsRepository, width: int, screen_width: int) -> None:
    """Persist `width`, clamped to `[MIN_WINDOW_WIDTH, screen_width]`, as the window width."""
    settings.set(SettingsScope.SHARED, WINDOW_WIDTH, clamp_window_width(width, screen_width))


def write_window_height(settings: SettingsRepository, height: int, screen_height: int) -> None:
    """Persist `height`, clamped to `[MIN_WINDOW_HEIGHT, screen_height]`, as the window height."""
    settings.set(SettingsScope.SHARED, WINDOW_HEIGHT, clamp_window_height(height, screen_height))
