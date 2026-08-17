from labyrinthes.application.errors import SettingCorruptError, SettingNotFoundError
from labyrinthes.application.settings_keys import TIME_LIMIT_SECONDS
from labyrinthes.application.settings_repository import SettingsRepository, SettingsScope
from labyrinthes.application.time_limit_settings import read_time_limit, write_time_limit
from labyrinthes.domain.duration import Duration


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


def test_reads_none_when_nothing_is_stored():
    repository = _InMemorySettingsRepository()

    assert read_time_limit(repository) is None


def test_reads_none_when_the_settings_file_is_corrupted():
    repository = _CorruptSettingsRepository()

    assert read_time_limit(repository) is None


def test_reads_a_valid_positive_integer_seconds_limit_as_a_duration():
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.GAME, TIME_LIMIT_SECONDS, 60)

    assert read_time_limit(repository) == Duration(milliseconds=60000)


def test_reads_none_for_every_non_positive_or_non_int_stored_value():
    # `type(value) is int` strictly rejects bool/float/str; 0 and negatives
    # are "no limit" sentinels (the port has no delete).
    for stored in ("60", 3.9, True, 0, -5):
        repository = _InMemorySettingsRepository()
        repository.set(SettingsScope.GAME, TIME_LIMIT_SECONDS, stored)

        assert read_time_limit(repository) is None


def test_never_writes_on_read():
    class _ExplodingOnSetRepository(SettingsRepository):
        def get(self, scope, key):
            raise SettingNotFoundError("unset")

        def set(self, scope, key, value):
            raise AssertionError("read_time_limit must never call set()")

    read_time_limit(_ExplodingOnSetRepository())


def test_writes_a_none_limit_as_the_zero_sentinel_and_reads_back_none():
    repository = _InMemorySettingsRepository()

    write_time_limit(repository, None)

    assert repository.get(SettingsScope.GAME, TIME_LIMIT_SECONDS) == 0
    assert read_time_limit(repository) is None


def test_writes_a_limit_in_whole_seconds_in_the_game_scope_and_reads_it_back():
    repository = _InMemorySettingsRepository()

    write_time_limit(repository, Duration(milliseconds=75000))

    assert repository.get(SettingsScope.GAME, TIME_LIMIT_SECONDS) == 75
    assert read_time_limit(repository) == Duration(milliseconds=75000)
