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


def test_to_clock_string_at_zero():
    assert Duration(milliseconds=0).to_clock_string() == "00:00"


def test_to_clock_string_sub_minute_rounds_down_to_the_second():
    assert Duration(milliseconds=42_999).to_clock_string() == "00:42"


def test_to_clock_string_exact_minute():
    assert Duration(milliseconds=60_000).to_clock_string() == "01:00"


def test_to_clock_string_minutes_and_seconds():
    assert Duration(milliseconds=125_000).to_clock_string() == "02:05"


def test_to_clock_string_uncapped_past_sixty_minutes():
    # Deliberately not reproducing the legacy `Chrono` bug of wrapping
    # minutes back to 00 past 60.
    assert Duration(milliseconds=75 * 60_000 + 3_000).to_clock_string() == "75:03"
