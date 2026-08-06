from labyrinthes.adapters.storage.csv_maze_format import read_maze_csv, write_maze_csv
from labyrinthes.domain.cell import Cell
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.maze_id import MazeId
from labyrinthes.domain.position import Position

_LEGACY_SIMPLE_MAZE_CSV = (
    "0,0\n"
    "10,5\n"
    "3,1,1,1,1,1,1,3,1,3,1,2\n"
    "3,1,0,3,1,0,2,0,2,0,3,2\n"
    "2,1,1,2,1,3,1,1,1,2,0,2\n"
    "3,1,0,3,0,3,1,3,2,1,0,2\n"
    "2,1,2,0,1,0,2,2,1,0,1,2\n"
    "1,1,1,1,1,1,1,1,1,1,0,0\n"
)


def _grid() -> Grid:
    return Grid.filled(width=2, height=2)


def test_round_trip_classic_maze_with_id(tmp_path):
    maze = Maze(
        grid=_grid(),
        entry=Position(row=0, col=0),
        exit=Position(row=1, col=2),
        kind=MazeKind.CLASSIC,
        id=MazeId(value="abc123"),
    )
    path = tmp_path / "classic-maze.csv"

    write_maze_csv(path, maze)
    loaded = read_maze_csv(path, MazeKind.CLASSIC)

    assert loaded == maze


def test_written_classic_maze_carries_a_maze_id_line(tmp_path):
    maze = Maze(
        grid=_grid(),
        entry=Position(row=0, col=0),
        exit=Position(row=1, col=2),
        kind=MazeKind.CLASSIC,
        id=MazeId(value="abc123"),
    )
    path = tmp_path / "classic-maze.csv"

    write_maze_csv(path, maze)
    lines = path.read_text(encoding="utf-8").splitlines()

    assert lines[2] == "abc123"


def test_round_trip_sketch_maze_without_id(tmp_path):
    maze = Maze(
        grid=_grid(),
        entry=Position(row=0, col=0),
        exit=Position(row=1, col=2),
        kind=MazeKind.SKETCH,
        id=None,
    )
    path = tmp_path / "sketch-maze.csv"

    write_maze_csv(path, maze)
    loaded = read_maze_csv(path, MazeKind.SKETCH)

    assert loaded == maze


def test_written_sketch_maze_has_no_maze_id_line(tmp_path):
    maze = Maze(
        grid=_grid(),
        entry=Position(row=0, col=0),
        exit=Position(row=1, col=2),
        kind=MazeKind.SKETCH,
        id=None,
    )
    path = tmp_path / "sketch-maze.csv"

    write_maze_csv(path, maze)
    lines = path.read_text(encoding="utf-8").splitlines()

    # 2 header lines + one grid row per raw row (height + 1), no MazeId line.
    assert len(lines) == 2 + maze.grid.height + 1
    # Every remaining line is a comma-separated row of single-digit cell
    # values, not an id string.
    for row in lines[2:]:
        assert all(value in "0123" for value in row.split(","))


def test_reads_legacy_shaped_csv_without_maze_id_line(tmp_path):
    path = tmp_path / "legacy-simple-maze.csv"
    path.write_text(_LEGACY_SIMPLE_MAZE_CSV, encoding="utf-8")

    maze = read_maze_csv(path, MazeKind.SKETCH)

    assert maze.entry == Position(row=0, col=0)
    assert maze.exit == Position(row=5, col=10)
    assert maze.grid.width == 11
    assert maze.grid.height == 5
    assert maze.id is None
    assert maze.kind == MazeKind.SKETCH
    assert maze.grid.cells[0][0] == Cell("3")
    assert maze.grid.cells[5][11] == Cell("0")
    assert maze.grid.cells[2][0] == Cell("2")
    assert maze.grid.cells[4][10] == Cell("1")
