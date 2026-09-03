"""Builder edit screen layout: labeled left/right panels, chips-only HUD,
and theme-driven colors for the new group headings/stage/`maze-frame`
(Story 4.10 -- I/O & Edge-Case Matrix rows 1 and 4)."""

import tkinter as tk

from labyrinthes.adapters.tkinter.builder.edit_area import _BuilderEditArea
from labyrinthes.adapters.tkinter.common import HudChip, PillButton, Theme
from labyrinthes.adapters.tkinter.common.tokens import colors_for
from tests.adapters.tkinter.builder._helpers import _sketch_maze


class _FakeConfigureEvent:
    """A minimal stand-in for a `<Configure>` event: `Stage._redraw` only
    reads `.width`/`.height` -- real X11 synthesis isn't reliable under a
    withdrawn `tk_root` (mirrors `test_builder_shell_windowing.py`'s own
    `_FakeConfigureEvent` / `test_stage.py`'s)."""

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height


def _area(
    tk_root, navigate_stub, fake_settings_repository, fake_maze_repository, theme=Theme.LIGHT
):
    navigate, _ = navigate_stub
    return _BuilderEditArea(
        tk_root,
        _sketch_maze(4, 3),
        theme,
        navigate=navigate,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )


# -- row 1: Builder edit screen renders -------------------------------------


def test_left_stage_right_are_packed_on_the_correct_sides(
    tk_root, navigate_stub, fake_settings_repository, fake_maze_repository
):
    # A regression that packed `_right_panel` with `side="left"` (or
    # similar) would otherwise go undetected -- the per-panel content tests
    # below only check children *within* each panel, never the panels'
    # own placement relative to the centered `Stage`.
    area = _area(tk_root, navigate_stub, fake_settings_repository, fake_maze_repository)

    assert area._left_panel.pack_info()["side"] == "left"
    assert area._right_panel.pack_info()["side"] == "right"
    assert area._stage.pack_info()["side"] == "left"
    assert area._stage.pack_info()["fill"] == "both"
    assert area._stage.pack_info()["expand"] == 1


def test_left_panel_shows_walls_zones_markers_groups_in_order(
    tk_root, navigate_stub, fake_settings_repository, fake_maze_repository
):
    area = _area(tk_root, navigate_stub, fake_settings_repository, fake_maze_repository)

    children = area._left_panel.winfo_children()
    headings = [c for c in children if isinstance(c, tk.Label)]
    assert [h.cget("text") for h in headings] == ["WALLS", "ZONES", "MARKERS"]

    walls_idx = children.index(headings[0])
    zones_idx = children.index(headings[1])
    markers_idx = children.index(headings[2])
    # Each heading is immediately followed by its own pair of tool buttons,
    # same order as before the panel split.
    assert children[walls_idx + 1] is area._break_button
    assert children[walls_idx + 2] is area._pass_through_button
    assert children[zones_idx + 1] is area._destroy_zone_button
    assert children[zones_idx + 2] is area._restore_zone_button
    assert children[markers_idx + 1] is area._set_entry_button
    assert children[markers_idx + 2] is area._set_exit_button


def test_right_panel_shows_actions_group_with_save_and_test_in_player(
    tk_root, navigate_stub, fake_settings_repository, fake_maze_repository
):
    area = _area(tk_root, navigate_stub, fake_settings_repository, fake_maze_repository)

    children = area._right_panel.winfo_children()
    heading = next(c for c in children if isinstance(c, tk.Label))
    assert heading.cget("text") == "ACTIONS"

    heading_idx = children.index(heading)
    assert children[heading_idx + 1] is area._save_button
    assert children[heading_idx + 2] is area._test_in_player_button
    assert area._save_button._label.cget("text") == "Save"
    assert area._test_in_player_button._label.cget("text") == "Test in Player"


def test_hud_row_contains_only_chips_no_buttons(
    tk_root, navigate_stub, fake_settings_repository, fake_maze_repository
):
    area = _area(tk_root, navigate_stub, fake_settings_repository, fake_maze_repository)

    hud_children = area._hud_row.winfo_children()
    assert len(hud_children) > 0
    assert all(isinstance(c, HudChip) for c in hud_children)
    assert not any(isinstance(c, PillButton) for c in hud_children)


# -- row 4: theme toggle -----------------------------------------------------


def test_theme_toggle_updates_group_heading_stage_grid_and_maze_frame_colors(
    tk_root, navigate_stub, fake_settings_repository, fake_maze_repository
):
    # Mirrors how the composition root actually re-themes (a fresh
    # construction at the new `Theme`, never an in-place mutation) -- see
    # `app/composition_root.py`'s "full re-navigate is the only mode" note.
    light_area = _area(
        tk_root, navigate_stub, fake_settings_repository, fake_maze_repository, theme=Theme.LIGHT
    )
    dark_area = _area(
        tk_root, navigate_stub, fake_settings_repository, fake_maze_repository, theme=Theme.DARK
    )
    light_colors = colors_for(Theme.LIGHT)
    dark_colors = colors_for(Theme.DARK)
    assert light_colors.ghost != dark_colors.ghost
    assert light_colors.panel != dark_colors.panel
    assert light_colors.border != dark_colors.border

    light_heading = next(
        c for c in light_area._left_panel.winfo_children() if isinstance(c, tk.Label)
    )
    dark_heading = next(
        c for c in dark_area._left_panel.winfo_children() if isinstance(c, tk.Label)
    )
    assert light_heading.cget("foreground") == light_colors.ghost
    assert dark_heading.cget("foreground") == dark_colors.ghost

    light_area._stage._redraw(_FakeConfigureEvent(200, 150))
    dark_area._stage._redraw(_FakeConfigureEvent(200, 150))
    light_gridline = light_area._stage.find_withtag("gridline")[0]
    dark_gridline = dark_area._stage.find_withtag("gridline")[0]
    # `colors.border`, not `colors.panel` (Story 4.10 follow-up): the two
    # are only a few RGB units apart, imperceptible on Tk's
    # non-anti-aliased canvas.
    assert light_area._stage.itemcget(light_gridline, "fill") == light_colors.border
    assert dark_area._stage.itemcget(dark_gridline, "fill") == dark_colors.border

    assert light_area._maze_frame.cget("highlightbackground") == light_colors.border
    assert dark_area._maze_frame.cget("highlightbackground") == dark_colors.border
