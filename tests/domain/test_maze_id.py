import dataclasses

import pytest

from labyrinthes.domain.maze_id import MazeId


def test_maze_id_holds_opaque_value():
    maze_id = MazeId(value="abc-123")

    assert maze_id.value == "abc-123"


def test_maze_id_is_immutable():
    maze_id = MazeId(value="abc-123")

    with pytest.raises(dataclasses.FrozenInstanceError):
        maze_id.value = "other"
