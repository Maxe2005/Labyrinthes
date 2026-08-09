"""JSON settings serialization -- the shared routine every `SettingsRepository`
reader/writer reuses.

Each file stores exactly one `SettingValue`, JSON-encoded. `bool`/`int`/
`float`/`str` round-trip through JSON's native types unchanged -- JSON's
`true`/`false` literals keep `bool` distinguishable from `int` on read-back,
unlike a naive `str`/`int` round-trip (Python's `bool` is an `int`
subclass). `tuple[str, ...]` encodes as a JSON array; since a JSON array
always decodes to a `list`, every array value read back is converted to a
tuple here, mirroring `Grid.cells`' immutable-nested-tuple convention.
"""

import json
from pathlib import Path

from labyrinthes.adapters.storage.atomic_write import atomic_open_for_write
from labyrinthes.application.settings_repository import SettingValue


def read_setting_value(path: Path) -> SettingValue:
    """Read the single `SettingValue` stored at `path`.

    A JSON array decodes back into a `tuple`, never a `list`.
    """
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if isinstance(value, list):
        return tuple(value)
    return value


def write_setting_value(path: Path, value: SettingValue) -> None:
    """Write `value` to `path` as JSON, creating `path`'s parent directory if needed.

    Writes via `atomic_open_for_write` (temp-file-plus-rename), never
    in-place, so a write interrupted partway never corrupts or truncates a
    previously saved file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with atomic_open_for_write(path, encoding="utf-8") as handle:
        json.dump(value, handle)
