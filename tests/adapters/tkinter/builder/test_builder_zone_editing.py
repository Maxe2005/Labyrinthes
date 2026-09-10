"""Builder zone editing: Destroy/Restore Zone click-and-drag (Story 3.3)."""

from labyrinthes.adapters.tkinter.builder.edit_area import _BuilderEditArea
from labyrinthes.adapters.tkinter.builder.maze_canvas import _BuilderMazeCanvas
from labyrinthes.adapters.tkinter.builder.screen import mount
from labyrinthes.adapters.tkinter.common import (
    HudChip,
    Theme,
    ToolButton,
)
from labyrinthes.domain.level_visibility import Wall
from labyrinthes.domain.position import Position
from labyrinthes.domain.zone_editing import destroy_zone
from tests.adapters.tkinter.builder._helpers import (
    _click_at_cell,
    _drag_zone,
    _FakeEvent,
    _release_at_cell,
    _sketch_maze,
)

# -- zone editing: destroy/restore a rectangular zone (Story 3.3) ----------


def test_destroy_zone_drag_destroys_the_rectangle_in_one_operation(
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
    destroy_button = next(
        b for b in find_all(frame, ToolButton) if b._label.cget("text") == "Destroy Zone"
    )
    destroy_button._on_click()
    assert destroy_button.active is True

    canvas = find_all(frame, _BuilderMazeCanvas)[0]
    reach_chip = next(
        c for c in find_all(frame, HudChip) if c._caption.cget("text") == "UNREACHABLE"
    )
    cursor_before = edit_area._session.cursor
    canvas_cursor_coords_before = canvas.coords(canvas._cursor_id)

    # Destroy zone from (0,0) to (1,1) opens ALL interior walls in that rectangle,
    # connecting not just the 2x2 block but also to cells below and right.
    # Initial: 12 cells, 1 reachable = 11 unreachable
    # After destroy zone (0,0)-(1,1): 8 cells reachable = 4 unreachable
    _drag_zone(canvas, Position(0, 0), Position(1, 1))

    expected_grid = destroy_zone(_sketch_maze(4, 3).grid, Position(0, 0), Position(1, 1))
    assert edit_area._session.maze.grid == expected_grid
    assert reach_chip._value_label.cget("text") == "4"
    # A zone operation never moves the editing cursor -- neither the
    # session's own cursor nor the on-canvas cursor rectangle.
    assert edit_area._session.cursor == cursor_before
    assert canvas.coords(canvas._cursor_id) == canvas_cursor_coords_before


def test_restore_zone_drag_over_a_just_destroyed_zone_returns_it_to_its_initial_state(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    # AC2: restoring the same rectangle just destroyed returns every wall in
    # it exactly to its initial (present) state.
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
    reach_chip = next(
        c for c in find_all(frame, HudChip) if c._caption.cget("text") == "UNREACHABLE"
    )
    original_grid = edit_area._session.maze.grid

    edit_area._activate_destroy_zone()
    _drag_zone(canvas, Position(0, 0), Position(1, 1))
    # After destroy: 4 unreachable
    assert reach_chip._value_label.cget("text") == "4"

    edit_area._activate_restore_zone()
    _drag_zone(canvas, Position(0, 0), Position(1, 1))

    assert edit_area._session.maze.grid == original_grid
    # After restore: back to 11 unreachable
    assert reach_chip._value_label.cget("text") == "11"


def test_zone_tool_active_press_and_release_on_the_same_cell_is_a_no_op(
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
    reach_chip = next(
        c for c in find_all(frame, HudChip) if c._caption.cget("text") == "UNREACHABLE"
    )
    original_grid = edit_area._session.maze.grid
    edit_area._activate_destroy_zone()

    _drag_zone(canvas, Position(1, 1), Position(1, 1))

    assert edit_area._session.maze.grid == original_grid
    assert reach_chip._value_label.cget("text") == "11"


def test_break_mode_click_and_drag_only_toggles_the_directly_clicked_wall(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    # Break mode is active by default: the press itself still behaves like
    # Story 3.2's single-click wall toggle, but the drag/release never
    # triggers a zone operation -- zone dispatch gates on
    # DESTROY_ZONE/RESTORE_ZONE, so a Break-mode drag is ignored.
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
    reach_chip = next(
        c for c in find_all(frame, HudChip) if c._caption.cget("text") == "UNREACHABLE"
    )

    wall = Wall(1, 1, "top")
    x0, y0, x1, y1 = canvas.coords(canvas._wall_items[wall])
    canvas._on_click(_FakeEvent(int((x0 + x1) / 2), int((y0 + y1) / 2)))
    canvas._on_release(_FakeEvent(3 * canvas._cell_size, 2 * canvas._cell_size))

    # Clicking Wall(1,1,"top") (between (0,1) and (1,1)) doesn't connect
    # new cells to entry since (0,1) is still walled from (0,0).
    # Unreachable stays 11
    assert reach_chip._value_label.cget("text") == "11"
    assert edit_area._session.maze.grid.cell_at(Position(1, 1)).has_top_wall is False


def test_keybinding_d_activates_destroy_zone_after_switching_to_pass_through(
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
    destroy_button = next(
        b for b in find_all(frame, ToolButton) if b._label.cget("text") == "Destroy Zone"
    )
    edit_area._activate_pass_through()
    assert destroy_button.active is False

    # `destroy_zone`'s bound handler (Story 3.3's BUILDER-scoped 'd') calls
    # exactly this method -- see `_BuilderEditArea.__init__`'s `bind_shortcut`.
    edit_area._activate_destroy_zone()

    assert destroy_button.active is True
    assert edit_area._session.tool is edit_area._session.tool.DESTROY_ZONE


def test_keybinding_r_activates_restore_zone_after_switching_to_pass_through(
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
    restore_button = next(
        b for b in find_all(frame, ToolButton) if b._label.cget("text") == "Restore Zone"
    )
    edit_area._activate_pass_through()
    assert restore_button.active is False

    # `restore_zone`'s bound handler (Story 3.3's BUILDER-scoped 'r') calls
    # exactly this method -- see `_BuilderEditArea.__init__`'s `bind_shortcut`.
    edit_area._activate_restore_zone()

    assert restore_button.active is True
    assert edit_area._session.tool is edit_area._session.tool.RESTORE_ZONE


def test_switching_from_a_zone_tool_to_break_mid_drag_still_dispatches_the_zone_op(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    # Regression: the tool governing a press-to-release gesture is the one
    # captured at press time, never a live re-read of `session.tool` at
    # release. Pressing with Destroy Zone active, then switching to Break
    # (e.g. via a keybinding) before releasing, must still destroy the
    # dragged zone -- the live tool having drifted to Break by release time
    # must not suppress it.
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
    edit_area._activate_destroy_zone()

    _click_at_cell(canvas, Position(0, 0))
    edit_area._activate_break()  # tool switches mid-drag, mouse still "held"
    _release_at_cell(canvas, Position(1, 1))

    expected_grid = destroy_zone(_sketch_maze(4, 3).grid, Position(0, 0), Position(1, 1))
    assert edit_area._session.maze.grid == expected_grid
    # The live tool stays whatever was last activated -- the zone dispatch
    # never overwrites `session.tool`.
    assert edit_area._session.tool is edit_area._session.tool.BREAK


def test_switching_from_break_to_a_zone_tool_mid_drag_does_not_trigger_a_zone_operation(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    # The mirror case: pressing while Break is active (firing Story 3.2's
    # single-click wall toggle immediately), then switching to Destroy Zone
    # before releasing elsewhere, must never additionally apply a zone
    # operation -- the gesture is governed by Break, the tool captured at
    # press time.
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
    reach_chip = next(
        c for c in find_all(frame, HudChip) if c._caption.cget("text") == "UNREACHABLE"
    )

    wall = Wall(1, 1, "top")  # Break is active by default
    x0, y0, x1, y1 = canvas.coords(canvas._wall_items[wall])
    canvas._on_click(_FakeEvent(int((x0 + x1) / 2), int((y0 + y1) / 2)))
    edit_area._activate_destroy_zone()  # tool switches mid-drag
    _release_at_cell(canvas, Position(2, 2))

    # Only the press-time single wall toggle applied -- no zone-wide change.
    # Clicking Wall(1,1,"top") doesn't connect new cells to entry.
    assert reach_chip._value_label.cget("text") == "11"
    assert edit_area._session.maze.grid.cell_at(Position(1, 1)).has_top_wall is False


def test_a_stray_release_without_a_preceding_press_does_not_replay_a_stale_drag(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    # Regression: `_drag_anchor`/`_drag_tool` must be consumed (reset to
    # `None`) after a release fires (or declines to fire) a zone operation,
    # so a second, stray `<ButtonRelease-1>` with no intervening
    # `<Button-1>` can never replay the same anchor as another operation.
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
    edit_area._activate_destroy_zone()

    _drag_zone(canvas, Position(0, 0), Position(1, 1))
    grid_after_first_drag = edit_area._session.maze.grid

    # A second release with no new press in between -- must be a no-op.
    _release_at_cell(canvas, Position(2, 2))

    assert edit_area._session.maze.grid == grid_after_first_drag
