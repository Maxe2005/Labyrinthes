import tkinter as tk

from labyrinthes.adapters.tkinter.common.tokens import Theme
from labyrinthes.adapters.tkinter.player.classic_gallery import ClassicMazeGallery
from labyrinthes.adapters.tkinter.player.generate_random_dialog import GenerateRandomDialog
from labyrinthes.app.router import ScreenId
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.position import Position


def _gallery(tk_root, repository, navigate, settings_repository):
    return ClassicMazeGallery(
        tk_root,
        theme=Theme.LIGHT,
        maze_repository=repository,
        settings_repository=settings_repository,
        navigate=navigate,
    )


def test_cold_open_shows_the_first_classic_maze_with_pager_and_play_controls(
    tk_root, seeded_maze_repository, navigate_stub, fake_settings_repository
):
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, seeded_maze_repository, navigate, fake_settings_repository)

    assert gallery._position_label.cget("text") == "Classic Maze 1 of 3"
    assert gallery._jump_entry.get() == "1"
    assert gallery._play_button.winfo_exists()
    assert gallery._previous_button.winfo_exists()
    assert gallery._next_button.winfo_exists()
    assert gallery._restart_button.winfo_exists()


def test_next_at_last_index_is_a_no_op(
    tk_root, seeded_maze_repository, navigate_stub, fake_settings_repository
):
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, seeded_maze_repository, navigate, fake_settings_repository)
    gallery._on_next()
    gallery._on_next()
    assert gallery._position_label.cget("text") == "Classic Maze 3 of 3"

    gallery._on_next()

    assert gallery._index == 2
    assert gallery._position_label.cget("text") == "Classic Maze 3 of 3"


def test_previous_at_first_index_is_a_no_op(
    tk_root, seeded_maze_repository, navigate_stub, fake_settings_repository
):
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, seeded_maze_repository, navigate, fake_settings_repository)

    gallery._on_previous()

    assert gallery._index == 0
    assert gallery._position_label.cget("text") == "Classic Maze 1 of 3"


def test_restart_mid_browse_resets_to_the_first_maze(
    tk_root, seeded_maze_repository, navigate_stub, fake_settings_repository
):
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, seeded_maze_repository, navigate, fake_settings_repository)
    gallery._on_next()
    gallery._on_next()
    assert gallery._index == 2

    gallery._on_restart()

    assert gallery._index == 0
    assert gallery._position_label.cget("text") == "Classic Maze 1 of 3"


def test_valid_jump_moves_to_the_requested_1_based_maze(
    tk_root, seeded_maze_repository, navigate_stub, fake_settings_repository
):
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, seeded_maze_repository, navigate, fake_settings_repository)
    gallery._jump_entry.delete(0, "end")
    gallery._jump_entry.insert(0, "3")

    gallery._on_jump()

    assert gallery._index == 2
    assert gallery._position_label.cget("text") == "Classic Maze 3 of 3"


def test_out_of_range_jump_reverts_the_entry_without_changing_the_index(
    tk_root, seeded_maze_repository, navigate_stub, fake_settings_repository
):
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, seeded_maze_repository, navigate, fake_settings_repository)
    gallery._jump_entry.delete(0, "end")
    gallery._jump_entry.insert(0, "9")

    gallery._on_jump()

    assert gallery._index == 0
    assert gallery._jump_entry.get() == "1"
    assert gallery._position_label.cget("text") == "Classic Maze 1 of 3"


def test_non_numeric_jump_reverts_the_entry_without_changing_the_index(
    tk_root, seeded_maze_repository, navigate_stub, fake_settings_repository
):
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, seeded_maze_repository, navigate, fake_settings_repository)
    gallery._jump_entry.delete(0, "end")
    gallery._jump_entry.insert(0, "abc")

    gallery._on_jump()

    assert gallery._index == 0
    assert gallery._jump_entry.get() == "1"


def test_cold_open_with_no_classics_shows_empty_state_and_no_pager_or_play(
    tk_root, fake_maze_repository, navigate_stub, fake_settings_repository
):
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, fake_maze_repository, navigate, fake_settings_repository)

    assert not hasattr(gallery, "_play_button")
    assert not hasattr(gallery, "_previous_button")
    assert gallery._generate_random_button.winfo_exists()


def test_empty_state_shows_an_inline_message(
    tk_root, fake_maze_repository, navigate_stub, fake_settings_repository
):
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, fake_maze_repository, navigate, fake_settings_repository)

    labels = [
        child.cget("text") for child in gallery.winfo_children() if isinstance(child, tk.Label)
    ]
    assert any("No classic mazes were found" in text for text in labels)


