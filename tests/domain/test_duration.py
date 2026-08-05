import dataclasses

import pytest

from labyrinthes.domain.duration import Duration
from labyrinthes.domain.errors import DomainValidationError


def test_duration_holds_milliseconds():
    duration = Duration(milliseconds=1500)

    assert duration.milliseconds == 1500


def test_duration_rejects_negative_milliseconds():
    with pytest.raises(DomainValidationError):
        Duration(milliseconds=-1)


def test_duration_accepts_zero():
    assert Duration(milliseconds=0).milliseconds == 0


def test_duration_is_immutable():
    duration = Duration(milliseconds=0)

    with pytest.raises(dataclasses.FrozenInstanceError):
        duration.milliseconds = 5
