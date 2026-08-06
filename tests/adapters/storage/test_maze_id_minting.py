from labyrinthes.adapters.storage.maze_id_minting import mint_maze_id
from labyrinthes.domain.maze_id import MazeId


def test_mint_maze_id_returns_a_maze_id():
    maze_id = mint_maze_id()

    assert isinstance(maze_id, MazeId)


def test_mint_maze_id_returns_non_empty_values():
    maze_id = mint_maze_id()

    assert maze_id.value


def test_mint_maze_id_returns_distinct_values():
    minted = {mint_maze_id().value for _ in range(100)}

    assert len(minted) == 100
