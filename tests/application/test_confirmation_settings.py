import pytest

from labyrinthes.application.confirmation_settings import (
    read_confirm_invalid_input,
    read_confirm_level_change,
    read_confirm_redefine_marker,
    read_confirm_restart,
    read_confirm_switch_maze,
    write_confirm_invalid_input,
    write_confirm_level_change,
    write_confirm_redefine_marker,
    write_confirm_restart,
    write_confirm_switch_maze,
)
from labyrinthes.application.errors import SettingCorruptError, SettingNotFoundError
from labyrinthes.application.settings_keys import (
    CONFIRM_INVALID_INPUT,
    CONFIRM_LEVEL_CHANGE,
    CONFIRM_REDEFINE_MARKER,
    CONFIRM_RESTART,
    CONFIRM_SWITCH_MAZE,
)
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


_READERS = [
    (read_confirm_switch_maze, False, CONFIRM_SWITCH_MAZE),
    (read_confirm_restart, True, CONFIRM_RESTART),
    (read_confirm_level_change, False, CONFIRM_LEVEL_CHANGE),
    (read_confirm_invalid_input, True, CONFIRM_INVALID_INPUT),
]

_WRITERS = [
    (write_confirm_switch_maze, CONFIRM_SWITCH_MAZE),
    (write_confirm_restart, CONFIRM_RESTART),
    (write_confirm_level_change, CONFIRM_LEVEL_CHANGE),
    (write_confirm_invalid_input, CONFIRM_INVALID_INPUT),
]


def test_reads_legacy_defaults_when_nothing_is_stored():
    repository = _InMemorySettingsRepository()

    assert read_confirm_switch_maze(repository) is False
    assert read_confirm_restart(repository) is True
    assert read_confirm_level_change(repository) is False
    assert read_confirm_invalid_input(repository) is True


def test_reads_defaults_when_the_settings_file_is_corrupted():
    repository = _CorruptSettingsRepository()

    for reader, default, _key in _READERS:
        assert reader(repository) is default


def test_returns_stored_bools_verbatim():
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.GAME, CONFIRM_SWITCH_MAZE, True)
    repository.set(SettingsScope.GAME, CONFIRM_RESTART, False)
    repository.set(SettingsScope.GAME, CONFIRM_LEVEL_CHANGE, True)
    repository.set(SettingsScope.GAME, CONFIRM_INVALID_INPUT, False)

    assert read_confirm_switch_maze(repository) is True
    assert read_confirm_restart(repository) is False
    assert read_confirm_level_change(repository) is True
    assert read_confirm_invalid_input(repository) is False


@pytest.mark.parametrize("non_bool", [1, 0, "true", "false", None, [], {}])
def test_falls_back_to_the_default_when_a_stored_value_is_not_an_actual_bool(non_bool):
    repository = _InMemorySettingsRepository()

    for reader, default, key in _READERS:
        repository.set(SettingsScope.GAME, key, non_bool)
        assert reader(repository) is default


def test_each_reader_falls_back_independently_when_the_others_are_set():
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.GAME, CONFIRM_RESTART, False)
    repository.set(SettingsScope.GAME, CONFIRM_INVALID_INPUT, False)

    assert read_confirm_switch_maze(repository) is False
    assert read_confirm_restart(repository) is False
    assert read_confirm_level_change(repository) is False
    assert read_confirm_invalid_input(repository) is False


def test_never_writes_on_read():
    class _ExplodingOnSetRepository(SettingsRepository):
        def get(self, scope, key):
            raise SettingNotFoundError("unset")

        def set(self, scope, key, value):
            raise AssertionError("read_confirm_* must never call set()")

    for reader, _default, _key in _READERS:
        reader(_ExplodingOnSetRepository())


def test_writers_persist_the_raw_bool_in_the_game_scope_and_round_trip():
    repository = _InMemorySettingsRepository()

    write_confirm_switch_maze(repository, True)
    write_confirm_restart(repository, False)
    write_confirm_level_change(repository, True)
    write_confirm_invalid_input(repository, False)

    assert repository.get(SettingsScope.GAME, CONFIRM_SWITCH_MAZE) is True
    assert repository.get(SettingsScope.GAME, CONFIRM_RESTART) is False
    assert repository.get(SettingsScope.GAME, CONFIRM_LEVEL_CHANGE) is True
    assert repository.get(SettingsScope.GAME, CONFIRM_INVALID_INPUT) is False

    assert read_confirm_switch_maze(repository) is True
    assert read_confirm_restart(repository) is False
    assert read_confirm_level_change(repository) is True
    assert read_confirm_invalid_input(repository) is False


def test_each_writer_stores_without_encoding():
    # The stored value must be the raw bool, not `1`/`0`/`"true"`/`"false"`
    # -- the reader's `type(value) is bool` strictness would otherwise read
    # a `1` back as the default.
    repository = _InMemorySettingsRepository()

    for writer, key in _WRITERS:
        writer(repository, True)
        assert repository.get(SettingsScope.GAME, key) is True
        writer(repository, False)
        assert repository.get(SettingsScope.GAME, key) is False


# -- Story 3.4: builder-scoped redefine-marker confirmation ----------------


def test_read_confirm_redefine_marker_defaults_to_true_in_the_builder_scope():
    # Story 3.4's default is `True` (unlike the legacy Player defaults) --
    # and it must be read from the `builder` scope, not `game`.
    repository = _InMemorySettingsRepository()

    assert read_confirm_redefine_marker(repository) is True


def test_read_confirm_redefine_marker_reads_only_the_builder_scope():
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.GAME, CONFIRM_REDEFINE_MARKER, False)
    assert read_confirm_redefine_marker(repository) is True  # game-scope value is ignored

    repository.set(SettingsScope.BUILDER, CONFIRM_REDEFINE_MARKER, False)
    assert read_confirm_redefine_marker(repository) is False


def test_read_confirm_redefine_marker_falls_back_when_the_value_is_not_an_actual_bool():
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.BUILDER, CONFIRM_REDEFINE_MARKER, 1)

    assert read_confirm_redefine_marker(repository) is True


def test_read_confirm_redefine_marker_falls_back_on_a_corrupted_store():
    assert read_confirm_redefine_marker(_CorruptSettingsRepository()) is True


def test_write_confirm_redefine_marker_persists_to_the_builder_scope_and_round_trips():
    repository = _InMemorySettingsRepository()

    write_confirm_redefine_marker(repository, False)
    assert repository.get(SettingsScope.BUILDER, CONFIRM_REDEFINE_MARKER) is False
    assert read_confirm_redefine_marker(repository) is False

    write_confirm_redefine_marker(repository, True)
    assert repository.get(SettingsScope.BUILDER, CONFIRM_REDEFINE_MARKER) is True
    assert read_confirm_redefine_marker(repository) is True
