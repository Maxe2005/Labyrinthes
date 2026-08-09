"""`JsonSettingsRepository` -- the single concrete `SettingsRepository` (Story 1.5).

One JSON file per `(scope, key)` pair, one folder per `SettingsScope`, under
a single declared root (see `settings_paths.py`). `get`/`set` each touch
exactly one file -- never a load-everything/dump-everything cycle (AD-7).
`get()` re-reads its file from disk on every call, with no in-memory cache,
so two repository instances sharing the same root (simulating Builder and
Game running at once) observe each other's `shared`-scope writes within the
same session.
"""

from pathlib import Path

from labyrinthes.adapters.storage.settings_format import read_setting_value, write_setting_value
from labyrinthes.adapters.storage.settings_paths import DEFAULT_SETTINGS_ROOT, setting_file_path
from labyrinthes.application.errors import SettingNotFoundError
from labyrinthes.application.settings_repository import (
    SettingsRepository,
    SettingsScope,
    SettingValue,
)


class JsonSettingsRepository(SettingsRepository):
    """`SettingsRepository` backed by one JSON file per `(scope, key)` pair under `root`."""

    def __init__(self, root: Path = DEFAULT_SETTINGS_ROOT) -> None:
        self._root = root

    def get(self, scope: SettingsScope, key: str) -> SettingValue:
        path = setting_file_path(self._root, scope, key)
        if not path.is_file():
            raise SettingNotFoundError(f"No {scope.value} setting named {key!r}")
        try:
            return read_setting_value(path)
        except (FileNotFoundError, IsADirectoryError):
            # TOCTOU: the file passed the `is_file()` check above but is
            # gone -- or replaced by a directory -- by the time we open it.
            # Indistinguishable from "never set" at this point, so reuse
            # the same not-found error.
            raise SettingNotFoundError(f"No {scope.value} setting named {key!r}") from None

    def set(self, scope: SettingsScope, key: str, value: SettingValue) -> None:
        path = setting_file_path(self._root, scope, key)
        write_setting_value(path, value)
