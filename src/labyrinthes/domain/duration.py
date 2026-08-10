"""Duration value object — shared by the Timer and Personal Records."""

from dataclasses import dataclass

from labyrinthes.domain.errors import DomainValidationError

_MILLISECONDS_PER_SECOND = 1000
_SECONDS_PER_MINUTE = 60


@dataclass(frozen=True)
class Duration:
    """A span of time in milliseconds. Never negative."""

    milliseconds: int

    def __post_init__(self) -> None:
        if self.milliseconds < 0:
            raise DomainValidationError(
                f"Duration.milliseconds must be >= 0, got {self.milliseconds}"
            )

    def to_clock_string(self) -> str:
        """`"MM:SS"`, total minutes uncapped.

        Deliberately does not reproduce the legacy `Chrono` class's bug of
        wrapping minutes back to `00` past 60 -- a run over an hour long
        prints e.g. `"75:03"`, not `"15:03"`.
        """
        total_seconds = self.milliseconds // _MILLISECONDS_PER_SECOND
        minutes, seconds = divmod(total_seconds, _SECONDS_PER_MINUTE)
        return f"{minutes:02d}:{seconds:02d}"
