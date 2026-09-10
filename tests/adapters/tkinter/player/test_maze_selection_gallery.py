import tkinter as tk

from labyrinthes.adapters.tkinter.common.tokens import Theme
from labyrinthes.adapters.tkinter.player.generate_random_dialog import GenerateRandomDialog
from labyrinthes.adapters.tkinter.player.maze_card import _MIN_MARKER_RADIUS, MazeCard
from labyrinthes.adapters.tkinter.player.maze_selection_gallery import MazeSelectionGallery
from labyrinthes.app.router import ScreenId
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.position import Position
from tests.adapters.tkinter.player.conftest import classic_maze, creation_maze, saved_random_maze


def _thumbnail_canvas(card):
    for child in card.winfo_children():
        if isinstance(child, tk.Canvas):
            return child
    raise AssertionError("MazeCard has no thumbnail Canvas child")


def _gallery(tk_root, repository, navigate, settings_repository):
    return MazeSelectionGallery(
        tk_root,
        theme=Theme.LIGHT,
        maze_repository=repository,
        settings_repository=settings_repository,
        navigate=navigate,
    )


def _cards(gallery, find_all):
    return find_all(gallery, MazeCard)


def _labels(gallery):
    labels = []
    for widget in gallery.winfo_children():
        labels.extend(_collect_labels(widget))
    return labels


def _collect_labels(widget):
    found = []
    if isinstance(widget, tk.Label):
        found.append(widget.cget("text"))
    for child in widget.winfo_children():
        found.extend(_collect_labels(child))
    return found


# -- three sections, populated ------------------------------------------------------


def test_all_three_sections_render_their_own_cards_when_populated(
    tk_root, fake_maze_repository, navigate_stub, fake_settings_repository, find_all
):
    fake_maze_repository.save(classic_maze(width=4, height=3), "alpha")
    fake_maze_repository.save(creation_maze(width=5, height=5), "bravo")
    fake_maze_repository.save(saved_random_maze(width=6, height=4), "charlie")
    navigate, _ = navigate_stub

    gallery = _gallery(tk_root, fake_maze_repository, navigate, fake_settings_repository)

    cards = _cards(gallery, find_all)
    names = {card._maze_name for card in cards}
    assert names == {"alpha", "bravo", "charlie"}


def test_section_headings_are_labeled_classic_creations_random(
    tk_root, fake_maze_repository, navigate_stub, fake_settings_repository
):
    fake_maze_repository.save(classic_maze(width=4, height=3), "alpha")
    fake_maze_repository.save(creation_maze(width=5, height=5), "bravo")
    fake_maze_repository.save(saved_random_maze(width=6, height=4), "charlie")
    navigate, _ = navigate_stub

    gallery = _gallery(tk_root, fake_maze_repository, navigate, fake_settings_repository)

    labels = _labels(gallery)
    assert "CLASSIC" in labels
    assert "CREATIONS" in labels
    assert "RANDOM" in labels


# -- thumbnail entry/exit marker minimum radius ---------------------------------------


def test_entry_and_exit_markers_keep_a_minimum_radius_at_the_smallest_thumbnail_cell_size(
    tk_root, fake_maze_repository, navigate_stub, fake_settings_repository, find_all
):
    # A maze at/near the FR-4 max bounds (e.g. 50x35, not a contrived edge
    # case) clamps `_thumbnail_cell_size` down to its 2px floor -- at that
    # scale, `marker_scale` alone would shrink the entry/exit markers to a
    # ~0.6px radius, too small to tell the entry square from the exit
    # diamond apart (NFR6). `MazeCard` passes `_MIN_MARKER_RADIUS` to guard
    # against that.
    fake_maze_repository.save(classic_maze(width=50, height=35), "big")
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, fake_maze_repository, navigate, fake_settings_repository)
    card = _cards(gallery, find_all)[0]
    canvas = _thumbnail_canvas(card)

    entry_bbox = canvas.bbox("entry-marker")
    exit_bbox = canvas.bbox("exit-marker")

    assert entry_bbox is not None
    assert exit_bbox is not None
    # `bbox` returns (x0, y0, x1, y1); a floored radius of
    # `_MIN_MARKER_RADIUS` shows up as a span of at least
    # `2 * _MIN_MARKER_RADIUS` px. Confirmed (via a direct, unfloored call
    # to `draw_entry_marker` at this same `cell_size=2`) that an unfloored
    # radius produces a span of only 2px here -- below this threshold --
    # so this genuinely discriminates the fix rather than passing
    # regardless of whether `min_radius` was wired through.
    minimum_span = 2 * _MIN_MARKER_RADIUS
    assert entry_bbox[2] - entry_bbox[0] >= minimum_span
    assert entry_bbox[3] - entry_bbox[1] >= minimum_span
    assert exit_bbox[2] - exit_bbox[0] >= minimum_span
    assert exit_bbox[3] - exit_bbox[1] >= minimum_span