def test_populated_state_also_shows_a_generate_random_button(
    tk_root, seeded_maze_repository, navigate_stub, fake_settings_repository
):
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, seeded_maze_repository, navigate, fake_settings_repository)

    assert gallery._generate_random_button.winfo_exists()


def test_play_navigates_to_player_with_the_currently_browsed_maze(
    tk_root, seeded_maze_repository, navigate_stub, fake_settings_repository
):
    navigate, calls = navigate_stub
    gallery = _gallery(tk_root, seeded_maze_repository, navigate, fake_settings_repository)
    gallery._on_next()  # browse to index 1 ("bravo")

    gallery._on_play()

    assert len(calls) == 1
    screen_id, maze = calls[0]
    assert screen_id == ScreenId.PLAYER
    assert maze == seeded_maze_repository.load("bravo", MazeKind.CLASSIC)


def test_jump_entry_locally_consumes_n_before_the_global_generate_random_shortcut(
    tk_root, seeded_maze_repository, navigate_stub, fake_settings_repository
):
    # Regression for the review finding: the global "n" (generate_random)
    # shortcut is registered via `bind_all()`, which Tk dispatches *after*
    # a widget's own instance bindings -- so the jump entry must have its
    # own "n"/"N" bindings that return "break" to stop the event there,
    # rather than falling through to `bind_all()`. `tk_root` is withdrawn
    # (unreliable real X11 KeyPress synthesis, per this suite's convention
    # -- see test_breadcrumb_home_segment_is_clickable...), so this asserts
    # the binding is actually registered rather than synthesizing the key.
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, seeded_maze_repository, navigate, fake_settings_repository)

    assert gallery._jump_entry.bind("<KeyPress-n>") != ""
    assert gallery._jump_entry.bind("<KeyPress-N>") != ""


# -- generate-random dialog (Story 2.2) ---------------------------------------------------


def test_generate_random_opens_a_dialog_parented_to_the_gallery(
    tk_root, seeded_maze_repository, navigate_stub, fake_settings_repository
):
    navigate, calls = navigate_stub
    gallery = _gallery(tk_root, seeded_maze_repository, navigate, fake_settings_repository)

    gallery._on_generate_random()

    dialogs = [c for c in gallery.winfo_children() if isinstance(c, GenerateRandomDialog)]
    assert len(dialogs) == 1
    assert dialogs[0].master is gallery
    assert calls == []


def test_generate_random_dialog_uses_the_default_bounds_when_none_are_stored(
    tk_root, seeded_maze_repository, navigate_stub, fake_settings_repository
):
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, seeded_maze_repository, navigate, fake_settings_repository)

    gallery._on_generate_random()

    dialog = [c for c in gallery.winfo_children() if isinstance(c, GenerateRandomDialog)][0]
    assert dialog._entries["columns"].get() == "3"
    assert dialog._entries["rows"].get() == "3"


def test_confirming_generation_navigates_to_player_with_a_generated_maze(
    tk_root, seeded_maze_repository, navigate_stub, fake_settings_repository
):
    navigate, calls = navigate_stub
    gallery = _gallery(tk_root, seeded_maze_repository, navigate, fake_settings_repository)

    gallery._on_generation_confirmed(10, 8, Position(row=0, col=0))

    assert len(calls) == 1
    screen_id, maze = calls[0]
    assert screen_id == ScreenId.PLAYER
    assert isinstance(maze, Maze)
    assert maze.kind == MazeKind.GENERATED
    assert maze.id is None
    assert maze.grid.width == 10
    assert maze.grid.height == 8
    assert maze.entry == Position(row=0, col=0)
    assert maze.exit != maze.entry


def test_confirming_generation_via_the_dialogs_own_confirm_callback_navigates(
    tk_root, seeded_maze_repository, navigate_stub, fake_settings_repository
):
    # End-to-end through the real dialog, not just `_on_generation_confirmed`
    # called directly -- proves the callback wiring itself is correct.
    navigate, calls = navigate_stub
    gallery = _gallery(tk_root, seeded_maze_repository, navigate, fake_settings_repository)
    gallery._on_generate_random()
    dialog = [c for c in gallery.winfo_children() if isinstance(c, GenerateRandomDialog)][0]
    dialog._entries["columns"].delete(0, "end")
    dialog._entries["columns"].insert(0, "10")
    dialog._entries["rows"].delete(0, "end")
    dialog._entries["rows"].insert(0, "8")

    dialog._on_generate_clicked()

    assert len(calls) == 1
    screen_id, maze = calls[0]
    assert screen_id == ScreenId.PLAYER
    assert maze.kind == MazeKind.GENERATED
    assert not dialog.winfo_exists()
