from labyrinthes.adapters.storage.json_settings_repository import JsonSettingsRepository
from labyrinthes.adapters.tkinter.common.tokens import Theme
from labyrinthes.app.theme_controller import ThemeController
from labyrinthes.application.settings_keys import THEME
from labyrinthes.application.settings_repository import SettingsScope


def test_default_theme_is_light_when_nothing_persisted(tmp_path):
    repository = JsonSettingsRepository(root=tmp_path)

    controller = ThemeController(repository)

    assert controller.theme == Theme.LIGHT


def test_default_theme_is_light_when_the_persisted_value_is_not_a_recognized_theme(tmp_path):
    # A hand-edited or otherwise corrupted settings file could hold a value
    # that isn't "light"/"dark" -- `ThemeController` is the first
    # unconditional, every-launch consumer of this setting
    # (`composition_root.build_app()`), so this must degrade to the
    # default rather than crash the app before its window ever shows.
    repository = JsonSettingsRepository(root=tmp_path)
    repository.set(SettingsScope.SHARED, THEME, "purple")

    controller = ThemeController(repository)

    assert controller.theme == Theme.LIGHT


def test_toggle_flips_the_theme(tmp_path):
    repository = JsonSettingsRepository(root=tmp_path)
    controller = ThemeController(repository)

    controller.toggle()

    assert controller.theme == Theme.DARK


def test_toggle_twice_returns_to_the_original_theme(tmp_path):
    repository = JsonSettingsRepository(root=tmp_path)
    controller = ThemeController(repository)

    controller.toggle()
    controller.toggle()

    assert controller.theme == Theme.LIGHT


def test_toggle_persists_the_new_theme_via_the_settings_repository(tmp_path):
    repository = JsonSettingsRepository(root=tmp_path)
    controller = ThemeController(repository)

    controller.toggle()

    reloaded = ThemeController(repository)
    assert reloaded.theme == Theme.DARK


def test_toggle_notifies_subscribers_with_the_new_theme(tmp_path):
    repository = JsonSettingsRepository(root=tmp_path)
    controller = ThemeController(repository)
    calls = []
    controller.subscribe(lambda theme: calls.append(theme))

    controller.toggle()

    assert calls == [Theme.DARK]


def test_a_second_controller_built_against_the_same_root_loads_the_persisted_theme(tmp_path):
    first = ThemeController(JsonSettingsRepository(root=tmp_path))
    first.toggle()

    second = ThemeController(JsonSettingsRepository(root=tmp_path))

    assert second.theme == Theme.DARK
