import pytest

from labyrinthes.application.settings_repository import (
    SettingsRepository,
    SettingsScope,
    SettingValue,
)


class _CompleteSettingsRepository(SettingsRepository):
    def get(self, scope: SettingsScope, key: str) -> SettingValue:
        return "value"

    def set(self, scope: SettingsScope, key: str, value: SettingValue) -> None:
        pass


class _IncompleteSettingsRepository(SettingsRepository):
    def get(self, scope: SettingsScope, key: str) -> SettingValue:
        return "value"

    # set intentionally omitted


def test_settings_scope_has_exactly_builder_game_shared():
    assert {member.name: member.value for member in SettingsScope} == {
        "BUILDER": "builder",
        "GAME": "game",
        "SHARED": "shared",
    }


def test_settings_repository_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        SettingsRepository()


def test_complete_subclass_instantiates_and_is_a_settings_repository():
    repository = _CompleteSettingsRepository()

    assert isinstance(repository, SettingsRepository)


def test_incomplete_subclass_cannot_be_instantiated():
    with pytest.raises(TypeError):
        _IncompleteSettingsRepository()
