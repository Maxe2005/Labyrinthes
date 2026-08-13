from labyrinthes.domain.duration import Duration
from labyrinthes.domain.movement_speed import MovementSpeed, cell_crossing_duration


def test_normal_is_the_legacy_default_invariant():
    # `vitesse deplacement (45) x decoupe du deplacement (5)` == 225ms per
    # cell -- the legacy default a fresh install must reproduce.
    assert cell_crossing_duration(MovementSpeed.NORMAL) == Duration(milliseconds=225)


def test_every_member_has_a_mapping():
    assert cell_crossing_duration(MovementSpeed.SLOW) == Duration(milliseconds=375)
    assert cell_crossing_duration(MovementSpeed.FAST) == Duration(milliseconds=150)


def test_all_durations_are_non_negative():
    for speed in MovementSpeed:
        assert cell_crossing_duration(speed).milliseconds >= 0


def test_exactly_three_speeds():
    assert set(MovementSpeed) == {MovementSpeed.SLOW, MovementSpeed.NORMAL, MovementSpeed.FAST}
