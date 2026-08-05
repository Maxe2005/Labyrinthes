import dataclasses

import pytest

from labyrinthes.domain.cell import Cell
from labyrinthes.domain.errors import DomainValidationError
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.position import Position


def test_filled_produces_padded_raw_size_with_playable_width_height():
    grid = Grid.filled(width=4, height=3)

    assert grid.width == 4
    assert grid.height == 3
    assert len(grid.cells) == 4  # height + 1
    assert all(len(row) == 5 for row in grid.cells)  # width + 1


def test_filled_real_cells_are_fully_walled():
    grid = Grid.filled(width=4, height=3)

    for row in range(3):
        for col in range(4):
            assert grid.cells[row][col].value == "3"


def test_filled_padding_column_is_left_wall_only():
    grid = Grid.filled(width=4, height=3)

    for row in range(3):
        assert grid.cells[row][4].value == "2"


def test_filled_padding_row_is_top_wall_only():
    grid = Grid.filled(width=4, height=3)

    for col in range(4):
        assert grid.cells[3][col].value == "1"


def test_filled_corner_cell_has_no_walls():
    grid = Grid.filled(width=4, height=3)

    assert grid.cells[3][4].value == "0"


@pytest.mark.parametrize(("width", "height"), [(0, 5), (5, 0), (-1, 5), (5, -1)])
def test_filled_rejects_non_positive_dimensions(width, height):
    with pytest.raises(DomainValidationError):
        Grid.filled(width=width, height=height)


def test_filled_smallest_legal_size():
    grid = Grid.filled(width=1, height=1)

    assert grid.width == 1
    assert grid.height == 1
    assert len(grid.cells) == 2  # height + 1
    assert all(len(row) == 2 for row in grid.cells)  # width + 1
    assert grid.cells[0][0].value == "3"  # the one real cell is fully walled
    assert grid.cells[0][1].value == "2"  # padding column
    assert grid.cells[1][0].value == "1"  # padding row
    assert grid.cells[1][1].value == "0"  # corner


def test_cell_at_returns_cell_for_valid_position():
    grid = Grid.filled(width=4, height=3)

    cell = grid.cell_at(Position(row=0, col=0))

    assert cell.value == "3"


@pytest.mark.parametrize("position", [Position(row=-1, col=0), Position(row=0, col=99)])
def test_cell_at_rejects_out_of_range_position(position):
    grid = Grid.filled(width=4, height=3)

    with pytest.raises(DomainValidationError):
        grid.cell_at(position)


def test_grid_is_immutable():
    grid = Grid.filled(width=4, height=3)

    with pytest.raises(dataclasses.FrozenInstanceError):
        grid.cells = ()


def test_cell_at_returns_padding_cell_at_raw_edge_indices():
    grid = Grid.filled(width=4, height=3)

    assert grid.cell_at(Position(row=grid.height, col=0)).value == "1"
    assert grid.cell_at(Position(row=0, col=grid.width)).value == "2"


def test_direct_construction_rejects_empty_cells():
    with pytest.raises(DomainValidationError):
        Grid(cells=())


def test_direct_construction_rejects_empty_rows():
    with pytest.raises(DomainValidationError):
        Grid(cells=((),))


def test_direct_construction_rejects_ragged_rows():
    with pytest.raises(DomainValidationError):
        Grid(cells=((Cell("0"), Cell("0")), (Cell("0"),)))
