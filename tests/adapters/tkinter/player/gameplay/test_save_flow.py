"""GameplayScreen: the Save flow for a GENERATED maze (Story 2.3, ported)."""

import dataclasses

from labyrinthes.adapters.tkinter.common.keybindings import keybinding
from labyrinthes.adapters.tkinter.common.tokens import Theme
from labyrinthes.adapters.tkinter.player.gameplay import GameplayScreen
from labyrinthes.adapters.tkinter.player.save_maze_dialog import SaveMazeDialog
from labyrinthes.domain.maze import MazeKind
from tests.adapters.tkinter.player.gameplay._helpers import (
    ExplodingMazeRepository,
    _classic_maze,
    _generated_maze,
)


def test_a_generated_maze_shows_the_save_button(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _generated_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    assert screen._save_button.winfo_exists()
    # Story 4.10: the Save button is relocated into the right panel's
    # `save_zone`, under the Movement group -- not a standalone zone
    # packed directly under the screen.
    assert screen._save_button.master is screen._right_panel.save_zone


def test_a_classic_maze_shows_no_save_button(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    assert not hasattr(screen, "_save_button")


def test_mounting_a_generated_maze_never_touches_the_repository(tk_root, fake_settings_repository):
    screen = GameplayScreen(
        tk_root,
        _generated_maze(),
        Theme.LIGHT,
        maze_repository=ExplodingMazeRepository(),
        settings_repository=fake_settings_repository,
    )

    assert screen._save_button.winfo_exists()


def test_clicking_save_opens_a_dialog_prefilled_with_existing_saved_random_names(
    tk_root, fake_maze_repository, fake_settings_repository
):
    existing = dataclasses.replace(_generated_maze(), kind=MazeKind.SAVED_RANDOM)
    fake_maze_repository.save(existing, "existing")
    screen = GameplayScreen(
        tk_root,
        _generated_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    screen._on_save_clicked()

    dialogs = [c for c in screen.winfo_children() if isinstance(c, SaveMazeDialog)]
    assert len(dialogs) == 1
    assert dialogs[0]._existing_names == ["existing"]


def test_confirming_save_calls_repository_save_once_with_the_transitioned_kind(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _generated_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    screen._on_save_confirmed("forest")

    assert fake_maze_repository.list_names(MazeKind.SAVED_RANDOM) == ["forest"]
    saved = fake_maze_repository.load("forest", MazeKind.SAVED_RANDOM)
    assert saved.kind == MazeKind.SAVED_RANDOM
    assert saved.id is not None


def test_confirming_save_updates_the_screens_own_maze_and_hides_save(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _generated_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    screen._on_save_confirmed("forest")

    assert screen._maze.kind == MazeKind.SAVED_RANDOM
    assert screen._maze.id is not None
    assert not hasattr(screen, "_save_button")


def test_confirming_save_also_updates_the_sessions_own_maze(
    tk_root, fake_maze_repository, fake_settings_repository
):
    # `self._session.maze` must not silently diverge from `self._maze` --
    # a future reader of `session.maze.kind`/`id` should see the same
    # post-save value either way.
    screen = GameplayScreen(
        tk_root,
        _generated_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    screen._on_save_confirmed("forest")

    assert screen._session.maze is screen._maze
    assert screen._session.maze.kind == MazeKind.SAVED_RANDOM


def test_confirming_save_notifies_on_kind_changed_with_the_new_kind(
    tk_root, fake_maze_repository, fake_settings_repository
):
    # Lets a caller (`screen.py`, for its kind-derived breadcrumb label)
    # stay in sync with `self._maze.kind` across a save, without
    # `GameplayScreen` needing to know anything about breadcrumbs itself.
    kinds_seen = []
    screen = GameplayScreen(
        tk_root,
        _generated_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
        on_kind_changed=kinds_seen.append,
    )

    screen._on_save_confirmed("forest")

    assert kinds_seen == [MazeKind.SAVED_RANDOM]


def test_on_kind_changed_defaults_to_none_and_a_save_still_succeeds(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _generated_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    screen._on_save_confirmed("forest")  # must not raise with no callback given

    assert screen._maze.kind == MazeKind.SAVED_RANDOM


def test_confirming_save_does_not_rebuild_the_hud_or_canvas(
    tk_root, fake_maze_repository, fake_settings_repository
):
    # Story 2.4's own addition: saving only rebuilds the save-zone, not the
    # whole screen -- the HUD chips and maze canvas built in `__init__`
    # must be the exact same widget instances afterward.
    screen = GameplayScreen(
        tk_root,
        _generated_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    canvas_before = screen._maze_canvas
    time_chip_before = screen._hud._time_chip

    screen._on_save_confirmed("forest")

    assert screen._maze_canvas is canvas_before
    assert screen._hud._time_chip is time_chip_before


def test_confirming_an_overwrite_through_the_full_dialog_flow_saves_once(
    tk_root, fake_maze_repository, fake_settings_repository
):
    existing = dataclasses.replace(_generated_maze(), kind=MazeKind.SAVED_RANDOM)
    fake_maze_repository.save(existing, "forest")
    screen = GameplayScreen(
        tk_root,
        _generated_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    screen._on_save_clicked()
    dialog = next(c for c in screen.winfo_children() if isinstance(c, SaveMazeDialog))
    dialog._name_entry.delete(0, "end")
    dialog._name_entry.insert(0, "forest")

    dialog._on_save_clicked()  # first click: arms, warns, does not save
    assert fake_maze_repository.list_names(MazeKind.SAVED_RANDOM) == ["forest"]
    dialog._on_save_clicked()  # second click: confirms the overwrite

    assert fake_maze_repository.list_names(MazeKind.SAVED_RANDOM) == ["forest"]
    saved = fake_maze_repository.load("forest", MazeKind.SAVED_RANDOM)
    assert saved.kind == MazeKind.SAVED_RANDOM
    assert screen._maze.kind == MazeKind.SAVED_RANDOM
    assert not hasattr(screen, "_save_button")


def test_repository_is_untouched_until_save_is_actually_confirmed(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _generated_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    screen._on_save_clicked()

    assert fake_maze_repository.list_names(MazeKind.SAVED_RANDOM) == []


def test_save_shortcut_is_registered_while_the_save_button_exists(
    tk_root, fake_maze_repository, fake_settings_repository
):
    GameplayScreen(
        tk_root,
        _generated_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    save_kb = keybinding("save_maze")

    assert tk_root.bind_all(save_kb.event) != ""


def test_save_shortcut_unregisters_once_the_maze_is_saved_and_the_button_rebuilt(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _generated_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    save_kb = keybinding("save_maze")
    assert tk_root.bind_all(save_kb.event) != ""

    screen._on_save_confirmed("forest")
    tk_root.update()

    assert tk_root.bind_all(save_kb.event) == ""
