import pytest

from labyrinthes.adapters.storage import settings_format
from labyrinthes.adapters.storage.settings_format import read_setting_value, write_setting_value
from labyrinthes.application.errors import SettingCorruptError


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


def test_malformed_json_content_raises_setting_corrupt_error(tmp_path):
    path = tmp_path / "value.json"
    path.write_text("not valid json{{{", encoding="utf-8")

    with pytest.raises(SettingCorruptError):
        read_setting_value(path)


def test_a_write_interrupted_partway_leaves_the_previous_file_intact(tmp_path, monkeypatch):
    path = tmp_path / "value.json"
    write_setting_value(path, "original")
    original_content = path.read_text(encoding="utf-8")

    def flaky_dump(value, handle):
        handle.write("partial garbage")
        raise RuntimeError("boom")

    monkeypatch.setattr(settings_format.json, "dump", flaky_dump)

    with pytest.raises(RuntimeError):
        write_setting_value(path, "new value")

    assert path.read_text(encoding="utf-8") == original_content
    assert list(tmp_path.iterdir()) == [path]
