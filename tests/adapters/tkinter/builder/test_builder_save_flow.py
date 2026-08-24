"""Builder save flow: Sketch vs. Maze, Test in Player, and
_SaveNameDialog naming/arming (Stories 3.6/3.8)."""

import tkinter as tk

from labyrinthes.adapters.tkinter.builder.edit_area import _BuilderEditArea
from labyrinthes.adapters.tkinter.builder.maze_canvas import _BuilderMazeCanvas
from labyrinthes.adapters.tkinter.builder.save_dialog import _SaveNameDialog
from labyrinthes.adapters.tkinter.builder.screen import mount
from labyrinthes.adapters.tkinter.common import (
    BuilderTestLaunch,
    ConfirmDialog,
    HudChip,
    PillButton,
    Theme,
)
from labyrinthes.adapters.tkinter.common.keybindings import keybinding
from labyrinthes.adapters.tkinter.common.navigation import ScreenId
from labyrinthes.application.builder_session import (
    apply_set_exit,
    apply_wall_toggle,
)
from labyrinthes.domain.level_visibility import Wall
from labyrinthes.domain.maze import MazeKind
from labyrinthes.domain.position import Position
from tests.adapters.tkinter.builder._helpers import (
    _classic_maze,
    _drag_zone,
    _sketch_maze,
)

# -- save flow (Story 3.6) --------------------------------------------------


def _place_exit(
    edit_area: _BuilderEditArea, canvas: _BuilderMazeCanvas, position: Position
) -> None:
    """Place the session exit marker at `position` (a border cell), the real
    way (`_activate_set_exit` + a same-cell drag), matching every other
    marker-placement test in this file."""
    edit_area._activate_set_exit()
    _drag_zone(canvas, position, position)


