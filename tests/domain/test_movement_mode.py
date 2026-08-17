from labyrinthes.domain.movement_mode import MovementMode


def test_members_carry_the_persisted_string_values():
    assert MovementMode.DISCRETE.value == "discrete"
    assert MovementMode.SMOOTH.value == "smooth"


def test_exactly_two_modes_and_exhaustive_iteration():
    assert set(MovementMode) == {MovementMode.DISCRETE, MovementMode.SMOOTH}
