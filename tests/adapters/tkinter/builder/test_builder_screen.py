import tkinter as tk

from labyrinthes.adapters.tkinter.builder.screen import (
    _BuilderEditArea,
    _BuilderMazeCanvas,
    mount,
)
from labyrinthes.adapters.tkinter.common import (
    HudChip,
    NewMazeDialog,
    SettingsWindow,
    Theme,
    ToolButton,
    TopBar,
)
from labyrinthes.adapters.tkinter.common.navigation import ScreenId
from labyrinthes.adapters.tkinter.common.tokens import colors_for
from labyrinthes.application.confirmation_settings import write_confirm_invalid_input
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.level_visibility import Wall
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.movement import Direction
from labyrinthes.domain.position import Position
from labyrinthes.domain.wall_editing import count_broken_walls
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
    tk_root, navigate_stub, toggle_theme_stub, fake_settings_repository
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
    )

    assert isinstance(frame, tk.Frame)
    assert frame.master is tk_root


def test_mount_renders_a_home_builder_breadcrumb(
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    )

    breadcrumb = find_all(frame, TopBar)[0]._breadcrumb
    assert breadcrumb is not None
    assert [label.cget("text") for label in breadcrumb._labels] == ["Home", "Builder"]


def test_breadcrumb_home_segment_is_clickable_and_navigates_home(
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    )

    breadcrumb = find_all(frame, TopBar)[0]._breadcrumb
    # `tk_root` is withdrawn, so real X11 button-press synthesis isn't
    # reliable; invoke the bound handler directly (see test_icon_btn.py).
    breadcrumb._segment_handlers[0]()

    assert calls == [(ScreenId.HOME, None)]


def test_breadcrumb_trailing_builder_segment_has_no_click_handler(
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    )

    breadcrumb = find_all(frame, TopBar)[0]._breadcrumb
    assert breadcrumb._segment_handlers[1] is None


def test_settings_icon_click_opens_a_non_modal_settings_window_leaving_builder_mounted(
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    )

    top_bar = find_all(frame, TopBar)[0]
    top_bar._theme_toggle_button._on_click()

    assert calls == [1]


def test_open_settings_from_builder_reflects_a_stored_confirmation_value(
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    tk_root, navigate_stub, toggle_theme_stub, fake_settings_repository
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
    )

    dialogs = [c for c in frame.winfo_children() if isinstance(c, NewMazeDialog)]
    assert len(dialogs) == 1
    assert calls == []


def test_confirming_new_maze_dialog_navigates_to_builder_with_the_new_sketch(
    tk_root, navigate_stub, toggle_theme_stub, fake_settings_repository
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
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    )

    chips = find_all(frame, HudChip)
    captions = {chip._caption.cget("text"): chip for chip in chips}
    assert captions["GRID"]._value_label.cget("text") == "4×3"
    assert captions["WALLS BROKEN"]._value_label.cget("text") == "0"


def test_break_mode_click_on_an_interior_wall_breaks_it_and_updates_the_hud(
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    )

    canvas = find_all(frame, tk.Canvas)[0]
    walls_chip = next(
        c for c in find_all(frame, HudChip) if c._caption.cget("text") == "WALLS BROKEN"
    )

    _click_wall(canvas, Wall(0, 1, "top"))  # top border row

    assert walls_chip._value_label.cget("text") == "0"


def test_pass_through_mode_arrow_key_across_a_wall_breaks_it_and_moves_the_cursor(
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    )

    edit_area = find_all(frame, _BuilderEditArea)[0]
    walls_chip = next(
        c for c in find_all(frame, HudChip) if c._caption.cget("text") == "WALLS BROKEN"
    )

    edit_area._on_move(Direction.RIGHT)  # Break tool is active by default; blocked, no break

    assert edit_area._session.cursor == Position(row=0, col=0)
    assert walls_chip._value_label.cget("text") == "0"


def test_pass_through_mode_arrow_key_into_a_border_wall_leaves_cursor_in_place_and_breaks_nothing(
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    tk_root, navigate_stub, toggle_theme_stub, find_all, fake_settings_repository
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
    tk_root, navigate_stub, toggle_theme_stub, fake_settings_repository
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
    )

    dialog = next(c for c in frame.winfo_children() if isinstance(c, NewMazeDialog))
    dialog._on_cancel()

    assert not dialog.winfo_exists()
    assert calls == []
    assert [c for c in frame.winfo_children() if isinstance(c, NewMazeDialog)] == []
