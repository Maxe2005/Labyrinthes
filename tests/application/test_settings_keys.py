from labyrinthes.application import settings_keys

_KEY_NAMES = [
    "MAZE_MIN_COLUMNS",
    "MAZE_MAX_COLUMNS",
    "MAZE_MIN_ROWS",
    "MAZE_MAX_ROWS",
]


def test_key_constants_are_non_empty_strings():
    for name in _KEY_NAMES:
        value = getattr(settings_keys, name)

        assert isinstance(value, str)
        assert value != ""


def test_key_constants_are_distinct():
    values = [getattr(settings_keys, name) for name in _KEY_NAMES]

    assert len(values) == len(set(values))