# -- per-section empty state --------------------------------------------------------


def test_one_empty_section_shows_only_its_own_empty_message(
    tk_root, fake_maze_repository, navigate_stub, fake_settings_repository, find_all
):
    # Classic and Random populated; Creations left empty.
    fake_maze_repository.save(classic_maze(width=4, height=3), "alpha")
    fake_maze_repository.save(saved_random_maze(width=6, height=4), "charlie")
    navigate, _ = navigate_stub

    gallery = _gallery(tk_root, fake_maze_repository, navigate, fake_settings_repository)

    labels = _labels(gallery)
    assert any("No Creations saved yet" in text for text in labels)
    cards = _cards(gallery, find_all)
    names = {card._maze_name for card in cards}
    assert names == {"alpha", "charlie"}


def test_every_section_empty_shows_three_empty_messages_and_generate_random_still_renders(
    tk_root, fake_maze_repository, navigate_stub, fake_settings_repository, find_all
):
    navigate, _ = navigate_stub

    gallery = _gallery(tk_root, fake_maze_repository, navigate, fake_settings_repository)

    labels = _labels(gallery)
    assert any("No classic mazes" in text for text in labels)
    assert any("No Creations saved yet" in text for text in labels)
    assert any("No saved random mazes" in text for text in labels)
    assert _cards(gallery, find_all) == []
    assert gallery._generate_random_button.winfo_exists()


# -- card activation -----------------------------------------------------------------


def test_clicking_a_card_navigates_to_player_with_that_maze(
    tk_root, fake_maze_repository, navigate_stub, fake_settings_repository, find_all
):
    fake_maze_repository.save(creation_maze(width=5, height=5), "bravo")
    navigate, calls = navigate_stub
    gallery = _gallery(tk_root, fake_maze_repository, navigate, fake_settings_repository)
    card = _cards(gallery, find_all)[0]

    card._on_activated()

    assert len(calls) == 1
    screen_id, maze = calls[0]
    assert screen_id == ScreenId.PLAYER
    assert maze == fake_maze_repository.load("bravo", MazeKind.CREATION)


def test_keyboard_activation_via_return_or_space_navigates_the_same_as_a_click(
    tk_root, fake_maze_repository, navigate_stub, fake_settings_repository, find_all
):
    # `MazeCard` binds `<Return>`/`<space>` to the same handler `<Button-1>`
    # does -- invoking it directly is this codebase's established
    # convention for exercising keyboard activation under a withdrawn
    # `tk_root` (real X11 KeyPress synthesis is unreliable there).
    fake_maze_repository.save(classic_maze(width=4, height=3), "alpha")
    navigate, calls = navigate_stub
    gallery = _gallery(tk_root, fake_maze_repository, navigate, fake_settings_repository)
    card = _cards(gallery, find_all)[0]
    assert card.bind("<Return>") != ""
    assert card.bind("<space>") != ""

    card._on_activated()

    assert len(calls) == 1
    assert calls[0][0] == ScreenId.PLAYER


def test_every_card_is_keyboard_focusable(
    tk_root, fake_maze_repository, navigate_stub, fake_settings_repository, find_all
):
    fake_maze_repository.save(classic_maze(width=4, height=3), "alpha")
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, fake_maze_repository, navigate, fake_settings_repository)
    card = _cards(gallery, find_all)[0]

    assert card.cget("takefocus")


def test_a_card_carries_its_own_mouse_wheel_bindings(
    tk_root, fake_maze_repository, navigate_stub, fake_settings_repository, find_all
):
    # Tk delivers a wheel event to whatever's directly under the pointer --
    # without `ScrollableFrame.bind_wheel_recursive()` reaching each card
    # (and its own thumbnail/name/meta children), the wheel would only
    # scroll while the pointer sits over the canvas's bare margin. Asserts
    # the binding is present rather than synthesizing a real wheel event,
    # mirroring this suite's established `bind(...) != ""` convention under
    # a withdrawn `tk_root`.
    fake_maze_repository.save(classic_maze(width=4, height=3), "alpha")
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, fake_maze_repository, navigate, fake_settings_repository)
    card = _cards(gallery, find_all)[0]

    for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
        assert card.bind(sequence) != ""
        assert _thumbnail_canvas(card).bind(sequence) != ""


