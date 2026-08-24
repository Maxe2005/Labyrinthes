"""`_BuilderMazeCanvas` -- Builder maze rendering + click/drag hit-testing.

Renders every wall position (border + interior) as a bar/gap, hit-testable
back to its `Wall`, plus an editing-cursor rectangle. Every wall position
gets exactly one permanent canvas line item, colored `colors.wall` (present)
or `colors.corridor` (broken -- a gap that blends into the background, per
the spec's "gaps for broken segments"). Editing only ever recolors these
items (`refresh_walls()`); positions are fixed for the canvas's lifetime, so
a gap stays clickable to restore later.

Click-and-drag zone editing (Story 3.3): the canvas compares the press cell
to the release cell (both cell-quantized via `_pixel_to_cell`) and fires
`on_zone_dragged` only when they differ -- a same-cell click is never a zone
operation, no separate pixel-distance threshold. The active tool is captured
at *press* time (via `capture_tool`) and threaded through to
`on_zone_dragged`/`application.builder_session.apply_zone_operation` unchanged, rather
than re-read live at release time -- so switching tools mid-drag (e.g. a
keybinding fired while the button is still held) can never compound a
press-time action under one tool with a release-time zone operation under a
different one.

Zone selection also supports a click-click gesture (Story 4.3): a first
click while a zone tool is active arms an anchor and draws a live colored
outline that follows the mouse; a second click on a different cell commits
the zone, a second click on the same cell (or Escape, via `_cancel_drag`)
cancels it.

Entry/exit marking (Story 3.4): `refresh_markers()` renders the entry as a
filled square (`colors.entry`), the exit as a filled diamond (`colors.exit`),
and, only while Set Exit is active, a dashed-`?` ghost preview
(`colors.ghost`) at the cursor cell when that cell is on the border and
holds no marker -- driven entirely by `_BuilderEditArea._sync_markers`,
which recomputes the ghost position and calls this method; the canvas itself
holds no marker-placement logic.

Kept local to `adapters/tkinter/builder/` per the Boundaries (Builder-
specific widgets never move to `adapters/tkinter/common/`).
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from labyrinthes.adapters.tkinter.common import TYPOGRAPHY, FontSpec, Theme
from labyrinthes.adapters.tkinter.common.tokens import ColorTokens, colors_for
from labyrinthes.application.builder_session import BuilderTool
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.level_visibility import Wall
from labyrinthes.domain.maze import Maze
from labyrinthes.domain.position import Position

__all__ = ["_BuilderMazeCanvas"]

_MAX_CANVAS_SPAN = 480
_MIN_CELL_SIZE = 16
_MAX_CELL_SIZE = 40
_WALL_WIDTH = 2
# Fraction of a cell a marker's radius spans -- same scale as the Player's
# `maze_canvas._MARKER_SCALE` (Story 3.4's marker geometry reference).
_MARKER_SCALE = 0.6
# Fraction of a cell the Set Exit ghost's dashed outline is inset from the
# cell edge (scales with the cell so it never overflows the smallest cells).
_GHOST_INSET_SCALE = 0.25
# Fraction of a cell the ghost's "?" glyph's font size spans.
_GHOST_FONT_SCALE = 0.55
# Search radius (px) `find_closest()` accepts around a click -- without it,
# a click meant for a *broken* (gap) wall would have to land exactly on the
# invisible hairline drawn there (see `_draw_wall_bar`).
_CLICK_HALO = 6


def _cell_size(width: int, height: int) -> int:
    """`clamp(min(480 // width, 480 // height), 16, 40)` px -- same clamp as
    `player/maze_canvas.py`'s `_cell_size`, kept local per the Boundaries
    (Builder-specific widgets stay local to `adapters/tkinter/builder/`)."""
    raw = min(_MAX_CANVAS_SPAN // width, _MAX_CANVAS_SPAN // height)
    return max(_MIN_CELL_SIZE, min(_MAX_CELL_SIZE, raw))


class _BuilderMazeCanvas(tk.Canvas):
    """Renders every wall position (border + interior) as a bar/gap, hit-testable
    back to its `Wall`, plus an editing-cursor rectangle.

    Every wall position gets exactly one permanent canvas line item, colored
    `colors.wall` (present) or `colors.corridor` (broken -- a gap that blends
    into the background, per the spec's "gaps for broken segments"). Editing
    only ever recolors these items (`refresh_walls()`); positions are fixed
    for the canvas's lifetime, so a gap stays clickable to restore later.
    """

    def __init__(
        self,
        parent: tk.Widget,
        *,
        maze: Maze,
        cursor: Position,
        theme: Theme,
        on_wall_clicked: Callable[[Wall], None],
        on_zone_dragged: Callable[[BuilderTool, Position, Position], None],
        on_cell_clicked: Callable[[BuilderTool, Position], None],
        capture_tool: Callable[[], BuilderTool],
    ) -> None:
        self._theme = theme
        self._on_wall_clicked = on_wall_clicked
        self._on_zone_dragged = on_zone_dragged
        self._on_cell_clicked = on_cell_clicked
        self._capture_tool = capture_tool
        grid = maze.grid
        self._grid_width = grid.width
        self._grid_height = grid.height
        self._cell_size = _cell_size(grid.width, grid.height)
        self._drag_anchor: Position | None = None
        self._drag_tool: BuilderTool | None = None
        # Armed anchor for click-click zone gesture (Story 4.3): set on first
        # click when a zone tool is active, cleared on Escape or second click.
        self._armed_anchor: Position | None = None
        self._armed_tool: BuilderTool | None = None
        self._anchor_just_armed: bool = False
        self._zone_outline_id: int | None = None
        self._marker_radius = int(round(self._cell_size * _MARKER_SCALE / 2))
        self._ghost_font = FontSpec(
            family=TYPOGRAPHY.heading.family,
            size=max(8, int(self._cell_size * _GHOST_FONT_SCALE)),
            weight="700",
        ).to_tk_font()
        colors = colors_for(theme)

        super().__init__(
            parent,
            width=grid.width * self._cell_size,
            height=grid.height * self._cell_size,
            background=colors.corridor,
            highlightthickness=0,
            bd=0,
        )

        self._wall_items: dict[Wall, int] = {}
        self._item_walls: dict[int, Wall] = {}
        self._draw_walls(grid, colors)
        # Drawn last so the cursor's own creation-order stacks it above
        # every wall bar/gap, permanently (wall items are only ever
        # recolored after this, never deleted/recreated).
        self._cursor_id = self._draw_cursor(cursor, colors)

        self.bind("<Button-1>", self._on_click)
        self.bind("<ButtonRelease-1>", self._on_release)
        # Live outline during zone selection (drag or click-click gesture).
        self.bind("<B1-Motion>", self._on_motion)

    def _draw_walls(self, grid: Grid, colors: ColorTokens) -> None:
        # Only genuine wall positions: a "top" bit is only meaningful for a
        # real column (`col < width`), a "left" bit only for a real row
        # (`row < height`) -- see `domain.wall_editing.count_broken_walls`'s
        # docstring on the padding row/column's dead bits. Border positions
        # (row/col 0 or height/width) are included and drawn like any other
        # wall; clicking one is refused by `apply_wall_toggle` (caught,
        # no-op) rather than excluded from hit-testing here.
        for row in range(grid.height + 1):
            for col in range(grid.width):
                self._draw_wall_bar(Wall(row, col, "top"), grid, colors)
        for row in range(grid.height):
            for col in range(grid.width + 1):
                self._draw_wall_bar(Wall(row, col, "left"), grid, colors)

    def _wall_present(self, wall: Wall, grid: Grid) -> bool:
        cell = grid.cell_at(Position(row=wall.row, col=wall.col))
        return cell.has_top_wall if wall.side == "top" else cell.has_left_wall

    def _draw_wall_bar(self, wall: Wall, grid: Grid, colors: ColorTokens) -> None:
        size = self._cell_size
        color = colors.wall if self._wall_present(wall, grid) else colors.corridor
        x0, y0 = wall.col * size, wall.row * size
        if wall.side == "top":
            item = self.create_line(
                x0, y0, x0 + size, y0, width=_WALL_WIDTH, fill=color, tags=("wall",)
            )
        else:
            item = self.create_line(
                x0, y0, x0, y0 + size, width=_WALL_WIDTH, fill=color, tags=("wall",)
            )
        self._wall_items[wall] = item
        self._item_walls[item] = wall

    def refresh_walls(self, grid: Grid) -> None:
        """Recolor every wall bar to match `grid`'s current present/broken state."""
        colors = colors_for(self._theme)
        for wall, item in self._wall_items.items():
            color = colors.wall if self._wall_present(wall, grid) else colors.corridor
            self.itemconfigure(item, fill=color)

    def _draw_cursor(self, position: Position, colors: ColorTokens) -> int:
        size = self._cell_size
        cx = position.col * size + size // 2
        cy = position.row * size + size // 2
        radius = int(round(size * _MARKER_SCALE / 2))
        return self.create_oval(
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
            fill=colors.accent,
            outline="",
            tags=("cursor",),
        )

    def set_cursor(self, position: Position) -> None:
        """Move the cursor circle to `position`'s cell, without redrawing walls."""
        size = self._cell_size
        cx = position.col * size + size // 2
        cy = position.row * size + size // 2
        radius = int(round(size * _MARKER_SCALE / 2))
        self.coords(self._cursor_id, cx - radius, cy - radius, cx + radius, cy + radius)

    def _pixel_to_cell(self, x: int, y: int) -> Position:
        """The grid cell containing pixel `(x, y)`, clamped to the grid's
        bounds -- a drag that ends (or starts) outside the canvas still
        resolves to the nearest edge cell rather than raising."""
        size = self._cell_size
        col = max(0, min(self._grid_width - 1, x // size))
        row = max(0, min(self._grid_height - 1, y // size))
        return Position(row=row, col=col)

    def _on_click(self, event: tk.Event) -> None:
        self._drag_anchor = self._pixel_to_cell(event.x, event.y)
        # Snapshot the active tool now -- the gesture this press might
        # start is governed by whichever tool was active at press time,
        # even if the user switches tools before releasing.
        self._drag_tool = self._capture_tool()

        # If a zone tool is active, arm the anchor for click-click gesture.
        # The anchor is armed on first click (press), and the live outline
        # follows the mouse via _on_motion. A second click commits the zone.
        # Only arm if no anchor is already armed (first click of the gesture).
        if (
            self._drag_tool in (BuilderTool.DESTROY_ZONE, BuilderTool.RESTORE_ZONE)
            and self._armed_anchor is None
        ):
            self._armed_anchor = self._drag_anchor
            self._armed_tool = self._drag_tool
            self._anchor_just_armed = True
            # Draw initial outline at the anchor cell (zero-size rectangle).
            self._draw_zone_outline(self._armed_anchor, self._armed_anchor)
            # Bind motion to update outline during click-click gesture (button released).
            self.bind("<Motion>", self._on_motion)

        # Wall hit-testing only matters under the Break tool: marker tools
        # place via `_on_release`'s same-cell click, so a wall hit under
        # them is wasted work.
        if self._drag_tool is not BuilderTool.BREAK:
            return
        hit = self.find_closest(event.x, event.y, halo=_CLICK_HALO)
        if not hit:
            return
        wall = self._item_walls.get(hit[0])
        if wall is None:
            # Closest item was the cursor rectangle, not a wall bar/gap.
            return
        self._on_wall_clicked(wall)

    def _on_motion(self, event: tk.Event) -> None:
        """Update the live zone outline during drag or click-click gesture."""
        if self._armed_anchor is None or self._armed_tool is None:
            return
        end = self._pixel_to_cell(event.x, event.y)
        self._draw_zone_outline(self._armed_anchor, end)

    def _draw_zone_outline(self, anchor: Position, end: Position) -> None:
        """Draw or update the live colored rectangle outline for zone selection."""
        colors = colors_for(self._theme)
        # Distinct color per tool: destroy=accent (blue), restore=entry (green)
        if self._armed_tool is BuilderTool.DESTROY_ZONE:
            outline_color = colors.accent
        else:
            outline_color = colors.entry
        x0, y0 = self._cell_bounds(anchor)[:2]
        x1, y1 = self._cell_bounds(end)[2:]
        # Normalize so top-left is always (min_x, min_y)
        x0, x1 = sorted((x0, x1))
        y0, y1 = sorted((y0, y1))
        if self._zone_outline_id is not None:
            self.coords(self._zone_outline_id, x0, y0, x1, y1)
        else:
            self._zone_outline_id = self.create_rectangle(
                x0,
                y0,
                x1,
                y1,
                outline=outline_color,
                width=2,
                dash=(4, 4),
                tags=("zone-outline",),
            )

    def _clear_zone_outline(self) -> None:
        """Remove the live zone outline and reset armed anchor state."""
        if self._zone_outline_id is not None:
            self.delete(self._zone_outline_id)
            self._zone_outline_id = None
        self._armed_anchor = None
        self._armed_tool = None
        self._anchor_just_armed = False
        # Unbind motion when anchor is cleared.
        self.unbind("<Motion>")

    def _cancel_drag(self) -> None:
        """Cancel an ongoing drag operation (e.g., on Escape key).

        Clears the drag anchor/tool and the zone outline, so that
        releasing the mouse button does not apply the zone operation.
        """
        self._drag_anchor = None
        self._drag_tool = None
        self._clear_zone_outline()

    def _on_release(self, event: tk.Event) -> None:
        # The click-vs-drag split is decided purely by comparing the press
        # cell to the release cell -- a release on the same cell as the
        # press is never a zone operation, with no separate pixel-distance
        # threshold (Story 3.3's Boundaries).
        if self._drag_anchor is None:
            return
        anchor = self._drag_anchor
        tool = self._drag_tool
        end = self._pixel_to_cell(event.x, event.y)
        # Consumed: reset both before dispatching so a stray/duplicate
        # <ButtonRelease-1> with no intervening <Button-1> can never replay
        # a stale anchor/tool as a zone operation.
        self._drag_anchor = None
        self._drag_tool = None

        # Click-click gesture: if an anchor was armed (first click with zone
        # tool), check if this release commits the zone (different cell) or
        # is the first click's release (same cell -- keep anchor armed) or
        # a second click on the same cell (cancel gesture).
        if self._armed_anchor is not None and self._armed_tool is not None:
            if end != self._armed_anchor:
                # Second click on different cell: commit the zone
                self._on_zone_dragged(self._armed_tool, self._armed_anchor, end)
                self._clear_zone_outline()
            elif self._anchor_just_armed:
                # First click's release on same cell: keep anchor armed for
                # click-click gesture (outline follows mouse until second click)
                self._anchor_just_armed = False
            else:
                # Second click on same cell as armed anchor: cancel gesture
                self._clear_zone_outline()
            return

        if tool is None:
            return
        if end != anchor:
            # Zone drag: only a press-captured zone tool fires a zone
            # operation -- a Break/Pass-through/marker drag never is one
            # (`_on_zone_dragged`'s own gate is a defensive fallback).
            if tool in (BuilderTool.DESTROY_ZONE, BuilderTool.RESTORE_ZONE):
                self._on_zone_dragged(tool, anchor, end)
        elif tool is BuilderTool.SET_ENTRY or tool is BuilderTool.SET_EXIT:
            # Same-cell release under a press-captured marker tool = a
            # cell click (Story 3.4).
            self._on_cell_clicked(tool, end)
        elif end == anchor:
            # Same-cell click with no zone-drag and no marker tool active:
            # move editing cursor directly to the clicked cell (Story 3.5).
            self._on_cell_clicked(tool, end)

    def _cell_center(self, position: Position) -> tuple[int, int]:
        size = self._cell_size
        return (position.col * size + size // 2, position.row * size + size // 2)

    def _cell_bounds(self, position: Position) -> tuple[int, int, int, int]:
        size = self._cell_size
        x0, y0 = position.col * size, position.row * size
        return x0, y0, x0 + size, y0 + size

    def refresh_markers(
        self,
        entry: Position | None,
        exit: Position | None,
        ghost: Position | None,
    ) -> None:
        """Redraw the entry/exit markers and any Set Exit ghost preview.

        Destroys every tagged `marker`/`ghost-marker` item and redraws from
        scratch, so a stale marker at a previous position can never linger
        after a placement/undo/redefinition -- this is the single redraw
        seam `_BuilderEditArea._sync_markers` drives. Colors come from the
        active theme via `colors_for`; the ghost is dashed + `?`-glyphed
        and purely informational, never hit-testable as a wall or a marker.
        """
        colors = colors_for(self._theme)
        self.delete("marker", "ghost-marker")
        if entry is not None:
            self._draw_entry_marker(entry, colors)
        if exit is not None:
            self._draw_exit_marker(exit, colors)
        if ghost is not None:
            self._draw_ghost(ghost, colors)

    def _draw_entry_marker(self, position: Position, colors: ColorTokens) -> None:
        # Filled square (entry = square, exit = diamond, builder/player = circle),
        # radius `_marker_radius`.
        cx, cy = self._cell_center(position)
        r = self._marker_radius
        self.create_rectangle(
            cx - r,
            cy - r,
            cx + r,
            cy + r,
            outline=colors.entry,
            fill=colors.entry,
            tags=("marker",),
        )

    def _draw_exit_marker(self, position: Position, colors: ColorTokens) -> None:
        # Filled diamond (see `_draw_entry_marker` for the shape/color split).
        cx, cy = self._cell_center(position)
        r = self._marker_radius
        self.create_polygon(
            cx,
            cy - r,
            cx + r,
            cy,
            cx,
            cy + r,
            cx - r,
            cy,
            outline=colors.exit,
            fill=colors.exit,
            tags=("marker",),
        )

    def _draw_ghost(self, position: Position, colors: ColorTokens) -> None:
        # Dashed outline + `?` glyph at the cursor cell, `colors.ghost`,
        # non-interactive (tags `ghost-marker` only -- never hit-testable).
        # The inset and glyph size scale with the cell size so the preview
        # stays inside the smallest cells (Story 3.4's marker geometry).
        x0, y0, x1, y1 = self._cell_bounds(position)
        inset = max(2, int(self._cell_size * _GHOST_INSET_SCALE))
        self.create_rectangle(
            x0 + inset,
            y0 + inset,
            x1 - inset,
            y1 - inset,
            outline=colors.ghost,
            dash=(3, 3),
            width=_WALL_WIDTH,
            tags=("ghost-marker",),
        )
        cx, cy = self._cell_center(position)
        self.create_text(
            cx,
            cy,
            text="?",
            fill=colors.ghost,
            font=self._ghost_font,
            tags=("ghost-marker",),
        )
