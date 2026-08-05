import dataclasses

import pytest

from labyrinthes.domain.position import Position


def test_position_holds_row_and_col():
    position = Position(row=2, col=5)

    assert position.row == 2
    assert position.col == 5


def test_position_is_immutable():
    position = Position(row=0, col=0)

    with pytest.raises(dataclasses.FrozenInstanceError):
        position.row = 1
