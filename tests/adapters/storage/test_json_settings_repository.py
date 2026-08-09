import pytest

from labyrinthes.adapters.storage.errors import InvalidSettingKeyError
from labyrinthes.adapters.storage.json_settings_repository import JsonSettingsRepository
from labyrinthes.adapters.storage.settings_paths import setting_file_path
from labyrinthes.application.errors import SettingCorruptError, SettingNotFoundError
from labyrinthes.application.settings_repository import SettingsScope


def test_get_on_a_key_never_set_raises_setting_not_found_error(tmp_path):
    repository = JsonSettingsRepository(root=tmp_path)

    with pytest.raises(SettingNotFoundError):
        repository.get(SettingsScope.BUILDER, "foo")


@pytest.mark.parametrize(
    "value",
    ["hello", 42, 3.14, True, False, ("a", "b", "c"), ()],
)
def test_set_then_get_round_trips_each_setting_value_type(tmp_path, value):
    repository = JsonSettingsRepository(root=tmp_path)

    repository.set(SettingsScope.BUILDER, "foo", value)
    loaded = repository.get(SettingsScope.BUILDER, "foo")

    assert loaded == value
    assert type(loaded) is type(value)


def test_set_on_one_scope_leaves_other_scopes_untouched(tmp_path):
    repository = JsonSettingsRepository(root=tmp_path)
    repository.set(SettingsScope.GAME, "b", "original")

    repository.set(SettingsScope.BUILDER, "a", "x")

    assert repository.get(SettingsScope.GAME, "b") == "original"


def test_set_on_one_key_leaves_other_keys_in_the_same_scope_untouched(tmp_path):
    repository = JsonSettingsRepository(root=tmp_path)
    repository.set(SettingsScope.BUILDER, "other", "original")

    repository.set(SettingsScope.BUILDER, "a", "x")

    assert repository.get(SettingsScope.BUILDER, "other") == "original"


def test_shared_scope_observed_identically_across_two_repository_instances(tmp_path):
    repo_1 = JsonSettingsRepository(root=tmp_path)
    repo_2 = JsonSettingsRepository(root=tmp_path)

    repo_1.set(SettingsScope.SHARED, "k", "v")

    assert repo_2.get(SettingsScope.SHARED, "k") == "v"


def test_set_with_an_empty_key_raises_invalid_setting_key_error(tmp_path):
    repository = JsonSettingsRepository(root=tmp_path)

    with pytest.raises(InvalidSettingKeyError):
        repository.set(SettingsScope.BUILDER, "", "x")


def test_set_with_a_path_separator_containing_key_raises_invalid_setting_key_error(tmp_path):
    repository = JsonSettingsRepository(root=tmp_path)

    with pytest.raises(InvalidSettingKeyError):
        repository.set(SettingsScope.BUILDER, "a/b", "x")


def test_re_set_an_existing_key_with_a_new_value_returns_the_new_value(tmp_path):
    repository = JsonSettingsRepository(root=tmp_path)
    repository.set(SettingsScope.BUILDER, "a", "v1")

    repository.set(SettingsScope.BUILDER, "a", "v2")

    assert repository.get(SettingsScope.BUILDER, "a") == "v2"


def test_get_on_a_malformed_settings_file_raises_setting_corrupt_error(tmp_path):
    repository = JsonSettingsRepository(root=tmp_path)
    path = setting_file_path(tmp_path, SettingsScope.BUILDER, "foo")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not valid json{{{", encoding="utf-8")

    with pytest.raises(SettingCorruptError):
        repository.get(SettingsScope.BUILDER, "foo")


def test_get_raises_setting_not_found_error_on_a_toctou_race(tmp_path, monkeypatch):
    # The file passes the `is_file()` existence check, but has vanished (or
    # been replaced by something unreadable) by the time `get()` actually
    # opens it -- indistinguishable, from the caller's perspective, from a
    # key that was never set.
    repository = JsonSettingsRepository(root=tmp_path)
    monkeypatch.setattr(
        "labyrinthes.adapters.storage.json_settings_repository.Path.is_file", lambda self: True
    )

    with pytest.raises(SettingNotFoundError):
        repository.get(SettingsScope.BUILDER, "foo")
