from labyrinthes.domain.difficulty import Difficulty


def test_difficulty_members_have_expected_values():
    assert Difficulty.ONE == 1
    assert Difficulty.TWO == 2
    assert Difficulty.THREE == 3


def test_difficulty_ordering():
    assert Difficulty.THREE > Difficulty.TWO > Difficulty.ONE
