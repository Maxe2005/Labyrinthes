import tkinter as tk

from labyrinthes.adapters.tkinter.common.confirm_dialog import ConfirmDialog
from labyrinthes.adapters.tkinter.common.tokens import Theme
from labyrinthes.adapters.tkinter.player.classic_gallery import ClassicMazeGallery
from labyrinthes.adapters.tkinter.player.generate_random_dialog import GenerateRandomDialog
from labyrinthes.app.router import ScreenId
from labyrinthes.application.confirmation_settings import (
    read_confirm_invalid_input,
    write_confirm_invalid_input,
    write_confirm_switch_maze,
)
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.position import Position
from tests.adapters.tkinter.player.conftest import saved_random_maze


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
    assert any("No classic or saved mazes were found" in text for text in labels)


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


def test_no_saved_random_mazes_leaves_classic_only_numbering_unchanged(
    tk_root, seeded_maze_repository, navigate_stub, fake_settings_repository
):
    # No saved-random mazes seeded -- the combined `self._entries` list is
    # classic-only, so the position label stays byte-for-byte the pre-Story
    # 2.3 text (Design Notes: contiguous classics-first ordering).
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, seeded_maze_repository, navigate, fake_settings_repository)

    assert gallery._position_label.cget("text") == "Classic Maze 1 of 3"


def test_saved_random_mazes_are_listed_after_classics_in_the_same_pager(
    tk_root, seeded_maze_repository_with_saved_random, navigate_stub, fake_settings_repository
):
    navigate, _ = navigate_stub
    gallery = _gallery(
        tk_root, seeded_maze_repository_with_saved_random, navigate, fake_settings_repository
    )

    assert gallery._entries == [
        (MazeKind.CLASSIC, "alpha"),
        (MazeKind.CLASSIC, "bravo"),
        (MazeKind.CLASSIC, "charlie"),
        (MazeKind.SAVED_RANDOM, "delta"),
        (MazeKind.SAVED_RANDOM, "echo"),
    ]


def test_position_label_for_a_saved_random_entry_uses_the_overall_combined_index(
    tk_root, seeded_maze_repository_with_saved_random, navigate_stub, fake_settings_repository
):
    navigate, _ = navigate_stub
    gallery = _gallery(
        tk_root, seeded_maze_repository_with_saved_random, navigate, fake_settings_repository
    )

    for _ in range(3):  # 3 classics -> index 3 is the first saved-random entry ("delta")
        gallery._on_next()

    assert gallery._index == 3
    assert gallery._position_label.cget("text") == "Saved Random Maze 4 of 5"
    assert gallery._jump_entry.get() == "4"


def test_next_walks_from_the_last_classic_into_the_first_saved_random_entry(
    tk_root, seeded_maze_repository_with_saved_random, navigate_stub, fake_settings_repository
):
    navigate, _ = navigate_stub
    gallery = _gallery(
        tk_root, seeded_maze_repository_with_saved_random, navigate, fake_settings_repository
    )
    gallery._jump_entry.delete(0, "end")
    gallery._jump_entry.insert(0, "3")
    gallery._on_jump()
    assert gallery._position_label.cget("text") == "Classic Maze 3 of 5"

    gallery._on_next()

    assert gallery._position_label.cget("text") == "Saved Random Maze 4 of 5"


def test_jump_to_a_saved_random_entry_by_its_overall_number(
    tk_root, seeded_maze_repository_with_saved_random, navigate_stub, fake_settings_repository
):
    navigate, _ = navigate_stub
    gallery = _gallery(
        tk_root, seeded_maze_repository_with_saved_random, navigate, fake_settings_repository
    )
    gallery._jump_entry.delete(0, "end")
    gallery._jump_entry.insert(0, "5")

    gallery._on_jump()

    assert gallery._index == 4
    assert gallery._position_label.cget("text") == "Saved Random Maze 5 of 5"


def test_playing_a_browsed_saved_random_entry_loads_it_by_its_own_kind(
    tk_root, seeded_maze_repository_with_saved_random, navigate_stub, fake_settings_repository
):
    navigate, calls = navigate_stub
    gallery = _gallery(
        tk_root, seeded_maze_repository_with_saved_random, navigate, fake_settings_repository
    )
    gallery._jump_entry.delete(0, "end")
    gallery._jump_entry.insert(0, "4")
    gallery._on_jump()

    gallery._on_play()

    assert len(calls) == 1
    screen_id, maze = calls[0]
    assert screen_id == ScreenId.PLAYER
    assert maze == seeded_maze_repository_with_saved_random.load("delta", MazeKind.SAVED_RANDOM)


def test_only_saved_random_mazes_shows_the_populated_state_not_the_empty_state(
    tk_root, fake_maze_repository, navigate_stub, fake_settings_repository
):
    fake_maze_repository.save(saved_random_maze(width=5, height=5), "solo")
    navigate, _ = navigate_stub

    gallery = _gallery(tk_root, fake_maze_repository, navigate, fake_settings_repository)

    assert gallery._entries == [(MazeKind.SAVED_RANDOM, "solo")]
    assert gallery._position_label.cget("text") == "Saved Random Maze 1 of 1"
    assert gallery._play_button.winfo_exists()


