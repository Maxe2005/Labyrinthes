"""Duration value object — shared by the Timer and Personal Records."""

from dataclasses import dataclass

from labyrinthes.domain.errors import DomainValidationError


@dataclass(frozen=True)
class Duration:
    """A span of time in milliseconds. Never negative."""

    milliseconds: int

    def __post_init__(self) -> None:
        if self.milliseconds < 0:
            raise DomainValidationError(
                f"Duration.milliseconds must be >= 0, got {self.milliseconds}"
            )
