from labyrinthes.application.errors import SettingCorruptError, SettingNotFoundError
from labyrinthes.application.hard_mode_settings import (
    read_hard_mode_moving_color,
    read_hard_mode_ready_color,
    write_hard_mode_moving_color,
    write_hard_mode_ready_color,
)
from labyrinthes.application.settings_keys import HARD_MODE_MOVING_COLOR, HARD_MODE_READY_COLOR
from labyrinthes.application.settings_repository import SettingsRepository, SettingsScope


class _InMemorySettingsRepository(SettingsRepository):
    def __init__(self) -> None:
        self._store: dict[tuple[SettingsScope, str], object] = {}

    def get(self, scope, key):
        try:
            return self._store[(scope, key)]
        except KeyError:
            raise SettingNotFoundError(f"No {scope.value} setting named {key!r}") from None

    def set(self, scope, key, value):
        self._store[(scope, key)] = value


class _CorruptSettingsRepository(SettingsRepository):
    def get(self, scope, key):
        raise SettingCorruptError("corrupted settings file")

    def set(self, scope, key, value):
        raise NotImplementedError


def test_reads_defaults_when_nothing_is_stored():
    repository = _InMemorySettingsRepository()

    assert read_hard_mode_ready_color(repository, "#ff0000") == "#ff0000"
    assert read_hard_mode_moving_color(repository, "#00ff00") == "#00ff00"


def test_reads_defaults_when_the_settings_file_is_corrupted():
    repository = _CorruptSettingsRepository()

    assert read_hard_mode_ready_color(repository, "#ff0000") == "#ff0000"
    assert read_hard_mode_moving_color(repository, "#00ff00") == "#00ff00"


def test_reads_valid_stored_colors():
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.GAME, HARD_MODE_READY_COLOR, "#111111")
    repository.set(SettingsScope.GAME, HARD_MODE_MOVING_COLOR, "#222222")

    assert read_hard_mode_ready_color(repository, "#ff0000") == "#111111"
    assert read_hard_mode_moving_color(repository, "#00ff00") == "#222222"


def test_each_color_falls_back_independently_when_the_other_is_set():
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.GAME, HARD_MODE_READY_COLOR, "#111111")

    assert read_hard_mode_ready_color(repository, "#ff0000") == "#111111"
    assert read_hard_mode_moving_color(repository, "#00ff00") == "#00ff00"


def test_falls_back_to_the_default_when_a_stored_value_is_not_a_string():
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.GAME, HARD_MODE_READY_COLOR, 42)
    repository.set(SettingsScope.GAME, HARD_MODE_MOVING_COLOR, None)

    assert read_hard_mode_ready_color(repository, "#ff0000") == "#ff0000"
    assert read_hard_mode_moving_color(repository, "#00ff00") == "#00ff00"


def test_falls_back_to_the_default_when_a_stored_value_is_not_a_valid_color():
    # A stored string that isn't a Tk-usable color would reach
    # `itemconfigure(fill=...)` and raise `TclError` at render time; the
    # reader must treat it as corrupt and fall back instead (patch from
    # code review). Named colors are also rejected -- without `tkinter`
    # (AD-1) they can't be validated, and the theme/color-picker both use
    # hex anyway.
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.GAME, HARD_MODE_READY_COLOR, "")
    repository.set(SettingsScope.GAME, HARD_MODE_MOVING_COLOR, "garbage")

    assert read_hard_mode_ready_color(repository, "#ff0000") == "#ff0000"
    assert read_hard_mode_moving_color(repository, "#00ff00") == "#00ff00"


def test_accepts_valid_hex_colors_in_all_tk_supported_lengths():
    # Tk accepts `#RGB`/`#RRGGBB`/`#RRRRGGGGBBBB` (3, 6, 9, or 12 hex
    # digits) -- these must round-trip, not fall back.
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.GAME, HARD_MODE_READY_COLOR, "#f00")
    repository.set(SettingsScope.GAME, HARD_MODE_MOVING_COLOR, "#ff0000000000")

    assert read_hard_mode_ready_color(repository, "#ff0000") == "#f00"
    assert read_hard_mode_moving_color(repository, "#00ff00") == "#ff0000000000"


def test_never_writes_on_read():
    class _ExplodingOnSetRepository(SettingsRepository):
        def get(self, scope, key):
            raise SettingNotFoundError("unset")

        def set(self, scope, key, value):
            raise AssertionError("read_hard_mode_* must never call set()")

    read_hard_mode_ready_color(_ExplodingOnSetRepository(), "#ff0000")
    read_hard_mode_moving_color(_ExplodingOnSetRepository(), "#00ff00")


def test_writes_persist_in_the_game_scope_and_round_trip():
    repository = _InMemorySettingsRepository()

    write_hard_mode_ready_color(repository, "#111111")
    write_hard_mode_moving_color(repository, "#222222")

    assert repository.get(SettingsScope.GAME, HARD_MODE_READY_COLOR) == "#111111"
    assert repository.get(SettingsScope.GAME, HARD_MODE_MOVING_COLOR) == "#222222"
    assert read_hard_mode_ready_color(repository, "#ff0000") == "#111111"
    assert read_hard_mode_moving_color(repository, "#00ff00") == "#222222"
