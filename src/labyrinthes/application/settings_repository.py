"""`SettingsRepository` port — the single interface for scoped settings persistence.

Each of `builder`/`game`/`shared` is written immediately on `set()` — never
a load-everything/dump-everything cycle — so running Builder and Player at
once never lets one silently overwrite the other's settings on close.
"""

import abc
import enum

SettingValue = str | int | float | bool | tuple[str, ...]
"""A storable settings value.

`tuple[str, ...]`, not `list`, mirrors the project's immutable-value-object
convention (e.g. `Grid.cells`) for the legacy comma-joined list settings.
"""


class SettingsScope(enum.Enum):
    """Which application's settings a key belongs to."""

    BUILDER = "builder"
    GAME = "game"
    SHARED = "shared"


class SettingsRepository(abc.ABC):
    """Port for reading/writing a single setting within a `SettingsScope`."""

    @abc.abstractmethod
    def get(self, scope: SettingsScope, key: str) -> SettingValue:
        """Return the stored value for `key` within `scope`.

        Raises `SettingNotFoundError` if no value is stored for `key`.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def set(self, scope: SettingsScope, key: str, value: SettingValue) -> None:
        """Store `value` for `key` within `scope`, persisting immediately."""
        raise NotImplementedError