def test_a_cards_wheel_binding_actually_scrolls_the_gallerys_canvas(
    tk_root, fake_maze_repository, navigate_stub, fake_settings_repository, find_all
):
    # `bind_wheel_recursive` binds the exact same `ScrollableFrame._on_mouse_wheel`
    # bound method onto the card as onto the canvas margin itself (not a
    # per-widget wrapper) -- so invoking it directly here is invoking
    # precisely what fires when the wheel event lands on the card, the same
    # "call the bound handler directly" convention this suite already uses
    # for click/keyboard activation under a withdrawn `tk_root`.
    fake_maze_repository.save(classic_maze(width=4, height=3), "alpha")
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, fake_maze_repository, navigate, fake_settings_repository)
    card = _cards(gallery, find_all)[0]
    scrollable = gallery._scrollable
    assert card.bind("<Button-5>") != ""  # the binding this handler models
    scrolled = []
    scrollable._canvas.yview_scroll = lambda number, what: scrolled.append((number, what))

    class _FakeWheelEvent:
        num = 5  # X11 "scroll down" button

    scrollable._on_mouse_wheel(_FakeWheelEvent())

    assert scrolled == [(1, "units")]


# -- scroll-into-view on focus --------------------------------------------------------


def test_focusing_a_card_scrolls_it_into_view(
    tk_root, fake_maze_repository, navigate_stub, fake_settings_repository, find_all
):
    fake_maze_repository.save(classic_maze(width=4, height=3), "alpha")
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, fake_maze_repository, navigate, fake_settings_repository)
    card = _cards(gallery, find_all)[0]
    scrolled = []
    gallery._scrollable.scroll_into_view = scrolled.append

    gallery._on_card_focus(card)

    assert scrolled == [card]


# -- generate-random dialog (unchanged wiring, ported from the pager) ----------------


def test_generate_random_opens_a_dialog_parented_to_the_gallery(
    tk_root, fake_maze_repository, navigate_stub, fake_settings_repository
):
    navigate, calls = navigate_stub
    gallery = _gallery(tk_root, fake_maze_repository, navigate, fake_settings_repository)

    gallery._on_generate_random()

    dialogs = [c for c in gallery.winfo_children() if isinstance(c, GenerateRandomDialog)]
    assert len(dialogs) == 1
    assert dialogs[0].master is gallery
    assert calls == []


def test_generate_random_dialog_uses_the_default_bounds_when_none_are_stored(
    tk_root, fake_maze_repository, navigate_stub, fake_settings_repository
):
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, fake_maze_repository, navigate, fake_settings_repository)

    gallery._on_generate_random()

    dialog = [c for c in gallery.winfo_children() if isinstance(c, GenerateRandomDialog)][0]
    assert dialog._entries["columns"].get() == "3"
    assert dialog._entries["rows"].get() == "3"


def test_confirming_generation_navigates_to_player_with_a_generated_maze(
    tk_root, fake_maze_repository, navigate_stub, fake_settings_repository
):
    navigate, calls = navigate_stub
    gallery = _gallery(tk_root, fake_maze_repository, navigate, fake_settings_repository)

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
    tk_root, fake_maze_repository, navigate_stub, fake_settings_repository
):
    # End-to-end through the real dialog, not just `_on_generation_confirmed`
    # called directly -- proves the callback wiring itself is correct.
    navigate, calls = navigate_stub
    gallery = _gallery(tk_root, fake_maze_repository, navigate, fake_settings_repository)
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


def test_generate_random_button_is_never_a_fourth_section(
    tk_root, fake_maze_repository, navigate_stub, fake_settings_repository
):
    # Packed directly on the gallery frame, outside the scrollable section
    # grid -- never a descendant of `.content`, so it can never render as a
    # fourth section card among Classic/Creations/Random.
    navigate, _ = navigate_stub
    gallery = _gallery(tk_root, fake_maze_repository, navigate, fake_settings_repository)

    assert gallery._generate_random_button.master is gallery
    assert gallery._generate_random_button.master is not gallery._scrollable.content
