"""Player gameplay screen layout: labeled left/right panels and theme-driven
colors for the new group headings/stage/`maze-frame` (Story 4.10 -- I/O &
Edge-Case Matrix rows 2 and 4)."""

import tkinter as tk

from labyrinthes.adapters.tkinter.common.tokens import Theme, colors_for
from labyrinthes.adapters.tkinter.player.gameplay import GameplayScreen
from tests.adapters.tkinter.player.gameplay._helpers import _classic_maze


class _FakeConfigureEvent:
    """A minimal stand-in for a `<Configure>` event: `Stage._redraw` only
    reads `.width`/`.height` -- real X11 synthesis isn't reliable under a
    withdrawn `tk_root` (mirrors `test_stage.py`'s own)."""

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height


# -- row 2: Player gameplay screen renders -----------------------------------


def test_left_stage_right_are_packed_on_the_correct_sides(
    tk_root, fake_maze_repository, fake_settings_repository
):
    # A regression that packed `_right_panel` with `side="left"` (or
    # similar) would otherwise go undetected -- the per-panel content tests
    # below only check children *within* each panel, never the panels'
    # own placement relative to the centered `Stage`.
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    assert screen._left_panel.pack_info()["side"] == "left"
    assert screen._right_panel.pack_info()["side"] == "right"
    assert screen._stage.pack_info()["side"] == "left"
    assert screen._stage.pack_info()["fill"] == "both"
    assert screen._stage.pack_info()["expand"] == 1


def test_left_panel_shows_mode_levels_difficulty_groups_in_order(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    headings = [c for c in screen._left_panel.winfo_children() if isinstance(c, tk.Label)]
    assert [h.cget("text") for h in headings] == ["MODE", "LEVELS", "DIFFICULTY"]


def test_right_panel_shows_movement_group(tk_root, fake_maze_repository, fake_settings_repository):
    screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )

    headings = [c for c in screen._right_panel.winfo_children() if isinstance(c, tk.Label)]
    assert [h.cget("text") for h in headings] == ["MOVEMENT"]


# -- row 4: theme toggle -----------------------------------------------------


def test_theme_toggle_updates_group_heading_stage_grid_and_maze_frame_colors(
    tk_root, fake_maze_repository, fake_settings_repository
):
    # Mirrors how the composition root actually re-themes (a fresh
    # construction at the new `Theme`, never an in-place mutation) -- see
    # `app/composition_root.py`'s "full re-navigate is the only mode" note.
    light_screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    dark_screen = GameplayScreen(
        tk_root,
        _classic_maze(),
        Theme.DARK,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )
    light_colors = colors_for(Theme.LIGHT)
    dark_colors = colors_for(Theme.DARK)
    assert light_colors.ghost != dark_colors.ghost
    assert light_colors.panel != dark_colors.panel
    assert light_colors.border != dark_colors.border

    light_heading = next(
        c for c in light_screen._left_panel.winfo_children() if isinstance(c, tk.Label)
    )
    dark_heading = next(
        c for c in dark_screen._left_panel.winfo_children() if isinstance(c, tk.Label)
    )
    assert light_heading.cget("foreground") == light_colors.ghost
    assert dark_heading.cget("foreground") == dark_colors.ghost

    light_screen._stage._redraw(_FakeConfigureEvent(200, 150))
    dark_screen._stage._redraw(_FakeConfigureEvent(200, 150))
    light_gridline = light_screen._stage.find_withtag("gridline")[0]
    dark_gridline = dark_screen._stage.find_withtag("gridline")[0]
    # `colors.border`, not `colors.panel` (Story 4.10 follow-up): the two
    # are only a few RGB units apart, imperceptible on Tk's
    # non-anti-aliased canvas.
    assert light_screen._stage.itemcget(light_gridline, "fill") == light_colors.border
    assert dark_screen._stage.itemcget(dark_gridline, "fill") == dark_colors.border

    assert light_screen._maze_frame.cget("highlightbackground") == light_colors.border
    assert dark_screen._maze_frame.cget("highlightbackground") == dark_colors.border
