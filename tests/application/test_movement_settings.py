from labyrinthes.application.errors import SettingCorruptError, SettingNotFoundError
from labyrinthes.application.movement_settings import (
    read_movement_mode,
    read_movement_speed,
    write_movement_mode,
    write_movement_speed,
)
from labyrinthes.application.settings_keys import MOVEMENT_MODE, MOVEMENT_SPEED
from labyrinthes.application.settings_repository import SettingsRepository, SettingsScope
from labyrinthes.domain.movement_mode import MovementMode
from labyrinthes.domain.movement_speed import MovementSpeed


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

    assert read_movement_mode(repository) is MovementMode.SMOOTH
    assert read_movement_speed(repository) is MovementSpeed.NORMAL


def test_reads_defaults_when_the_settings_file_is_corrupted():
    repository = _CorruptSettingsRepository()

    assert read_movement_mode(repository) is MovementMode.SMOOTH
    assert read_movement_speed(repository) is MovementSpeed.NORMAL


def test_reads_valid_stored_values():
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.GAME, MOVEMENT_MODE, "discrete")
    repository.set(SettingsScope.GAME, MOVEMENT_SPEED, "fast")

    assert read_movement_mode(repository) is MovementMode.DISCRETE
    assert read_movement_speed(repository) is MovementSpeed.FAST


def test_mode_falls_back_independently_when_speed_is_set():
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.GAME, MOVEMENT_SPEED, "slow")

    assert read_movement_mode(repository) is MovementMode.SMOOTH
    assert read_movement_speed(repository) is MovementSpeed.SLOW


def test_falls_back_to_the_default_when_a_stored_value_is_not_a_valid_member():
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.GAME, MOVEMENT_MODE, "turbo")
    repository.set(SettingsScope.GAME, MOVEMENT_SPEED, 42)

    assert read_movement_mode(repository) is MovementMode.SMOOTH
    assert read_movement_speed(repository) is MovementSpeed.NORMAL


def test_never_writes_on_read():
    class _ExplodingOnSetRepository(SettingsRepository):
        def get(self, scope, key):
            raise SettingNotFoundError("unset")

        def set(self, scope, key, value):
            raise AssertionError("read_movement_* must never call set()")

    read_movement_mode(_ExplodingOnSetRepository())
    read_movement_speed(_ExplodingOnSetRepository())


def test_write_round_trips_the_member_value_in_the_game_scope():
    repository = _InMemorySettingsRepository()

    write_movement_mode(repository, MovementMode.DISCRETE)
    write_movement_speed(repository, MovementSpeed.FAST)

    assert repository.get(SettingsScope.GAME, MOVEMENT_MODE) == "discrete"
    assert repository.get(SettingsScope.GAME, MOVEMENT_SPEED) == "fast"
    assert read_movement_mode(repository) is MovementMode.DISCRETE
    assert read_movement_speed(repository) is MovementSpeed.FAST
