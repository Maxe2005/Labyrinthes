import pytest

from labyrinthes.adapters.storage.settings_format import read_setting_value, write_setting_value


@pytest.mark.parametrize(
    "value",
    ["hello", 42, 3.14, True, False, ("a", "b", "c"), ()],
)
def test_round_trips_each_setting_value_type(tmp_path, value):
    path = tmp_path / "value.json"

    write_setting_value(path, value)
    loaded = read_setting_value(path)

    assert loaded == value
    assert type(loaded) is type(value)


def test_tuple_value_decodes_back_to_a_tuple_not_a_list(tmp_path):
    path = tmp_path / "value.json"

    write_setting_value(path, ("a", "b"))
    loaded = read_setting_value(path)

    assert isinstance(loaded, tuple)
    assert not isinstance(loaded, list)


def test_bool_value_stays_distinguishable_from_int(tmp_path):
    path = tmp_path / "value.json"

    write_setting_value(path, False)
    loaded = read_setting_value(path)

    assert loaded is False
    assert isinstance(loaded, bool)
