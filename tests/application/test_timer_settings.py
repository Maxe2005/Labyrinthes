from labyrinthes.application.errors import SettingCorruptError, SettingNotFoundError
from labyrinthes.application.timer_settings import (
    read_timer_limit_enabled,
    read_timer_limit_seconds,
    write_timer_limit_enabled,
    write_timer_limit_seconds,
)
from labyrinthes.application.settings_keys import TIMER_LIMIT_ENABLED, TIMER_LIMIT_SECONDS
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

    assert read_timer_limit_enabled(repository) is False
    assert read_timer_limit_seconds(repository) == 60


def test_reads_defaults_when_the_settings_file_is_corrupted():
    repository = _CorruptSettingsRepository()

    assert read_timer_limit_enabled(repository) is False
    assert read_timer_limit_seconds(repository) == 60


def test_reads_valid_stored_values():
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.GAME, TIMER_LIMIT_ENABLED, "true")
    repository.set(SettingsScope.GAME, TIMER_LIMIT_SECONDS, "120")

    assert read_timer_limit_enabled(repository) is True
    assert read_timer_limit_seconds(repository) == 120


def test_enabled_falls_back_independently_when_seconds_is_set():
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.GAME, TIMER_LIMIT_SECONDS, "90")

    assert read_timer_limit_enabled(repository) is False
    assert read_timer_limit_seconds(repository) == 90


def test_seconds_falls_back_independently_when_enabled_is_set():
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.GAME, TIMER_LIMIT_ENABLED, "true")

    assert read_timer_limit_enabled(repository) is True
    assert read_timer_limit_seconds(repository) == 60


def test_enabled_falls_back_to_default_when_stored_value_is_invalid():
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.GAME, TIMER_LIMIT_ENABLED, "not_a_bool")

    assert read_timer_limit_enabled(repository) is False


def test_seconds_falls_back_to_default_when_stored_value_is_invalid():
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.GAME, TIMER_LIMIT_SECONDS, "not_a_number")

    assert read_timer_limit_seconds(repository) == 60


def test_never_writes_on_read():
    class _ExplodingOnSetRepository(SettingsRepository):
        def get(self, scope, key):
            raise SettingNotFoundError("unset")

        def set(self, scope, key, value):
            raise AssertionError("read_timer_limit_* must never call set()")

    read_timer_limit_enabled(_ExplodingOnSetRepository())
    read_timer_limit_seconds(_ExplodingOnSetRepository())


def test_write_round_trips_the_value_in_the_game_scope():
    repository = _InMemorySettingsRepository()

    write_timer_limit_enabled(repository, True)
    write_timer_limit_seconds(repository, 90)

    assert repository.get(SettingsScope.GAME, TIMER_LIMIT_ENABLED) == "true"
    assert repository.get(SettingsScope.GAME, TIMER_LIMIT_SECONDS) == "90"
    assert read_timer_limit_enabled(repository) is True
    assert read_timer_limit_seconds(repository) == 90