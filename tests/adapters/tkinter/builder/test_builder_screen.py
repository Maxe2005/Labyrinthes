import tkinter as tk

from labyrinthes.adapters.tkinter.builder.screen import (
    _BuilderEditArea,
    _BuilderMazeCanvas,
    _SaveNameDialog,
    mount,
)
from labyrinthes.adapters.tkinter.common import (
    ConfirmDialog,
    HudChip,
    NewMazeDialog,
    PillButton,
    SettingsWindow,
    Theme,
    ToolButton,
    TopBar,
)
from labyrinthes.adapters.tkinter.common.navigation import ScreenId
from labyrinthes.adapters.tkinter.common.tokens import colors_for
from labyrinthes.application.builder_session import BuilderTool
from labyrinthes.application.confirmation_settings import (
    write_confirm_invalid_input,
    write_confirm_redefine_marker,
)
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.level_visibility import Wall
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.movement import Direction
from labyrinthes.domain.position import Position
from labyrinthes.domain.wall_editing import count_broken_walls, toggle_wall
from labyrinthes.domain.zone_editing import destroy_zone


class _FakeEvent:
    """A minimal stand-in for `tk.Event`: `_on_click` only reads `.x`/`.y`,
    and real X11 click synthesis isn't reliable under a withdrawn `tk_root`
    (see e.g. `test_settings_icon_click_...`'s comment above)."""

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


def _sketch_maze(columns: int = 4, rows: int = 3) -> Maze:
    return Maze(
        grid=Grid.filled(columns, rows),
        entry=Position(row=0, col=0),
        exit=Position(row=rows - 1, col=columns - 1),
        kind=MazeKind.SKETCH,
        id=None,
    )


def _classic_maze(columns: int = 4, rows: int = 3) -> Maze:
    return Maze(
        grid=Grid.filled(columns, rows),
        entry=Position(row=0, col=0),
        exit=Position(row=rows - 1, col=columns - 1),
        kind=MazeKind.CLASSIC,
        id=None,
    )


def _open_top_row_maze() -> Maze:
    """A 4×3 sketch with an open corridor along the top row and one step
    down into the interior -- lets the cursor move between unmarked border
    cells and into an interior cell without needing to break walls first."""
    grid = Grid.filled(4, 3)
    grid = toggle_wall(grid, Wall(row=0, col=1, side="left"))  # (0,0)-(0,1)
    grid = toggle_wall(grid, Wall(row=0, col=2, side="left"))  # (0,1)-(0,2)
    grid = toggle_wall(grid, Wall(row=1, col=1, side="top"))  # (0,1)-(1,1)
    return Maze(
        grid=grid,
        entry=Position(row=0, col=0),
        exit=Position(row=2, col=3),
        kind=MazeKind.SKETCH,
        id=None,
    )


def _click_wall(canvas: _BuilderMazeCanvas, wall: Wall) -> None:
    """Simulate a click on `wall`'s bar/gap: the midpoint of its canvas item."""
    x0, y0, x1, y1 = canvas.coords(canvas._wall_items[wall])
    canvas._on_click(_FakeEvent(int((x0 + x1) / 2), int((y0 + y1) / 2)))