def test_save_pill_button_renders_in_the_hud_row_with_the_canonical_shortcut(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        _sketch_maze(4, 3),
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    save_button = next(b for b in find_all(frame, PillButton) if b._label.cget("text") == "Save")
    assert save_button._kbd is not None


def test_test_in_player_pill_renders_non_primary_with_the_canonical_shortcut(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        _sketch_maze(4, 3),
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    test_pill = next(
        b for b in find_all(frame, PillButton) if b._label.cget("text") == "Test in Player"
    )
    assert test_pill._primary is False  # exactly one primary pill per screen
    assert test_pill._kbd is not None  # canonical shortcut kbd-tag

    save_pill = next(b for b in find_all(frame, PillButton) if b._label.cget("text") == "Save")
    assert save_pill._primary is True


def test_test_in_player_pill_click_navigates_to_player_with_the_edited_session_maze(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, calls = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        _sketch_maze(4, 3),
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )
    edit_area = find_all(frame, _BuilderEditArea)[0]
    test_pill = next(
        b for b in find_all(frame, PillButton) if b._label.cget("text") == "Test in Player"
    )

    # Break an interior wall first so the "exact in-progress object"
    # assertion isn't trivially satisfied by an unedited session -- the
    # hand-off must reflect the live edited state, not the mounted maze.
    broken = Wall(row=1, col=1, side="top")
    pre_edit_grid = edit_area._session.maze.grid
    assert pre_edit_grid.cell_at(Position(row=1, col=1)).has_top_wall
    edit_area._session = apply_wall_toggle(edit_area._session, broken)
    # The Test in Player gate requires the session's exit marker to be set
    # (amendment) -- place it before clicking.
    exit_marker = Position(row=2, col=3)
    edit_area._session = apply_set_exit(edit_area._session, exit_marker)

    test_pill._on_click()

    assert len(calls) == 1
    assert calls[0][0] is ScreenId.PLAYER
    launch = calls[0][1]
    assert isinstance(launch, BuilderTestLaunch)
    assert launch.maze is edit_area._session.maze  # exact in-progress object
    assert launch.maze.grid is not pre_edit_grid  # the wall edit is handed off
    assert not launch.maze.grid.cell_at(Position(row=1, col=1)).has_top_wall
    assert launch.entry == edit_area._session.entry  # markers round-trip
    assert launch.exit == exit_marker


def test_test_in_player_pill_click_is_blocked_by_a_popup_when_the_exit_is_unset(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    # Amendment: Test in Player is refused while the session's exit marker
    # is unset (`start_builder_session` always seeds the entry, so only the
    # exit can be missing). An alert-mode ConfirmDialog explains -- and no
    # navigation happens.
    navigate, calls = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        _sketch_maze(4, 3),
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )
    edit_area = find_all(frame, _BuilderEditArea)[0]
    assert edit_area._session.exit is None
    test_pill = next(
        b for b in find_all(frame, PillButton) if b._label.cget("text") == "Test in Player"
    )

    test_pill._on_click()

    assert calls == []
    dialogs = find_all(frame, ConfirmDialog)
    assert len(dialogs) == 1
    labels = [c.cget("text") for c in find_all(dialogs[0], tk.Label)]
    assert any("exit" in text.lower() for text in labels)


def test_test_in_player_is_available_for_a_classic_maze_once_the_exit_is_set(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    # FR-8's "available from any active Builder session" -- not gated to
    # maze kind (unlike FR-19's mirror), but the exit-marker gate applies
    # to every kind alike.
    navigate, calls = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    classic = _classic_maze(4, 3)
    frame = mount(
        tk_root,
        classic,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )
    edit_area = find_all(frame, _BuilderEditArea)[0]
    exit_marker = Position(row=2, col=3)
    edit_area._session = apply_set_exit(edit_area._session, exit_marker)
    test_pill = next(
        b for b in find_all(frame, PillButton) if b._label.cget("text") == "Test in Player"
    )

    test_pill._on_click()

    assert len(calls) == 1
    assert calls[0][0] is ScreenId.PLAYER
    launch = calls[0][1]
    assert isinstance(launch, BuilderTestLaunch)
    assert launch.maze is edit_area._session.maze
    assert launch.exit == exit_marker


def test_test_in_player_shortcut_is_registered_for_an_active_edit_session(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    mount(
        tk_root,
        _sketch_maze(4, 3),
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    assert tk_root.bind_all(keybinding("test_in_player").event) != ""


def test_test_in_player_shortcut_is_not_registered_in_the_new_maze_entry_state(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    # I/O matrix "Builder in the New-Maze entry state": no active session,
    # so 't' is inert there.
    assert tk_root.bind_all(keybinding("test_in_player").event) == ""


def test_test_in_player_shortcut_fires_the_same_handler_as_the_pill(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, calls = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        _sketch_maze(4, 3),
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )
    edit_area = find_all(frame, _BuilderEditArea)[0]
    # The Test in Player gate requires the session's exit marker to be set
    # (amendment) -- place it before firing the handler.
    edit_area._session = apply_set_exit(edit_area._session, Position(row=2, col=3))

    # Verifies the handler method the `test_in_player` binding is wired to
    # (the registration itself is asserted separately in
    # `test_test_in_player_shortcut_is_registered_for_an_active_edit_session`).
    edit_area._test_in_player()

    assert len(calls) == 1
    assert calls[0][0] is ScreenId.PLAYER
    launch = calls[0][1]
    assert isinstance(launch, BuilderTestLaunch)
    assert launch.maze is edit_area._session.maze  # exact in-progress object


def test_status_chip_shows_draft_for_a_sketch_maze(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        _sketch_maze(4, 3),
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    chips = {c._caption.cget("text"): c for c in find_all(frame, HudChip)}
    assert chips["STATUS"]._value_label.cget("text") == "Draft"


def test_status_chip_is_absent_for_a_classic_maze(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        _classic_maze(4, 3),
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    chips = {c._caption.cget("text"): c for c in find_all(frame, HudChip)}
    assert "STATUS" not in chips


def test_saving_with_exit_not_set_offers_a_sketch_save_via_confirm_dialog(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, calls = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        _sketch_maze(4, 3),
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )
    edit_area = find_all(frame, _BuilderEditArea)[0]
    assert edit_area._session.exit is None  # fresh session: never pre-set

    edit_area.save_maze()

    dialogs = find_all(frame, ConfirmDialog)
    assert len(dialogs) == 1
    label_texts = [label.cget("text") for label in find_all(dialogs[0], tk.Label)]
    assert any("Sketch" in text for text in label_texts)
    # No save/navigation happened yet -- only the exit-not-set explanation.
    assert calls == []
    assert fake_maze_repository.list_names(MazeKind.SKETCH) == []


def test_confirming_the_exit_not_set_dialog_saves_as_a_sketch_and_navigates_back(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, calls = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        _sketch_maze(4, 3),
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )
    edit_area = find_all(frame, _BuilderEditArea)[0]

    edit_area.save_maze()
    find_all(frame, ConfirmDialog)[0]._on_confirm_clicked()

    name_dialogs = find_all(frame, _SaveNameDialog)
    assert len(name_dialogs) == 1
    dialog = name_dialogs[0]
    assert dialog._name_entry.get() == "4x3"  # suggested from grid dimensions

    dialog._on_save_clicked()

    assert fake_maze_repository.list_names(MazeKind.SKETCH) == ["4x3"]
    saved = fake_maze_repository.load("4x3", MazeKind.SKETCH)
    assert saved.kind is MazeKind.SKETCH
    assert saved.id is None  # SKETCH is never id-eligible (AD-3)
    assert len(calls) == 1
    screen_id, navigated_maze = calls[0]
    assert screen_id is ScreenId.BUILDER
    assert navigated_maze == saved


def test_saving_with_exit_set_promotes_sketch_to_classic_and_mints_a_maze_id(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, calls = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        _sketch_maze(4, 3),
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )
    edit_area = find_all(frame, _BuilderEditArea)[0]
    canvas = find_all(frame, tk.Canvas)[0]
    _place_exit(edit_area, canvas, Position(2, 3))

    edit_area.save_maze()

    # Exit is set: no exit-not-set ConfirmDialog -- straight to naming.
    assert find_all(frame, ConfirmDialog) == []
    dialog = find_all(frame, _SaveNameDialog)[0]
    dialog._on_save_clicked()

    assert fake_maze_repository.list_names(MazeKind.CLASSIC) == ["4x3"]
    saved = fake_maze_repository.load("4x3", MazeKind.CLASSIC)
    assert saved.kind is MazeKind.CLASSIC
    assert saved.id is not None  # CLASSIC is id-eligible: minted on first save (AD-3/AD-6)
    assert len(calls) == 1
    assert calls[0] == (ScreenId.BUILDER, saved)


def test_saving_a_maze_that_already_has_an_id_keeps_it_unchanged(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    # A future Edit-in-Builder resave (Story 3.9): the maze is already
    # CLASSIC/SAVED_RANDOM with an id -- re-saving must carry it forward
    # unchanged, never re-mint (AD-3/AD-6, `MazeRepository.save()`'s own
    # contract).
    navigate, calls = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    existing = fake_maze_repository.save(_classic_maze(4, 3), "existing")
    assert existing.id is not None

    frame = mount(
        tk_root,
        existing,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )
    edit_area = find_all(frame, _BuilderEditArea)[0]
    canvas = find_all(frame, tk.Canvas)[0]
    _place_exit(edit_area, canvas, Position(2, 3))

    edit_area.save_maze()
    dialog = find_all(frame, _SaveNameDialog)[0]
    dialog._name_entry.delete(0, "end")
    dialog._name_entry.insert(0, "existing")
    # Re-saving under its own current name is itself a collision (the name
    # is already in `existing_names`) -- the arm/confirm overwrite pattern
    # applies here too, same as any other duplicate.
    dialog._on_save_clicked()
    assert dialog._save_button._label.cget("text") == "Overwrite"
    dialog._on_save_clicked()

    resaved = fake_maze_repository.load("existing", MazeKind.CLASSIC)
    assert resaved.id == existing.id
    assert calls[-1] == (ScreenId.BUILDER, resaved)


def test_duplicate_name_arms_the_save_button_and_requires_a_second_click_to_overwrite(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, calls = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    fake_maze_repository.save(_classic_maze(4, 3), "4x3")  # pre-existing collision

    frame = mount(
        tk_root,
        _sketch_maze(4, 3),
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )
    edit_area = find_all(frame, _BuilderEditArea)[0]
    canvas = find_all(frame, tk.Canvas)[0]
    _place_exit(edit_area, canvas, Position(2, 3))
    edit_area.save_maze()
    dialog = find_all(frame, _SaveNameDialog)[0]

    dialog._on_save_clicked()  # first click on the colliding "4x3" name

    assert dialog.winfo_exists()  # not yet closed -- armed instead
    assert dialog._save_button._label.cget("text") == "Overwrite"
    assert calls == []

    dialog._on_save_clicked()  # second click, name unchanged: confirms

    assert not dialog.winfo_exists()
    assert len(calls) == 1
    saved = fake_maze_repository.load("4x3", MazeKind.CLASSIC)
    assert calls[0] == (ScreenId.BUILDER, saved)


def test_editing_the_name_after_arming_resets_the_save_button(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, calls = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    fake_maze_repository.save(_classic_maze(4, 3), "4x3")

    frame = mount(
        tk_root,
        _sketch_maze(4, 3),
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )
    edit_area = find_all(frame, _BuilderEditArea)[0]
    canvas = find_all(frame, tk.Canvas)[0]
    _place_exit(edit_area, canvas, Position(2, 3))
    edit_area.save_maze()
    dialog = find_all(frame, _SaveNameDialog)[0]
    dialog._on_save_clicked()
    assert dialog._save_button._label.cget("text") == "Overwrite"

    dialog._name_entry.delete(0, "end")
    dialog._name_entry.insert(0, "a-different-name")
    dialog._on_name_changed()

    assert dialog._save_button._label.cget("text") == "Save"
    assert calls == []


def test_saving_with_an_empty_name_shows_an_inline_error_and_does_not_save(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, calls = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        _sketch_maze(4, 3),
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )
    edit_area = find_all(frame, _BuilderEditArea)[0]
    edit_area.save_maze()
    find_all(frame, ConfirmDialog)[0]._on_confirm_clicked()
    dialog = find_all(frame, _SaveNameDialog)[0]
    dialog._name_entry.delete(0, "end")

    dialog._on_save_clicked()

    assert dialog.winfo_exists()
    assert dialog._message_label.cget("text") == "Name is required."
    assert calls == []
    assert fake_maze_repository.list_names(MazeKind.SKETCH) == []
