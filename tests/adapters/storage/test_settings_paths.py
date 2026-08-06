import pytest

from labyrinthes.adapters.storage.errors import InvalidSettingKeyError
from labyrinthes.adapters.storage.settings_paths import setting_file_path
from labyrinthes.application.settings_repository import SettingsScope


@pytest.mark.parametrize(
    ("scope", "expected_subfolder"),
    [
        (SettingsScope.BUILDER, "builder"),
        (SettingsScope.GAME, "game"),
        (SettingsScope.SHARED, "shared"),
    ],
)
def test_setting_file_path_uses_one_subfolder_per_scope_value(tmp_path, scope, expected_subfolder):
    path = setting_file_path(tmp_path, scope, "foo")

    assert path == tmp_path / expected_subfolder / "foo.json"


def test_setting_file_path_rejects_empty_key(tmp_path):
    with pytest.raises(InvalidSettingKeyError):
        setting_file_path(tmp_path, SettingsScope.BUILDER, "")


@pytest.mark.parametrize("key", ["a/b", "/a", "a/", "a\\b"])
def test_setting_file_path_rejects_path_separators_in_key(tmp_path, key):
    with pytest.raises(InvalidSettingKeyError):
        setting_file_path(tmp_path, SettingsScope.BUILDER, key)
