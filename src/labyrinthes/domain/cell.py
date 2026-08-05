"""Cell value object — a single grid square, encoded as one digit.

The encoding is a preserved public contract (AD-6): `"0"`/`"1"`/`"2"`/`"3"`,
bit 1 = top wall, bit 2 = left wall. This is what Story 1.4's
`MazeRepository` reads/writes byte-for-byte compatible with existing
`.csv` maze files — do not reinterpret or re-encode it.

`has_right_wall`/`has_bottom_wall` are deliberately not exposed here:
those aren't encoded on the cell itself in the legacy scheme, only via a
neighboring cell's top/left bit — a `Grid`-level concern.
"""

from dataclasses import dataclass

from labyrinthes.domain.errors import DomainValidationError

_VALID_VALUES = ("0", "1", "2", "3")


@dataclass(frozen=True)
class Cell:
    """A grid square encoded as one digit `"0"`–`"3"`.

    Encodage binaire des murs :
    - Bit 0 (poids 1) : Mur du haut
    - Bit 1 (poids 2) : Mur de gauche

    Valeurs :
    - 0 ("00") : Aucun mur
    - 1 ("01") : Mur haut uniquement
    - 2 ("10") : Mur gauche uniquement
    - 3 ("11") : Murs haut et gauche
    """

    value: str

    def __post_init__(self) -> None:
        if self.value not in _VALID_VALUES:
            raise DomainValidationError(
                f"Cell.value must be one of {_VALID_VALUES}, got {self.value!r}"
            )

    @property
    def has_top_wall(self) -> bool:
        # Masquage binaire : extrait le bit 0 (valeur 1) qui représente le mur du haut.
        return bool(int(self.value) & 1)

    @property
    def has_left_wall(self) -> bool:
        # Masquage binaire : extrait le bit 1 (valeur 2) qui représente le mur de gauche.
        return bool(int(self.value) & 2)
