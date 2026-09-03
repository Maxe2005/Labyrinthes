from labyrinthes.application.errors import SettingCorruptError, SettingNotFoundError
from labyrinthes.application.settings_keys import WINDOW_HEIGHT, WINDOW_WIDTH
from labyrinthes.application.settings_repository import SettingsRepository, SettingsScope
from labyrinthes.application.window_settings import (
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    clamp_window_height,
    clamp_window_width,
    read_window_size,
    write_window_height,
    write_window_width,
)


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


# -- clamp helpers -----------------------------------------------------------


def test_clamp_window_width_leaves_an_in_range_value_untouched():
    assert clamp_window_width(1280, screen_width=1920) == 1280


def test_clamp_window_width_clamps_up_to_the_minimum():
    assert clamp_window_width(50, screen_width=1920) == MIN_WINDOW_WIDTH


def test_clamp_window_width_clamps_down_to_the_screen_width():
    assert clamp_window_width(99999, screen_width=1920) == 1920


def test_clamp_window_width_never_inverts_the_range_for_a_tiny_screen():
    # A screen narrower than the minimum still yields the minimum, never a
    # `max > min` inverted range.
    assert clamp_window_width(500, screen_width=400) == MIN_WINDOW_WIDTH


def test_clamp_window_height_leaves_an_in_range_value_untouched():
    assert clamp_window_height(800, screen_height=1080) == 800


def test_clamp_window_height_clamps_up_to_the_minimum():
    assert clamp_window_height(50, screen_height=1080) == MIN_WINDOW_HEIGHT


def test_clamp_window_height_clamps_down_to_the_screen_height():
    assert clamp_window_height(99999, screen_height=1080) == 1080


# -- read_window_size ---------------------------------------------------------


def test_reads_the_default_size_when_nothing_is_stored():
    repository = _InMemorySettingsRepository()

    assert read_window_size(repository, 1920, 1080) == (
        DEFAULT_WINDOW_WIDTH,
        DEFAULT_WINDOW_HEIGHT,
    )


def test_reads_the_default_size_when_the_settings_file_is_corrupted():
    repository = _CorruptSettingsRepository()

    assert read_window_size(repository, 1920, 1080) == (
        DEFAULT_WINDOW_WIDTH,
        DEFAULT_WINDOW_HEIGHT,
    )


def test_reads_a_stored_valid_size():
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.SHARED, WINDOW_WIDTH, 1024)
    repository.set(SettingsScope.SHARED, WINDOW_HEIGHT, 768)

    assert read_window_size(repository, 1920, 1080) == (1024, 768)


def test_falls_back_to_the_default_for_a_non_int_stored_value():
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.SHARED, WINDOW_WIDTH, "not-an-int")
    repository.set(SettingsScope.SHARED, WINDOW_HEIGHT, "not-an-int")

    assert read_window_size(repository, 1920, 1080) == (
        DEFAULT_WINDOW_WIDTH,
        DEFAULT_WINDOW_HEIGHT,
    )


def test_clamps_a_stored_out_of_bounds_size_to_the_given_screen_bounds():
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.SHARED, WINDOW_WIDTH, 50)
    repository.set(SettingsScope.SHARED, WINDOW_HEIGHT, 99999)

    width, height = read_window_size(repository, 1920, 1080)

    assert width == MIN_WINDOW_WIDTH
    assert height == 1080


def test_clamps_the_default_down_when_it_exceeds_a_small_screen():
    repository = _InMemorySettingsRepository()

    width, height = read_window_size(repository, 900, 700)

    assert width == 900
    assert height == 700


def test_never_writes_on_read():
    class _ExplodingOnSetRepository(SettingsRepository):
        def get(self, scope, key):
            raise SettingNotFoundError("unset")

        def set(self, scope, key, value):
            raise AssertionError("read_window_size must never call set()")

    read_window_size(_ExplodingOnSetRepository(), 1920, 1080)


# -- write_window_width / write_window_height ---------------------------------


def test_writes_an_in_range_width_in_the_shared_scope_and_reads_it_back():
    repository = _InMemorySettingsRepository()

    write_window_width(repository, 1440, screen_width=1920)

    assert repository.get(SettingsScope.SHARED, WINDOW_WIDTH) == 1440
    assert read_window_size(repository, 1920, 1080)[0] == 1440


def test_write_window_width_clamps_an_out_of_bounds_value_before_persisting():
    repository = _InMemorySettingsRepository()

    write_window_width(repository, 99999, screen_width=1920)

    assert repository.get(SettingsScope.SHARED, WINDOW_WIDTH) == 1920


def test_writes_an_in_range_height_in_the_shared_scope_and_reads_it_back():
    repository = _InMemorySettingsRepository()

    write_window_height(repository, 900, screen_height=1080)

    assert repository.get(SettingsScope.SHARED, WINDOW_HEIGHT) == 900
    assert read_window_size(repository, 1920, 1080)[1] == 900


def test_write_window_height_clamps_an_out_of_bounds_value_before_persisting():
    repository = _InMemorySettingsRepository()

    write_window_height(repository, 50, screen_height=1080)

    assert repository.get(SettingsScope.SHARED, WINDOW_HEIGHT) == MIN_WINDOW_HEIGHT
