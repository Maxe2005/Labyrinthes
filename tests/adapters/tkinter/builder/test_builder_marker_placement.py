"""Builder entry/exit marking: Set Entry/Set Exit tools, the ghost preview,
and redefinition confirmation (Story 3.4)."""

from labyrinthes.adapters.tkinter.builder.edit_area import _BuilderEditArea
from labyrinthes.adapters.tkinter.builder.maze_canvas import _BuilderMazeCanvas
from labyrinthes.adapters.tkinter.builder.screen import mount
from labyrinthes.adapters.tkinter.common import (
    ConfirmDialog,
    Theme,
    ToolButton,
)
from labyrinthes.adapters.tkinter.common.tokens import colors_for
from labyrinthes.application.builder_session import (
    BuilderTool,
)
from labyrinthes.application.confirmation_settings import (
    write_confirm_redefine_marker,
)
from labyrinthes.domain.movement import Direction
from labyrinthes.domain.position import Position
from tests.adapters.tkinter.builder._helpers import (
    _drag_zone,
    _open_top_row_maze,
    _sketch_maze,
)

# -- entry/exit marking (Story 3.4) ----------------------------------------


def _tool_button_by_label(find_all, frame, label: str) -> ToolButton:
    return next(b for b in find_all(frame, ToolButton) if b._label.cget("text") == label)


