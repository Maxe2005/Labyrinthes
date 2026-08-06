"""Maze CSV serialization -- the one shared routine AD-6 requires every
reader/writer (including Epic 4's migration script) to reuse.

File shape, one line each in this fixed order:

    1. entry line: `"col,row"`
    2. exit line: `"col,row"`
    3. (present only when `kind` is `CLASSIC`/`SAVED_RANDOM`) a `MazeId`
       line: the raw id value, nothing else
    4. one comma-separated grid row per remaining line, raw indices --
       including the closed-border padding row/column (see `Grid`'s module
       docstring) -- each value a single `"0"`-`"3"` `Cell` digit

Entry/exit lines are `col,row` order, not `row,col` -- verified against the
legacy reader (`Laby_grille.ouvrir_lab`: `Position(row=int(tab[1]),
col=int(tab[0]))`). Getting this backwards silently transposes every
entry/exit on load.

Whether a `MazeId` line is present is a pure function of the `kind` the
caller already knows (from `load(name, kind)`'s parameter, or the directory
being scanned in `find_by_id`) -- never sniffed from the file's content.
"""

import csv
from pathlib import Path

from labyrinthes.domain.cell import Cell
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.maze_id import MazeId
from labyrinthes.domain.position import Position

_ID_ELIGIBLE_KINDS = frozenset({MazeKind.CLASSIC, MazeKind.SAVED_RANDOM})


def read_maze_csv(path: Path, kind: MazeKind) -> Maze:
    """Read `path` into a `Maze` of `kind`.

    `kind` decides whether line 3 is a `MazeId` line or the first grid row --
    never sniffed from the content itself.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    entry_col, entry_row = (int(value) for value in lines[0].split(","))
    exit_col, exit_row = (int(value) for value in lines[1].split(","))

    remaining = lines[2:]
    maze_id: MazeId | None = None
    if kind in _ID_ELIGIBLE_KINDS:
        maze_id = MazeId(value=remaining[0])
        remaining = remaining[1:]

    cells = tuple(tuple(Cell(value) for value in row.split(",")) for row in remaining)

    return Maze(
        grid=Grid(cells=cells),
        entry=Position(row=entry_row, col=entry_col),
        exit=Position(row=exit_row, col=exit_col),
        kind=kind,
        id=maze_id,
    )


def write_maze_csv(path: Path, maze: Maze) -> None:
    """Write `maze` to `path`, matching `read_maze_csv`'s line shape exactly.

    Creates `path`'s parent directory if it doesn't exist yet. Uses
    `newline=""` plus `csv.writer(..., lineterminator="\\n")` so line endings
    match the legacy writer's behavior regardless of platform.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow([maze.entry.col, maze.entry.row])
        writer.writerow([maze.exit.col, maze.exit.row])
        if maze.kind in _ID_ELIGIBLE_KINDS and maze.id is not None:
            writer.writerow([maze.id.value])
        for row in maze.grid.cells:
            writer.writerow([cell.value for cell in row])