def _cell_center_event(canvas: _BuilderMazeCanvas, cell: Position) -> _FakeEvent:
    size = canvas._cell_size
    return _FakeEvent(cell.col * size + size // 2, cell.row * size + size // 2)


def _click_at_cell(canvas: _BuilderMazeCanvas, cell: Position) -> None:
    """Simulate a `<Button-1>` press at `cell`'s center."""
    canvas._on_click(_cell_center_event(canvas, cell))


def _release_at_cell(canvas: _BuilderMazeCanvas, cell: Position) -> None:
    """Simulate a `<ButtonRelease-1>` at `cell`'s center."""
    canvas._on_release(_cell_center_event(canvas, cell))


def _drag_zone(canvas: _BuilderMazeCanvas, anchor: Position, end: Position) -> None:
    """Simulate a press-drag-release gesture: press at `anchor`'s cell center,
    release at `end`'s cell center."""
    _click_at_cell(canvas, anchor)
    _release_at_cell(canvas, end)


def test_mount_returns_a_frame_parented_under_the_given_parent(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    assert isinstance(frame, tk.Frame)
    assert frame.master is tk_root


def test_mount_renders_a_home_builder_breadcrumb(
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
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    breadcrumb = find_all(frame, TopBar)[0]._breadcrumb
    assert breadcrumb is not None
    assert [label.cget("text") for label in breadcrumb._labels] == ["Home", "Builder"]


def test_breadcrumb_home_segment_is_clickable_and_navigates_home(
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
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    breadcrumb = find_all(frame, TopBar)[0]._breadcrumb
    # `tk_root` is withdrawn, so real X11 button-press synthesis isn't
    # reliable; invoke the bound handler directly (see test_icon_btn.py).
    breadcrumb._segment_handlers[0]()

    assert calls == [(ScreenId.HOME, None)]


def test_breadcrumb_trailing_builder_segment_has_no_click_handler(
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
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    breadcrumb = find_all(frame, TopBar)[0]._breadcrumb
    assert breadcrumb._segment_handlers[1] is None


def test_settings_icon_click_opens_a_non_modal_settings_window_leaving_builder_mounted(
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
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    top_bar = find_all(frame, TopBar)[0]
    top_bar._settings_button._on_click()

    # `SettingsWindow` is parented to `tk_root` (the persistent container),
    # not to `frame` itself (Story 1.11) -- see
    # `test_destroying_the_screens_frame_leaves_an_open_settings_window_open`.
    settings_windows = [c for c in tk_root.winfo_children() if isinstance(c, SettingsWindow)]
    assert len(settings_windows) == 1
    assert settings_windows[0].grab_status() is None
    assert frame.winfo_exists()


def test_destroying_the_screens_frame_leaves_an_open_settings_window_open(
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
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    top_bar = find_all(frame, TopBar)[0]
    top_bar._settings_button._on_click()

    settings_windows = [c for c in tk_root.winfo_children() if isinstance(c, SettingsWindow)]
    assert len(settings_windows) == 1
    settings_window = settings_windows[0]

    # The exact operation `Router.navigate()` performs on the
    # previously-mounted screen's frame (Story 1.11: `SettingsWindow` is
    # parented to the persistent container, not to `frame`, so this no
    # longer cascades into destroying it -- see `SettingsWindow`'s
    # docstring).
    frame.destroy()

    assert settings_window.winfo_exists() == 1


def test_theme_toggle_icon_click_invokes_the_passed_in_toggle_theme_callable(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, _ = navigate_stub
    toggle_theme, calls = toggle_theme_stub
    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    top_bar = find_all(frame, TopBar)[0]
    top_bar._theme_toggle_button._on_click()

    assert calls == [1]


def test_open_settings_from_builder_reflects_a_stored_confirmation_value(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    write_confirm_invalid_input(fake_settings_repository, False)
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    top_bar = find_all(frame, TopBar)[0]
    top_bar._settings_button._on_click()

    settings_windows = [c for c in tk_root.winfo_children() if isinstance(c, SettingsWindow)]
    assert len(settings_windows) == 1
    settings_windows[0]._select_category("Confirmation")
    assert settings_windows[0]._confirmation_rows["Alert me about invalid input"].get() is False
    settings_windows[0].destroy()


# -- state=None: New Maze Dialog entry state (Story 3.2) --------------------


def test_cold_open_with_state_none_opens_the_new_maze_dialog(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, calls = navigate_stub
    toggle_theme, _ = toggle_theme_stub

    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    dialogs = [c for c in frame.winfo_children() if isinstance(c, NewMazeDialog)]
    assert len(dialogs) == 1
    assert calls == []


def test_confirming_new_maze_dialog_navigates_to_builder_with_the_new_sketch(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, calls = navigate_stub
    toggle_theme, _ = toggle_theme_stub

    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    dialog = next(c for c in frame.winfo_children() if isinstance(c, NewMazeDialog))
    dialog._entries["columns"].delete(0, "end")
    dialog._entries["columns"].insert(0, "20")
    dialog._entries["rows"].delete(0, "end")
    dialog._entries["rows"].insert(0, "15")
    dialog._on_confirm_clicked()

    assert len(calls) == 1
    screen_id, maze = calls[0]
    assert screen_id is ScreenId.BUILDER
    assert maze.kind is MazeKind.SKETCH
    assert maze.id is None
    assert maze.grid.width == 20
    assert maze.grid.height == 15


# -- state=Maze: edit UI (Story 3.2) -----------------------------------------


def test_mount_with_a_maze_renders_hud_chips_for_grid_size_and_zero_walls_broken(
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

    chips = find_all(frame, HudChip)
    captions = {chip._caption.cget("text"): chip for chip in chips}
    assert captions["GRID"]._value_label.cget("text") == "4×3"
    assert captions["WALLS BROKEN"]._value_label.cget("text") == "0"


def test_break_mode_click_on_an_interior_wall_breaks_it_and_updates_the_hud(
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

    canvas = find_all(frame, tk.Canvas)[0]
    walls_chip = next(
        c for c in find_all(frame, HudChip) if c._caption.cget("text") == "WALLS BROKEN"
    )

    _click_wall(canvas, Wall(1, 1, "top"))

    assert walls_chip._value_label.cget("text") == "1"

    # Clicking the same segment again restores it (toggle).
    _click_wall(canvas, Wall(1, 1, "top"))

    assert walls_chip._value_label.cget("text") == "0"


def test_break_mode_click_on_a_border_wall_is_a_no_op(
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

    canvas = find_all(frame, tk.Canvas)[0]
    walls_chip = next(
        c for c in find_all(frame, HudChip) if c._caption.cget("text") == "WALLS BROKEN"
    )

    _click_wall(canvas, Wall(0, 1, "top"))  # top border row

    assert walls_chip._value_label.cget("text") == "0"


def test_pass_through_mode_arrow_key_across_a_wall_breaks_it_and_moves_the_cursor(
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

    pass_through_button = next(
        b for b in find_all(frame, ToolButton) if b._label.cget("text") == "Pass-through"
    )
    pass_through_button._on_click()
    assert pass_through_button.active is True

    edit_area = find_all(frame, _BuilderEditArea)[0]
    walls_chip = next(
        c for c in find_all(frame, HudChip) if c._caption.cget("text") == "WALLS BROKEN"
    )

    edit_area._on_move(Direction.RIGHT)

    assert edit_area._session.cursor == Position(row=0, col=1)
    assert walls_chip._value_label.cget("text") == "1"


def test_break_mode_arrow_key_moves_the_cursor_without_breaking_any_wall(
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
    walls_chip = next(
        c for c in find_all(frame, HudChip) if c._caption.cget("text") == "WALLS BROKEN"
    )

    edit_area._on_move(Direction.RIGHT)  # Break tool is active by default; blocked, no break

    assert edit_area._session.cursor == Position(row=0, col=0)
    assert walls_chip._value_label.cget("text") == "0"


def test_pass_through_mode_arrow_key_into_a_border_wall_leaves_cursor_in_place_and_breaks_nothing(
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
    walls_chip = next(
        c for c in find_all(frame, HudChip) if c._caption.cget("text") == "WALLS BROKEN"
    )
    edit_area._activate_pass_through()

    edit_area._on_move(Direction.UP)  # cursor is already at row 0: hits the top border

    assert edit_area._session.cursor == Position(row=0, col=0)
    assert walls_chip._value_label.cget("text") == "0"


def test_keybinding_b_activates_break_wall_after_switching_to_pass_through(
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
    break_button = next(
        b for b in find_all(frame, ToolButton) if b._label.cget("text") == "Break Wall"
    )
    edit_area._activate_pass_through()
    assert break_button.active is False

    # `break_wall`'s bound handler (Story 3.2's BUILDER-scoped 'b') calls
    # exactly this method -- see `_BuilderEditArea.__init__`'s `bind_shortcut`.
    edit_area._activate_break()

    assert break_button.active is True
    assert edit_area._session.tool is edit_area._session.tool.BREAK


def test_pass_through_mode_click_on_a_wall_is_a_no_op(
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
    edit_area._activate_pass_through()
    canvas = find_all(frame, tk.Canvas)[0]
    walls_chip = next(
        c for c in find_all(frame, HudChip) if c._caption.cget("text") == "WALLS BROKEN"
    )

    # Break-mode-only: a direct click never toggles a wall while Pass-through
    # is active -- Pass-through only ever breaks a wall via cursor movement.
    _click_wall(canvas, Wall(1, 1, "top"))

    assert walls_chip._value_label.cget("text") == "0"


def test_wall_bar_canvas_color_reflects_present_vs_broken_state(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    find_all,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, _ = navigate_stub
    toggle_theme, _ = toggle_theme_stub
    colors = colors_for(Theme.LIGHT)

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
    item = canvas._wall_items[Wall(1, 1, "top")]
    assert canvas.itemcget(item, "fill") == colors.wall

    _click_wall(canvas, Wall(1, 1, "top"))

    assert canvas.itemcget(item, "fill") == colors.corridor

    _click_wall(canvas, Wall(1, 1, "top"))

    assert canvas.itemcget(item, "fill") == colors.wall


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

    canvas = find_all(frame, tk.Canvas)[0]
    walls_chip = next(
        c for c in find_all(frame, HudChip) if c._caption.cget("text") == "WALLS BROKEN"
    )
    cursor_before = edit_area._session.cursor
    canvas_cursor_coords_before = canvas.coords(canvas._cursor_id)

    _drag_zone(canvas, Position(0, 0), Position(1, 1))

    expected_grid = destroy_zone(_sketch_maze(4, 3).grid, Position(0, 0), Position(1, 1))
    assert edit_area._session.maze.grid == expected_grid
    assert walls_chip._value_label.cget("text") == str(count_broken_walls(expected_grid))
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
    canvas = find_all(frame, tk.Canvas)[0]
    walls_chip = next(
        c for c in find_all(frame, HudChip) if c._caption.cget("text") == "WALLS BROKEN"
    )
    original_grid = edit_area._session.maze.grid

    edit_area._activate_destroy_zone()
    _drag_zone(canvas, Position(0, 0), Position(1, 1))
    assert walls_chip._value_label.cget("text") != "0"

    edit_area._activate_restore_zone()
    _drag_zone(canvas, Position(0, 0), Position(1, 1))

    assert edit_area._session.maze.grid == original_grid
    assert walls_chip._value_label.cget("text") == "0"


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
    canvas = find_all(frame, tk.Canvas)[0]
    walls_chip = next(
        c for c in find_all(frame, HudChip) if c._caption.cget("text") == "WALLS BROKEN"
    )
    original_grid = edit_area._session.maze.grid
    edit_area._activate_destroy_zone()

    _drag_zone(canvas, Position(1, 1), Position(1, 1))

    assert edit_area._session.maze.grid == original_grid
    assert walls_chip._value_label.cget("text") == "0"


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
    canvas = find_all(frame, tk.Canvas)[0]
    walls_chip = next(
        c for c in find_all(frame, HudChip) if c._caption.cget("text") == "WALLS BROKEN"
    )

    wall = Wall(1, 1, "top")
    x0, y0, x1, y1 = canvas.coords(canvas._wall_items[wall])
    canvas._on_click(_FakeEvent(int((x0 + x1) / 2), int((y0 + y1) / 2)))
    canvas._on_release(_FakeEvent(3 * canvas._cell_size, 2 * canvas._cell_size))

    assert walls_chip._value_label.cget("text") == "1"
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
    canvas = find_all(frame, tk.Canvas)[0]
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
    canvas = find_all(frame, tk.Canvas)[0]
    walls_chip = next(
        c for c in find_all(frame, HudChip) if c._caption.cget("text") == "WALLS BROKEN"
    )

    wall = Wall(1, 1, "top")  # Break is active by default
    x0, y0, x1, y1 = canvas.coords(canvas._wall_items[wall])
    canvas._on_click(_FakeEvent(int((x0 + x1) / 2), int((y0 + y1) / 2)))
    edit_area._activate_destroy_zone()  # tool switches mid-drag
    _release_at_cell(canvas, Position(2, 2))

    # Only the press-time single wall toggle applied -- no zone-wide change.
    assert walls_chip._value_label.cget("text") == "1"
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
    canvas = find_all(frame, tk.Canvas)[0]
    edit_area._activate_destroy_zone()

    _drag_zone(canvas, Position(0, 0), Position(1, 1))
    grid_after_first_drag = edit_area._session.maze.grid

    # A second release with no new press in between -- must be a no-op.
    _release_at_cell(canvas, Position(2, 2))

    assert edit_area._session.maze.grid == grid_after_first_drag


def test_cancelling_the_new_maze_dialog_destroys_it_and_leaves_the_frame_empty(
    tk_root,
    navigate_stub,
    toggle_theme_stub,
    fake_settings_repository,
    fake_maze_repository,
):
    navigate, calls = navigate_stub
    toggle_theme, _ = toggle_theme_stub

    frame = mount(
        tk_root,
        None,
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )

    dialog = next(c for c in frame.winfo_children() if isinstance(c, NewMazeDialog))
    dialog._on_cancel()

    assert not dialog.winfo_exists()
    assert calls == []
    assert [c for c in frame.winfo_children() if isinstance(c, NewMazeDialog)] == []


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
    canvas = find_all(frame, tk.Canvas)[0]
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
    canvas = find_all(frame, tk.Canvas)[0]
    edit_area._activate_set_exit()

    _drag_zone(canvas, Position(2, 0), Position(2, 0))

    assert edit_area._session.exit == Position(2, 0)
    assert edit_area._session.maze.exit == Position(2, 0)
    # Entry (seeded) + exit = two distinct marker items.
    assert len(canvas.find_withtag("marker")) == 2


def test_clicking_an_interior_cell_with_set_exit_is_a_no_op(
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
    canvas = find_all(frame, tk.Canvas)[0]
    edit_area._activate_set_exit()

    _drag_zone(canvas, Position(1, 1), Position(1, 1))

    assert edit_area._session.exit is None
    assert edit_area._session.maze.exit == Position(2, 3)
    assert len(canvas.find_withtag("marker")) == 1  # only the seeded entry


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
    canvas = find_all(frame, tk.Canvas)[0]
    edit_area._activate_set_exit()

    assert canvas.find_withtag("ghost-marker") == ()  # entry cell: no ghost

    edit_area._on_move(Direction.RIGHT)  # cursor (0,1), border, unmarked

    ghost = canvas.find_withtag("ghost-marker")
    assert len(ghost) == 2  # dashed rect + "?" glyph
    cx, cy = canvas._cell_center(Position(0, 1))
    x0, y0, x1, y1 = canvas.bbox(ghost[0])
    assert (x0 + x1) // 2 == cx
    assert (y0 + y1) // 2 == cy

    edit_area._on_move(Direction.RIGHT)  # cursor (0,2), border, unmarked

    cx, cy = canvas._cell_center(Position(0, 2))
    x0, y0, x1, y1 = canvas.bbox(canvas.find_withtag("ghost-marker")[0])
    assert (x0 + x1) // 2 == cx
    assert (y0 + y1) // 2 == cy


def test_set_exit_ghost_is_hidden_when_the_cursor_moves_to_an_interior_cell(
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
        _open_top_row_maze(),
        navigate,
        Theme.LIGHT,
        toggle_theme,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )
    edit_area = find_all(frame, _BuilderEditArea)[0]
    canvas = find_all(frame, tk.Canvas)[0]
    edit_area._activate_set_exit()
    edit_area._on_move(Direction.RIGHT)  # cursor (0,1): border, ghost shows

    assert len(canvas.find_withtag("ghost-marker")) == 2

    edit_area._on_move(Direction.DOWN)  # cursor (1,1): interior, ghost hidden

    assert canvas.find_withtag("ghost-marker") == ()


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
    canvas = find_all(frame, tk.Canvas)[0]
    edit_area._activate_set_exit()
    edit_area._on_move(Direction.RIGHT)  # cursor (0,1), border, unmarked

    assert len(canvas.find_withtag("ghost-marker")) == 2

    _drag_zone(canvas, Position(0, 1), Position(0, 1))  # place exit at (0,1)

    assert canvas.find_withtag("ghost-marker") == ()  # cursor sits on the exit

    edit_area._on_move(Direction.RIGHT)  # cursor (0,2): ghost reappears

    assert len(canvas.find_withtag("ghost-marker")) == 2


def test_set_exit_ghost_is_never_rendered_for_other_tools(
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
    canvas = find_all(frame, tk.Canvas)[0]

    edit_area._activate_break()
    assert canvas.find_withtag("ghost-marker") == ()

    edit_area._activate_set_entry()
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
    canvas = find_all(frame, tk.Canvas)[0]
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
    canvas = find_all(frame, tk.Canvas)[0]
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
    canvas = find_all(frame, tk.Canvas)[0]
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
    canvas = find_all(frame, tk.Canvas)[0]
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
    canvas = find_all(frame, tk.Canvas)[0]
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
    canvas = find_all(frame, tk.Canvas)[0]
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
    canvas = find_all(frame, tk.Canvas)[0]
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
    canvas = find_all(frame, tk.Canvas)[0]
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
    canvas = find_all(frame, tk.Canvas)[0]
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
    canvas = find_all(frame, tk.Canvas)[0]
    edit_area._activate_set_exit()
    _drag_zone(canvas, Position(2, 0), Position(2, 0))  # first placement

    _drag_zone(canvas, Position(2, 3), Position(2, 3))  # redefine at (2,3)
    dialogs = find_all(frame, ConfirmDialog)
    assert len(dialogs) == 1

    dialogs[0]._on_cancel_clicked()

    assert edit_area._session.exit == Position(2, 0)
    assert find_all(frame, ConfirmDialog) == []


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
