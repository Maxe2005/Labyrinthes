from labyrinthes.application.errors import SettingCorruptError, SettingNotFoundError
from labyrinthes.application.maze_size_bounds import read_maze_size_bounds
from labyrinthes.application.settings_keys import (
    MAZE_MAX_COLUMNS,
    MAZE_MAX_ROWS,
    MAZE_MIN_COLUMNS,
    MAZE_MIN_ROWS,
)
from labyrinthes.application.settings_repository import SettingsRepository, SettingsScope
from labyrinthes.domain.maze_size_bounds import DEFAULT_MAZE_SIZE_BOUNDS, MazeSizeBounds


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
    """A `SettingsRepository` test double whose `get()` always raises `SettingCorruptError`."""

    def get(self, scope, key):
        raise SettingCorruptError("corrupted settings file")

    def set(self, scope, key, value):
        raise NotImplementedError


def test_returns_defaults_when_nothing_is_stored():
    repository = _InMemorySettingsRepository()

    bounds = read_maze_size_bounds(repository)

    assert bounds == DEFAULT_MAZE_SIZE_BOUNDS


def test_returns_defaults_when_the_settings_file_is_corrupted():
    bounds = read_maze_size_bounds(_CorruptSettingsRepository())

    assert bounds == DEFAULT_MAZE_SIZE_BOUNDS


def test_reads_all_four_stored_values_when_present():
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.SHARED, MAZE_MIN_COLUMNS, 5)
    repository.set(SettingsScope.SHARED, MAZE_MAX_COLUMNS, 40)
    repository.set(SettingsScope.SHARED, MAZE_MIN_ROWS, 4)
    repository.set(SettingsScope.SHARED, MAZE_MAX_ROWS, 20)

    bounds = read_maze_size_bounds(repository)

    assert bounds == MazeSizeBounds(min_columns=5, max_columns=40, min_rows=4, max_rows=20)


def test_falls_back_to_the_default_field_by_field_when_only_some_keys_are_set():
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.SHARED, MAZE_MIN_COLUMNS, 5)

    bounds = read_maze_size_bounds(repository)

    assert bounds == MazeSizeBounds(
        min_columns=5,
        max_columns=DEFAULT_MAZE_SIZE_BOUNDS.max_columns,
        min_rows=DEFAULT_MAZE_SIZE_BOUNDS.min_rows,
        max_rows=DEFAULT_MAZE_SIZE_BOUNDS.max_rows,
    )


def test_falls_back_to_the_default_when_a_stored_value_is_non_numeric():
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.SHARED, MAZE_MIN_COLUMNS, "not-a-number")
    repository.set(SettingsScope.SHARED, MAZE_MAX_COLUMNS, 40)

    bounds = read_maze_size_bounds(repository)

    assert bounds.min_columns == DEFAULT_MAZE_SIZE_BOUNDS.min_columns
    assert bounds.max_columns == 40


def test_never_writes_to_the_settings_repository():
    class _ExplodingOnSetRepository(SettingsRepository):
        def get(self, scope, key):
            raise SettingNotFoundError("unset")

        def set(self, scope, key, value):
            raise AssertionError("read_maze_size_bounds must never call set()")

    # Must not raise -- proves no `set()` call happens.
    read_maze_size_bounds(_ExplodingOnSetRepository())


# -- regression: review findings on non-positive/inverted stored bounds ------


def test_falls_back_to_the_default_when_a_stored_value_is_zero():
    # A stored `0` parses "successfully" as an int, so it isn't caught by
    # the non-numeric case above -- but `min_columns=0` would let
    # `validate_dimensions` wave through `width=0`, which
    # `generate_random_maze` then rejects with an uncaught
    # `DomainValidationError`. Must be rejected here instead.
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.SHARED, MAZE_MIN_COLUMNS, 0)

    bounds = read_maze_size_bounds(repository)

    assert bounds.min_columns == DEFAULT_MAZE_SIZE_BOUNDS.min_columns


def test_falls_back_to_the_default_when_a_stored_value_is_negative():
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.SHARED, MAZE_MIN_ROWS, -5)

    bounds = read_maze_size_bounds(repository)

    assert bounds.min_rows == DEFAULT_MAZE_SIZE_BOUNDS.min_rows


def test_falls_back_the_whole_columns_pair_when_min_exceeds_max():
    # Both values individually parse fine and are positive -- only
    # overriding `min_columns` past the still-default `max_columns` (50)
    # produces an inverted pair that `validate_dimensions` could never
    # satisfy for any width, permanently and silently soft-locking
    # "Generate". The whole pair must fall back to the defaults together,
    # not just the one overridden field.
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.SHARED, MAZE_MIN_COLUMNS, 100)

    bounds = read_maze_size_bounds(repository)

    assert bounds.min_columns == DEFAULT_MAZE_SIZE_BOUNDS.min_columns
    assert bounds.max_columns == DEFAULT_MAZE_SIZE_BOUNDS.max_columns


def test_falls_back_the_whole_rows_pair_when_min_exceeds_max():
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.SHARED, MAZE_MIN_ROWS, 999)

    bounds = read_maze_size_bounds(repository)

    assert bounds.min_rows == DEFAULT_MAZE_SIZE_BOUNDS.min_rows
    assert bounds.max_rows == DEFAULT_MAZE_SIZE_BOUNDS.max_rows


def test_a_valid_narrowed_pair_is_kept_as_is():
    # Confirms the inversion fallback doesn't over-fire on a legitimate,
    # deliberately narrowed (but still consistent) pair.
    repository = _InMemorySettingsRepository()
    repository.set(SettingsScope.SHARED, MAZE_MIN_COLUMNS, 10)
    repository.set(SettingsScope.SHARED, MAZE_MAX_COLUMNS, 20)

    bounds = read_maze_size_bounds(repository)

    assert bounds.min_columns == 10
    assert bounds.max_columns == 20
