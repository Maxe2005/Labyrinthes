import dataclasses

from labyrinthes.adapters.tkinter.common.keybindings import keybinding
from labyrinthes.adapters.tkinter.common.tokens import Theme
from labyrinthes.adapters.tkinter.player.gameplay_placeholder import GameplayPlaceholder
from labyrinthes.adapters.tkinter.player.save_maze_dialog import SaveMazeDialog
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.position import Position


def _generated_maze(width=4, height=3) -> Maze:
    return Maze(
        grid=Grid.filled(width=width, height=height),
        entry=Position(row=0, col=0),
        exit=Position(row=height - 1, col=width - 1),
        kind=MazeKind.GENERATED,
        id=None,
    )


def _classic_maze(width=4, height=3) -> Maze:
    return Maze(
        grid=Grid.filled(width=width, height=height),
        entry=Position(row=0, col=0),
        exit=Position(row=height - 1, col=width - 1),
        kind=MazeKind.CLASSIC,
        id=None,
    )


class ExplodingMazeRepository:
    def save(self, maze, name):
        raise AssertionError("save() must not be called")

    def load(self, name, kind):
        raise AssertionError("load() must not be called")

    def find_by_id(self, maze_id):
        raise AssertionError("find_by_id() must not be called")

    def list_names(self, kind):
        raise AssertionError("list_names() must not be called")


def test_a_generated_maze_shows_the_save_button(tk_root, fake_maze_repository):
    placeholder = GameplayPlaceholder(
        tk_root, _generated_maze(), Theme.LIGHT, maze_repository=fake_maze_repository
    )

    assert placeholder._save_button.winfo_exists()


def test_a_classic_maze_shows_no_save_button(tk_root, fake_maze_repository):
    placeholder = GameplayPlaceholder(
        tk_root, _classic_maze(), Theme.LIGHT, maze_repository=fake_maze_repository
    )

    assert not hasattr(placeholder, "_save_button")


def test_mounting_a_generated_maze_never_touches_the_repository(tk_root):
    # No repository method is called just from mounting -- only opening the
    # Save dialog (list_names) or confirming a save (save) touches it.
    placeholder = GameplayPlaceholder(
        tk_root, _generated_maze(), Theme.LIGHT, maze_repository=ExplodingMazeRepository()
    )

    assert placeholder._save_button.winfo_exists()


def test_clicking_save_opens_a_dialog_prefilled_with_existing_saved_random_names(
    tk_root, fake_maze_repository
):
    # `FakeMazeRepository.save()` keys by the maze's own `kind`, so seed a
    # maze that already carries `SAVED_RANDOM`.
    existing = dataclasses.replace(_generated_maze(), kind=MazeKind.SAVED_RANDOM)
    fake_maze_repository.save(existing, "existing")
    placeholder = GameplayPlaceholder(
        tk_root, _generated_maze(), Theme.LIGHT, maze_repository=fake_maze_repository
    )

    placeholder._on_save_clicked()

    dialogs = [c for c in placeholder.winfo_children() if isinstance(c, SaveMazeDialog)]
    assert len(dialogs) == 1
    assert dialogs[0]._existing_names == ["existing"]


def test_confirming_save_calls_repository_save_once_with_the_transitioned_kind(
    tk_root, fake_maze_repository
):
    placeholder = GameplayPlaceholder(
        tk_root, _generated_maze(), Theme.LIGHT, maze_repository=fake_maze_repository
    )

    placeholder._on_save_confirmed("forest")

    assert fake_maze_repository.list_names(MazeKind.SAVED_RANDOM) == ["forest"]
    saved = fake_maze_repository.load("forest", MazeKind.SAVED_RANDOM)
    assert saved.kind == MazeKind.SAVED_RANDOM
    # AC: "the returned Maze carries ... a freshly minted MazeId".
    assert saved.id is not None


def test_confirming_save_updates_the_placeholders_own_maze_and_hides_save(
    tk_root, fake_maze_repository
):
    placeholder = GameplayPlaceholder(
        tk_root, _generated_maze(), Theme.LIGHT, maze_repository=fake_maze_repository
    )

    placeholder._on_save_confirmed("forest")

    assert placeholder._maze.kind == MazeKind.SAVED_RANDOM
    assert placeholder._maze.id is not None
    assert not hasattr(placeholder, "_save_button")


def test_confirming_an_overwrite_through_the_full_dialog_flow_saves_once(
    tk_root, fake_maze_repository
):
    # End-to-end coverage for the I/O matrix's collision rows, driven
    # through `GameplayPlaceholder`'s real Save button and `SaveMazeDialog`
    # (not just `_on_save_confirmed` directly, and not just the dialog in
    # isolation against an `on_confirm` stub) -- closes the gap where
    # neither existing suite exercised Save -> collision -> Overwrite ->
    # repository-save as one full cycle.
    existing = dataclasses.replace(_generated_maze(), kind=MazeKind.SAVED_RANDOM)
    fake_maze_repository.save(existing, "forest")
    placeholder = GameplayPlaceholder(
        tk_root, _generated_maze(), Theme.LIGHT, maze_repository=fake_maze_repository
    )

    placeholder._on_save_clicked()
    dialog = next(c for c in placeholder.winfo_children() if isinstance(c, SaveMazeDialog))
    dialog._name_entry.delete(0, "end")
    dialog._name_entry.insert(0, "forest")

    dialog._on_save_clicked()  # first click: arms, warns, does not save
    assert fake_maze_repository.list_names(MazeKind.SAVED_RANDOM) == ["forest"]
    dialog._on_save_clicked()  # second click: confirms the overwrite

    assert fake_maze_repository.list_names(MazeKind.SAVED_RANDOM) == ["forest"]
    saved = fake_maze_repository.load("forest", MazeKind.SAVED_RANDOM)
    assert saved.kind == MazeKind.SAVED_RANDOM
    assert placeholder._maze.kind == MazeKind.SAVED_RANDOM
    assert not hasattr(placeholder, "_save_button")


def test_repository_is_untouched_until_save_is_actually_confirmed(tk_root, fake_maze_repository):
    placeholder = GameplayPlaceholder(
        tk_root, _generated_maze(), Theme.LIGHT, maze_repository=fake_maze_repository
    )
    placeholder._on_save_clicked()

    assert fake_maze_repository.list_names(MazeKind.SAVED_RANDOM) == []


def test_save_shortcut_is_registered_while_the_save_button_exists(tk_root, fake_maze_repository):
    GameplayPlaceholder(
        tk_root, _generated_maze(), Theme.LIGHT, maze_repository=fake_maze_repository
    )
    save_kb = keybinding("save_maze")

    assert tk_root.bind_all(save_kb.event) != ""


def test_save_shortcut_unregisters_once_the_maze_is_saved_and_the_button_rebuilt(
    tk_root, fake_maze_repository
):
    placeholder = GameplayPlaceholder(
        tk_root, _generated_maze(), Theme.LIGHT, maze_repository=fake_maze_repository
    )
    save_kb = keybinding("save_maze")
    assert tk_root.bind_all(save_kb.event) != ""

    placeholder._on_save_confirmed("forest")
    tk_root.update()

    assert tk_root.bind_all(save_kb.event) == ""
