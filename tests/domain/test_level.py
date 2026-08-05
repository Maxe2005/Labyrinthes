from labyrinthes.domain.level import Level


def test_level_members_have_expected_values():
    assert Level.ONE == 1
    assert Level.TWO == 2
    assert Level.THREE == 3
    assert Level.FOUR == 4
    assert Level.MAX == 5


def test_level_ordering():
    assert Level.MAX > Level.FOUR > Level.THREE > Level.TWO > Level.ONE
