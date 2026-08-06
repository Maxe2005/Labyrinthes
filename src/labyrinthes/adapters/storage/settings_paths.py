"""Filesystem layout for the JSON settings store.

One root directory (`DEFAULT_SETTINGS_ROOT`, overridable per
`JsonSettingsRepository` instance), one subfolder per `SettingsScope` named
after `scope.value` (already the intended English folder name:
`builder`/`game`/`shared`), one `<key>.json` file per setting. This is the
module a future settings-migration script would import (AD-8's precedent for
`paths.py`) -- the path/naming scheme must not be duplicated anywhere else.
"""

from pathlib import Path

from labyrinthes.adapters.storage.errors import InvalidSettingKeyError
from labyrinthes.application.settings_repository import SettingsScope

DEFAULT_SETTINGS_ROOT = Path("settings")
SETTING_FILE_SUFFIX = ".json"

_PATH_SEPARATORS = ("/", "\\")


def setting_file_path(root: Path, scope: SettingsScope, key: str) -> Path:
    """The file path for `key` within `scope`, rooted at `root`.

    Raises `InvalidSettingKeyError` for anything that would break the
    on-disk `<key>.json` mapping: an empty key, or a key containing a path
    separator.
    """
    if not key:
        raise InvalidSettingKeyError("Setting key must not be empty")
    if any(separator in key for separator in _PATH_SEPARATORS):
        raise InvalidSettingKeyError(f"Setting key must not contain a path separator: {key!r}")
    return root / scope.value / f"{key}{SETTING_FILE_SUFFIX}"