def test_neither_classics_nor_saved_random_mazes_shows_the_empty_state(
    tk_root, fake_maze_repository, navigate_stub, fake_settings_repository
):
    navigate, _ = navigate_stub

    gallery = _gallery(tk_root, fake_maze_repository, navigate, fake_settings_repository)

    assert not hasattr(gallery, "_play_button")
    labels = [
        child.cget("text") for child in gallery.winfo_children() if isinstance(child, tk.Label)
    ]
    assert any("No classic or saved mazes were found" in text for text in labels)


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


# -- Story 2.10: gated browse/jump surfaces ---------------------------------------------


def test_next_opens_a_confirm_dialog_when_confirm_switch_maze_is_on(
    tk_root, seeded_maze_repository, navigate_stub, fake_settings_repository
):
    write_confirm_switch_maze(fake_settings_repository, True)
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, seeded_maze_repository, navigate, fake_settings_repository)

    gallery._on_next()

    dialogs = [c for c in gallery.winfo_children() if isinstance(c, ConfirmDialog)]
    assert len(dialogs) == 1
    assert gallery._confirm_dialog is dialogs[0]
    assert gallery._index == 0


def test_confirming_the_switch_dialog_moves_to_the_next_maze(
    tk_root, seeded_maze_repository, navigate_stub, fake_settings_repository
):
    write_confirm_switch_maze(fake_settings_repository, True)
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, seeded_maze_repository, navigate, fake_settings_repository)

    gallery._on_next()
    gallery._confirm_dialog._on_confirm_clicked()

    assert gallery._index == 1
    assert gallery._position_label.cget("text") == "Classic Maze 2 of 3"
    assert gallery._confirm_dialog is None


def test_cancelling_the_switch_dialog_leaves_the_index_untouched(
    tk_root, seeded_maze_repository, navigate_stub, fake_settings_repository
):
    write_confirm_switch_maze(fake_settings_repository, True)
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, seeded_maze_repository, navigate, fake_settings_repository)
    gallery._on_next()
    gallery._on_next()  # first dialog open
    gallery._confirm_dialog._on_cancel_clicked()

    assert gallery._index == 0
    assert gallery._position_label.cget("text") == "Classic Maze 1 of 3"
    assert gallery._confirm_dialog is None


def test_a_second_gated_trigger_while_a_dialog_is_open_is_a_no_op(
    tk_root, seeded_maze_repository, navigate_stub, fake_settings_repository
):
    write_confirm_switch_maze(fake_settings_repository, True)
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, seeded_maze_repository, navigate, fake_settings_repository)
    gallery._on_next()
    first = gallery._confirm_dialog

    gallery._on_next()

    dialogs = [c for c in gallery.winfo_children() if isinstance(c, ConfirmDialog)]
    assert len(dialogs) == 1
    assert gallery._confirm_dialog is first
    first.destroy()


def test_restart_is_gated_behind_confirm_switch_maze(
    tk_root, seeded_maze_repository, navigate_stub, fake_settings_repository
):
    write_confirm_switch_maze(fake_settings_repository, True)
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, seeded_maze_repository, navigate, fake_settings_repository)
    gallery._index = 2
    gallery._refresh_display()

    gallery._on_restart()

    assert gallery._index == 2
    assert gallery._confirm_dialog is not None
    gallery._confirm_dialog._on_confirm_clicked()
    assert gallery._index == 0


def test_a_valid_jump_is_gated_behind_confirm_switch_maze(
    tk_root, seeded_maze_repository, navigate_stub, fake_settings_repository
):
    write_confirm_switch_maze(fake_settings_repository, True)
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, seeded_maze_repository, navigate, fake_settings_repository)
    gallery._jump_entry.delete(0, "end")
    gallery._jump_entry.insert(0, "3")

    gallery._on_jump()

    assert gallery._index == 0
    assert gallery._confirm_dialog is not None
    gallery._confirm_dialog._on_confirm_clicked()
    assert gallery._index == 2


def test_invalid_jump_shows_an_ok_only_alert_when_confirm_invalid_input_is_on(
    tk_root, seeded_maze_repository, navigate_stub, fake_settings_repository
):
    write_confirm_invalid_input(fake_settings_repository, True)
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, seeded_maze_repository, navigate, fake_settings_repository)
    gallery._jump_entry.delete(0, "end")
    gallery._jump_entry.insert(0, "abc")

    gallery._on_jump()

    assert gallery._index == 0
    assert gallery._jump_entry.get() == "1"
    dialog = gallery._confirm_dialog
    assert dialog is not None
    assert not hasattr(dialog, "_cancel_button")
    dialog._on_confirm_clicked()
    assert gallery._confirm_dialog is None


def test_invalid_jump_skips_the_alert_when_confirm_invalid_input_is_off(
    tk_root, seeded_maze_repository, navigate_stub, fake_settings_repository
):
    write_confirm_invalid_input(fake_settings_repository, False)
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, seeded_maze_repository, navigate, fake_settings_repository)
    gallery._jump_entry.delete(0, "end")
    gallery._jump_entry.insert(0, "abc")

    gallery._on_jump()

    assert gallery._index == 0
    assert gallery._jump_entry.get() == "1"
    assert gallery._confirm_dialog is None
    assert read_confirm_invalid_input(fake_settings_repository) is False
