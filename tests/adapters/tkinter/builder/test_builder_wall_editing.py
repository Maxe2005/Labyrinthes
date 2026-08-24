"""Builder wall editing: HUD chips, Break/Pass-through tools (Story 3.2)."""

import tkinter as tk

from labyrinthes.adapters.tkinter.builder.edit_area import _BuilderEditArea
from labyrinthes.adapters.tkinter.builder.screen import mount
from labyrinthes.adapters.tkinter.common import (
    HudChip,
    Theme,
    ToolButton,
)
from labyrinthes.adapters.tkinter.common.tokens import colors_for
from labyrinthes.domain.level_visibility import Wall
from labyrinthes.domain.movement import Direction
from labyrinthes.domain.position import Position
from tests.adapters.tkinter.builder._helpers import (
    _click_wall,
    _sketch_maze,
)


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


def test_break_mode_arrow_key_across_a_wall_breaks_it_and_moves_the_cursor(
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

    # Break tool is active by default
    edit_area = find_all(frame, _BuilderEditArea)[0]
    walls_chip = next(
        c for c in find_all(frame, HudChip) if c._caption.cget("text") == "WALLS BROKEN"
    )

    edit_area._on_move(Direction.RIGHT)

    assert edit_area._session.cursor == Position(row=0, col=1)
    assert walls_chip._value_label.cget("text") == "1"


def test_pass_through_mode_arrow_key_moves_the_cursor_through_walls(
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
    walls_chip = next(
        c for c in find_all(frame, HudChip) if c._caption.cget("text") == "WALLS BROKEN"
    )

    edit_area._on_move(Direction.RIGHT)  # Pass-through tool: moves through walls freely

    assert edit_area._session.cursor == Position(row=0, col=1)
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
