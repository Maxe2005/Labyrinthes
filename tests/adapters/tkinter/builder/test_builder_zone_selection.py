"""Builder zone selection: the colored live outline and click-click gesture (Story 4.3)."""

import tkinter as tk

from labyrinthes.adapters.tkinter.builder.edit_area import _BuilderEditArea
from labyrinthes.adapters.tkinter.builder.maze_canvas import _BuilderMazeCanvas
from labyrinthes.adapters.tkinter.builder.screen import mount
from labyrinthes.adapters.tkinter.common import (
    HudChip,
    Theme,
)
from labyrinthes.application.builder_session import (
    BuilderTool,
)
from labyrinthes.domain.position import Position
from tests.adapters.tkinter.builder._helpers import (
    _click_at_cell,
    _drag_zone,
    _FakeEvent,
    _release_at_cell,
    _sketch_maze,
)

# -- zone selection: colored outline & click-click gesture (Story 4.3) --------


def _click_at_cell_no_drag(canvas: _BuilderMazeCanvas, cell: Position) -> None:
    """Simulate a click (press + release) at `cell`'s center without dragging."""
    _click_at_cell(canvas, cell)
    _release_at_cell(canvas, cell)


def test_zone_selection_colored_outline_visible_during_drag(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    """AC1: Colored outline is drawn live during drag."""
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
    canvas = find_all(frame, tk.Canvas)[0]
    edit_area._activate_destroy_zone()

    # Press at (0,0) and drag to (1,1) -- outline should exist during drag
    _click_at_cell(canvas, Position(0, 0))
    # During drag, the outline should be drawn
    assert canvas._zone_outline_id is not None
    assert canvas._armed_anchor == Position(0, 0)
    assert canvas._armed_tool is BuilderTool.DESTROY_ZONE

    # Move mouse to (1,1) -- outline should update
    canvas._on_motion(_FakeEvent(2 * canvas._cell_size, 2 * canvas._cell_size))
    assert canvas._zone_outline_id is not None

    # Release commits the zone
    _release_at_cell(canvas, Position(1, 1))
    # Outline should be cleared after commit
    assert canvas._zone_outline_id is None
    assert canvas._armed_anchor is None
    assert canvas._armed_tool is None


def test_zone_selection_click_click_gesture_arms_and_commits(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    """AC3: Click-click gesture -- first click arms, second click commits."""
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
    canvas = find_all(frame, tk.Canvas)[0]
    reach_chip = next(
        c for c in find_all(frame, HudChip) if c._caption.cget("text") == "UNREACHABLE"
    )
    edit_area._activate_destroy_zone()

    # First click at (0,0) -- arms the anchor, shows outline
    _click_at_cell_no_drag(canvas, Position(0, 0))
    assert canvas._armed_anchor == Position(0, 0)
    assert canvas._armed_tool is BuilderTool.DESTROY_ZONE
    assert canvas._zone_outline_id is not None
    # Initial unreachable: 11
    assert reach_chip._value_label.cget("text") == "11"

    # Second click at (1,1) -- commits the zone
    _click_at_cell_no_drag(canvas, Position(1, 1))
    assert canvas._armed_anchor is None
    assert canvas._armed_tool is None
    assert canvas._zone_outline_id is None
    # Zone destroyed: 8 cells reachable = 4 unreachable
    assert reach_chip._value_label.cget("text") == "4"


def test_zone_selection_outline_follows_mouse_during_click_click_gesture(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    """Outline follows mouse live during click-click gesture (between clicks)."""
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
    canvas = find_all(frame, tk.Canvas)[0]
    edit_area._activate_destroy_zone()

    # First click at (0,0) -- arms the anchor
    _click_at_cell_no_drag(canvas, Position(0, 0))
    assert canvas._armed_anchor == Position(0, 0)
    assert canvas._zone_outline_id is not None

    # Move mouse to (2,2) WITHOUT clicking -- outline should follow
    canvas._on_motion(_FakeEvent(2 * canvas._cell_size + 5, 2 * canvas._cell_size + 5))
    assert canvas._zone_outline_id is not None

    # Check outline coordinates span from (0,0) to (2,2)
    x0, y0, x1, y1 = canvas.coords(canvas._zone_outline_id)
    assert x0 == 0
    assert y0 == 0
    assert x1 == 3 * canvas._cell_size
    assert y1 == 3 * canvas._cell_size

    # Second click at (2,2) commits
    _click_at_cell_no_drag(canvas, Position(2, 2))
    assert canvas._armed_anchor is None
    assert canvas._zone_outline_id is None


def test_zone_selection_escape_cancels_armed_anchor(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    """AC4: Escape cancels the armed anchor."""
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
    canvas = find_all(frame, tk.Canvas)[0]
    reach_chip = next(
        c for c in find_all(frame, HudChip) if c._caption.cget("text") == "UNREACHABLE"
    )
    edit_area._activate_destroy_zone()

    # First click arms the anchor
    _click_at_cell_no_drag(canvas, Position(0, 0))
    assert canvas._armed_anchor == Position(0, 0)
    assert canvas._zone_outline_id is not None

    # Press Escape -- should cancel
    edit_area._cancel_armed_anchor()
    assert canvas._armed_anchor is None
    assert canvas._armed_tool is None
    assert canvas._zone_outline_id is None
    # No zone operation should have been applied; unreachable stays 11
    assert reach_chip._value_label.cget("text") == "11"


def test_zone_selection_escape_during_drag_cancels_drag(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    """Escape during a drag (press + move + release) cancels the drag operation."""
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
    canvas = find_all(frame, tk.Canvas)[0]
    reach_chip = next(
        c for c in find_all(frame, HudChip) if c._caption.cget("text") == "UNREACHABLE"
    )
    edit_area._activate_destroy_zone()

    # Press at (0,0) -- starts drag
    _click_at_cell(canvas, Position(0, 0))
    assert canvas._drag_anchor == Position(0, 0)
    assert canvas._drag_tool is BuilderTool.DESTROY_ZONE

    # Move to (2,2) -- drag in progress, outline visible
    canvas._on_motion(_FakeEvent(2 * canvas._cell_size, 2 * canvas._cell_size))
    assert canvas._zone_outline_id is not None

    # Press Escape -- should cancel the drag
    edit_area._cancel_armed_anchor()
    assert canvas._drag_anchor is None
    assert canvas._drag_tool is None
    assert canvas._zone_outline_id is None

    # Release at (2,2) -- should NOT apply the zone (drag was cancelled)
    _release_at_cell(canvas, Position(2, 2))
    assert reach_chip._value_label.cget("text") == "11"


def test_zone_selection_restore_zone_click_click_gesture(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    """Click-click gesture works for Restore Zone tool too."""
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
    canvas = find_all(frame, tk.Canvas)[0]
    edit_area._activate_destroy_zone()
    _drag_zone(canvas, Position(0, 0), Position(1, 1))  # Destroy first

    edit_area._activate_restore_zone()
    # Click-click to restore
    _click_at_cell_no_drag(canvas, Position(0, 0))
    _click_at_cell_no_drag(canvas, Position(1, 1))

    # Zone should be restored (back to original)
    original_grid = _sketch_maze(4, 3).grid
    assert edit_area._session.maze.grid == original_grid


def test_zone_selection_same_cell_click_is_no_op(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    """Click-click on same cell is a no-op (never applies zone)."""
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
    canvas = find_all(frame, tk.Canvas)[0]
    reach_chip = next(
        c for c in find_all(frame, HudChip) if c._caption.cget("text") == "UNREACHABLE"
    )
    edit_area._activate_destroy_zone()

    # Click same cell twice
    _click_at_cell_no_drag(canvas, Position(1, 1))
    _click_at_cell_no_drag(canvas, Position(1, 1))

    # No zone operation applied; unreachable stays 11
    assert reach_chip._value_label.cget("text") == "11"
    assert canvas._armed_anchor is None


def test_zone_selection_tool_switch_mid_gesture_uses_press_time_tool(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    """Tool at press time governs the click-click gesture (press-time capture)."""
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
    canvas = find_all(frame, tk.Canvas)[0]
    edit_area._activate_destroy_zone()

    # First click with Destroy Zone -- arms anchor
    _click_at_cell_no_drag(canvas, Position(0, 0))
    assert canvas._armed_tool is BuilderTool.DESTROY_ZONE

    # Switch to Restore Zone tool mid-gesture
    edit_area._activate_restore_zone()

    # Second click -- should use Destroy Zone (press-time tool)
    _click_at_cell_no_drag(canvas, Position(1, 1))
    # Zone should be destroyed, not restored
    reach_chip = next(
        c for c in find_all(frame, HudChip) if c._caption.cget("text") == "UNREACHABLE"
    )
    # Destroy zone (0,0)-(1,1) makes 8 cells reachable = 4 unreachable
    assert reach_chip._value_label.cget("text") == "4"


def test_zone_selection_break_tool_does_not_arm_anchor(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    """Break tool does not arm anchor for click-click gesture."""
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

    canvas = find_all(frame, tk.Canvas)[0]
    # Break tool is active by default

    # Click should not arm anchor
    _click_at_cell_no_drag(canvas, Position(0, 0))
    assert canvas._armed_anchor is None
    assert canvas._armed_tool is None
