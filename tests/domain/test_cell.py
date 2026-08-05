import dataclasses

import pytest

from labyrinthes.domain.cell import Cell
from labyrinthes.domain.errors import DomainValidationError


@pytest.mark.parametrize(
    ("value", "has_top_wall", "has_left_wall"),
    [
        ("0", False, False),
        ("1", True, False),
        ("2", False, True),
        ("3", True, True),
    ],
)
def test_cell_wall_booleans_derived_from_digit(value, has_top_wall, has_left_wall):
    cell = Cell(value=value)

    assert cell.has_top_wall is has_top_wall
    assert cell.has_left_wall is has_left_wall


@pytest.mark.parametrize("value", ["4", "x", "", "00", "-1"])
def test_cell_rejects_invalid_value(value):
    with pytest.raises(DomainValidationError):
        Cell(value=value)


def test_cell_is_immutable():
    cell = Cell(value="0")

    with pytest.raises(dataclasses.FrozenInstanceError):
        cell.value = "1"