def test_set_entry_and_set_exit_tool_buttons_are_rendered_in_the_sidebar(
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

    assert _tool_button_by_label(find_all, frame, "Set Entry").active is False
    assert _tool_button_by_label(find_all, frame, "Set Exit").active is False


def test_keybinding_e_activates_set_entry_and_x_set_exit(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    # `set_entry`/`set_exit`'s bound handlers (BUILDER-scoped 'e'/'x') call
    # exactly these methods -- see `_BuilderEditArea.__init__`'s
    # `bind_shortcut` (mirrors the 'd'/'r' tests).
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

    edit_area = find_all(frame, _BuilderEditArea)[0]
    edit_area._activate_set_entry()

    assert _tool_button_by_label(find_all, frame, "Set Entry").active is True
    assert edit_area._session.tool is BuilderTool.SET_ENTRY

    edit_area._activate_set_exit()

    assert _tool_button_by_label(find_all, frame, "Set Exit").active is True
    assert edit_area._session.tool is BuilderTool.SET_EXIT


def test_clicking_a_cell_with_set_entry_places_the_entry_marker(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    # The entry is seeded at (0,0), so this is a *redefinition* -- disable
    # the Story 3.4 confirm gate so the placement applies directly (the
    # prompt itself is covered by the dedicated redefinition tests below).
    write_confirm_redefine_marker(fake_settings_repository, False)
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
    edit_area = find_all(frame, _BuilderEditArea)[0]
    canvas = find_all(frame, _BuilderMazeCanvas)[0]
    edit_area._activate_set_entry()

    _drag_zone(canvas, Position(1, 1), Position(1, 1))

    assert edit_area._session.entry == Position(1, 1)
    assert edit_area._session.maze.entry == Position(1, 1)
    markers = canvas.find_withtag("marker")
    assert len(markers) == 1
    cx, cy = canvas._cell_center(Position(1, 1))
    x0, y0, x1, y1 = canvas.bbox(markers[0])
    assert (x0 + x1) // 2 == cx
    assert (y0 + y1) // 2 == cy
    assert canvas.itemcget(markers[0], "fill") == colors_for(Theme.LIGHT).entry


def test_clicking_a_border_cell_with_set_exit_places_the_exit_marker(
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
    edit_area = find_all(frame, _BuilderEditArea)[0]
    canvas = find_all(frame, _BuilderMazeCanvas)[0]
    edit_area._activate_set_exit()

    _drag_zone(canvas, Position(2, 0), Position(2, 0))

    assert edit_area._session.exit == Position(2, 0)
    assert edit_area._session.maze.exit == Position(2, 0)
    # Entry (seeded) + exit = two distinct marker items.
    assert len(canvas.find_withtag("marker")) == 2


def test_clicking_an_interior_cell_with_set_exit_places_the_exit_marker(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    # Exit can now be placed on any cell except the entry (Story 4.4).
    write_confirm_redefine_marker(fake_settings_repository, False)
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
    edit_area = find_all(frame, _BuilderEditArea)[0]
    canvas = find_all(frame, _BuilderMazeCanvas)[0]
    edit_area._activate_set_exit()

    _drag_zone(canvas, Position(1, 1), Position(1, 1))

    assert edit_area._session.exit == Position(1, 1)
    assert edit_area._session.maze.exit == Position(1, 1)
    # Entry (seeded) + exit = two distinct marker items.
    assert len(canvas.find_withtag("marker")) == 2


def test_set_exit_ghost_preview_follows_the_cursor_along_the_border(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    # The cursor starts on the seeded entry (0,0), whose cell the ghost
    # never covers (the entry marker renders there) -- so the ghost appears
    # only once the cursor reaches an unmarked border cell. The movement
    # goes through the real `_on_move` path (walls pre-opened by
    # `_open_top_row_maze`) so the tracking contract is pinned end-to-end.
    # Ghost is now a filled diamond (1 item) per Story 4.4.
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        _open_top_row_maze(),
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )
    edit_area = find_all(frame, _BuilderEditArea)[0]
    canvas = find_all(frame, _BuilderMazeCanvas)[0]
    edit_area._activate_set_exit()

    assert canvas.find_withtag("ghost-marker") == ()  # entry cell: no ghost

    edit_area._on_move(Direction.RIGHT)  # cursor (0,1), border, unmarked

    ghost = canvas.find_withtag("ghost-marker")
    assert len(ghost) == 1  # filled diamond
    cx, cy = canvas._cell_center(Position(0, 1))
    x0, y0, x1, y1 = canvas.bbox(ghost[0])
    assert (x0 + x1) // 2 == cx
    assert (y0 + y1) // 2 == cy

    edit_area._on_move(Direction.RIGHT)  # cursor (0,2), border, unmarked

    cx, cy = canvas._cell_center(Position(0, 2))
    x0, y0, x1, y1 = canvas.bbox(canvas.find_withtag("ghost-marker")[0])
    assert (x0 + x1) // 2 == cx
    assert (y0 + y1) // 2 == cy


def test_set_exit_ghost_preview_follows_the_cursor_on_interior_cells(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    # Ghost now shows on interior cells too (except the entry cell) per Story 4.4.
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        _open_top_row_maze(),
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )
    edit_area = find_all(frame, _BuilderEditArea)[0]
    canvas = find_all(frame, _BuilderMazeCanvas)[0]
    edit_area._activate_set_exit()
    edit_area._on_move(Direction.RIGHT)  # cursor (0,1): border, ghost shows

    assert len(canvas.find_withtag("ghost-marker")) == 1  # filled diamond

    edit_area._on_move(Direction.DOWN)  # cursor (1,1): interior, ghost still shows

    ghost = canvas.find_withtag("ghost-marker")
    assert len(ghost) == 1  # filled diamond on interior cell
    cx, cy = canvas._cell_center(Position(1, 1))
    x0, y0, x1, y1 = canvas.bbox(ghost[0])
    assert (x0 + x1) // 2 == cx
    assert (y0 + y1) // 2 == cy


def test_set_exit_ghost_is_never_drawn_over_an_existing_marker(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    # The ghost never covers a marker cell: neither the seeded entry at the
    # cursor's start cell nor the exit once placed at the cursor's cell --
    # the I/O matrix's "filled diamond marker replaces the ghost".
    # Ghost is now a filled diamond (1 item) per Story 4.4.
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        _open_top_row_maze(),
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )
    edit_area = find_all(frame, _BuilderEditArea)[0]
    canvas = find_all(frame, _BuilderMazeCanvas)[0]
    edit_area._activate_set_exit()
    edit_area._on_move(Direction.RIGHT)  # cursor (0,1), border, unmarked

    assert len(canvas.find_withtag("ghost-marker")) == 1  # filled diamond

    _drag_zone(canvas, Position(0, 1), Position(0, 1))  # place exit at (0,1)

    assert canvas.find_withtag("ghost-marker") == ()  # cursor sits on the exit

    edit_area._on_move(Direction.RIGHT)  # cursor (0,2): ghost reappears

    assert len(canvas.find_withtag("ghost-marker")) == 1  # filled diamond


def test_ghost_is_never_rendered_for_non_marker_tools(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    # Non-marker tools (Break, Pass-through, zone tools) never show ghosts.
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
    edit_area = find_all(frame, _BuilderEditArea)[0]
    canvas = find_all(frame, _BuilderMazeCanvas)[0]

    edit_area._activate_break()
    assert canvas.find_withtag("ghost-marker") == ()

    edit_area._activate_pass_through()
    assert canvas.find_withtag("ghost-marker") == ()

    edit_area._activate_destroy_zone()
    assert canvas.find_withtag("ghost-marker") == ()

    edit_area._activate_restore_zone()
    assert canvas.find_withtag("ghost-marker") == ()


def test_redefining_the_entry_at_a_different_cell_requires_confirmation(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    # The `confirm_redefine_marker` setting defaults to `True` (Story 3.4).
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
    edit_area = find_all(frame, _BuilderEditArea)[0]
    canvas = find_all(frame, _BuilderMazeCanvas)[0]
    edit_area._activate_set_entry()

    _drag_zone(canvas, Position(1, 1), Position(1, 1))

    dialogs = find_all(frame, ConfirmDialog)
    assert len(dialogs) == 1
    assert edit_area._session.entry == Position(0, 0)  # not moved yet

    dialogs[0]._on_confirm_clicked()

    assert edit_area._session.entry == Position(1, 1)
    assert find_all(frame, ConfirmDialog) == []


def test_cancelling_the_redefinition_dialog_leaves_the_marker_in_place(
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
    edit_area = find_all(frame, _BuilderEditArea)[0]
    canvas = find_all(frame, _BuilderMazeCanvas)[0]
    edit_area._activate_set_entry()

    _drag_zone(canvas, Position(1, 1), Position(1, 1))
    dialogs = find_all(frame, ConfirmDialog)
    assert len(dialogs) == 1

    dialogs[0]._on_cancel_clicked()

    assert edit_area._session.entry == Position(0, 0)
    assert find_all(frame, ConfirmDialog) == []


def test_clicking_the_markers_own_cell_is_a_no_op_without_a_prompt(
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
    edit_area = find_all(frame, _BuilderEditArea)[0]
    canvas = find_all(frame, _BuilderMazeCanvas)[0]
    edit_area._activate_set_entry()

    _drag_zone(canvas, Position(0, 0), Position(0, 0))  # entry already here

    assert find_all(frame, ConfirmDialog) == []
    assert edit_area._session.entry == Position(0, 0)


def test_redefine_confirmation_can_be_disabled_via_settings(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    write_confirm_redefine_marker(fake_settings_repository, False)
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
    edit_area = find_all(frame, _BuilderEditArea)[0]
    canvas = find_all(frame, _BuilderMazeCanvas)[0]
    edit_area._activate_set_entry()

    _drag_zone(canvas, Position(1, 1), Position(1, 1))

    assert find_all(frame, ConfirmDialog) == []
    assert edit_area._session.entry == Position(1, 1)


def test_first_exit_placement_never_prompts(
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
    edit_area = find_all(frame, _BuilderEditArea)[0]
    canvas = find_all(frame, _BuilderMazeCanvas)[0]
    edit_area._activate_set_exit()

    _drag_zone(canvas, Position(2, 0), Position(2, 0))

    assert find_all(frame, ConfirmDialog) == []
    assert edit_area._session.exit == Position(2, 0)


def test_placing_the_exit_on_the_entry_cell_is_a_no_op(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    # Start and goal never share a cell (human-resolved intent): placing
    # the exit on the entry's cell is a silent no-op, no prompt.
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
    edit_area = find_all(frame, _BuilderEditArea)[0]
    canvas = find_all(frame, _BuilderMazeCanvas)[0]
    edit_area._activate_set_exit()

    _drag_zone(canvas, Position(0, 0), Position(0, 0))  # the entry's cell

    assert find_all(frame, ConfirmDialog) == []
    assert edit_area._session.exit is None
    assert edit_area._session.entry == Position(0, 0)
    assert len(canvas.find_withtag("marker")) == 1  # only the seeded entry


def test_placing_the_entry_on_the_exit_cell_is_a_no_op(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    # Mirror of the exit-on-entry case: the entry cannot move onto the
    # exit's cell either.
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
    edit_area = find_all(frame, _BuilderEditArea)[0]
    canvas = find_all(frame, _BuilderMazeCanvas)[0]
    edit_area._activate_set_exit()
    _drag_zone(canvas, Position(2, 0), Position(2, 0))  # place the exit

    edit_area._activate_set_entry()
    _drag_zone(canvas, Position(2, 0), Position(2, 0))  # the exit's cell

    assert find_all(frame, ConfirmDialog) == []
    assert edit_area._session.entry == Position(0, 0)
    assert edit_area._session.exit == Position(2, 0)
    assert len(canvas.find_withtag("marker")) == 2


def test_a_drag_under_a_marker_tool_never_places_a_marker(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    # Placement reuses the same-cell press/release comparison -- a genuine
    # drag (press and release on different cells) under a marker tool is
    # neither a zone operation nor a placement (Story 3.4's Design Notes).
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
    edit_area = find_all(frame, _BuilderEditArea)[0]
    canvas = find_all(frame, _BuilderMazeCanvas)[0]
    edit_area._activate_set_exit()

    _drag_zone(canvas, Position(0, 0), Position(2, 0))  # press ≠ release

    assert edit_area._session.exit is None
    assert edit_area._session.entry == Position(0, 0)
    assert len(canvas.find_withtag("marker")) == 1


def test_redefining_the_exit_at_a_different_cell_requires_confirmation(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    # The exit redefinition path mirrors the entry's: a prompt first, the
    # placement only on Confirm, and a second gated trigger while the
    # dialog is open never stacks a second dialog (`_maybe_confirm`'s
    # no-stack guard).
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
    edit_area = find_all(frame, _BuilderEditArea)[0]
    canvas = find_all(frame, _BuilderMazeCanvas)[0]
    edit_area._activate_set_exit()
    _drag_zone(canvas, Position(2, 0), Position(2, 0))  # first placement

    _drag_zone(canvas, Position(2, 3), Position(2, 3))  # redefine at (2,3)

    dialogs = find_all(frame, ConfirmDialog)
    assert len(dialogs) == 1
    assert edit_area._session.exit == Position(2, 0)  # not moved yet

    _drag_zone(canvas, Position(2, 2), Position(2, 2))  # second gated trigger

    assert len(find_all(frame, ConfirmDialog)) == 1  # no stack

    dialogs[0]._on_confirm_clicked()

    assert edit_area._session.exit == Position(2, 3)
    assert find_all(frame, ConfirmDialog) == []


def test_cancelling_the_exit_redefinition_dialog_leaves_the_marker_in_place(
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
    edit_area = find_all(frame, _BuilderEditArea)[0]
    canvas = find_all(frame, _BuilderMazeCanvas)[0]
    edit_area._activate_set_exit()
    _drag_zone(canvas, Position(2, 0), Position(2, 0))  # first placement

    _drag_zone(canvas, Position(2, 3), Position(2, 3))  # redefine at (2,3)
    dialogs = find_all(frame, ConfirmDialog)
    assert len(dialogs) == 1

    dialogs[0]._on_cancel_clicked()

    assert edit_area._session.exit == Position(2, 0)
    assert find_all(frame, ConfirmDialog) == []
