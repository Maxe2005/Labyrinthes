"""Logo options for the Player game screen (Story 2.11).

Provides `_LOGO_OPTIONS` — a tuple of `LogoOption(key, filename, label)` —
and `_logo_path(key)` to resolve a key to the on-disk image file path.
All 13 images come from the "parcoureur" set of the legacy Idées LOGO/
folder, renamed in English per the rewrite naming convention.
"""

from __future__ import annotations

_LOGO_OPTIONS: tuple[tuple[str, str, str], ...] = (
    ("logo-01", "logo-01.jpg", "logo-01"),
    ("default", "logo-02.jpg", "default"),
    ("insta", "logo-03.jpg", "insta"),
    ("logo-04", "logo-04.jpg", "logo-04"),
    ("water", "logo-05.jpg", "water"),
    ("logo-06", "logo-06.jpg", "logo-06"),
    ("logo-07", "logo-07.jpg", "logo-07"),
    ("logo-08", "logo-08.jpg", "logo-08"),
    ("logo-09", "logo-09.jpg", "logo-09"),
    ("logo-10", "logo-10.jpg", "logo-10"),
    ("logo-11", "logo-11.jpg", "logo-11"),
    ("logo-12", "logo-12.jpg", "logo-12"),
    ("logo-13", "logo-13.jpg", "logo-13"),
)

_LOGO_BY_KEY: dict[str, tuple[str, str]] = {
    key: (filename, label) for key, filename, label in _LOGO_OPTIONS
}


def _logo_path(key: str) -> str:
    """Return the on-disk path for *key*.

    The assets directory is co-located with the consumer code under
    ``src/labyrinthes/adapters/tkinter/player/assets/logos/``.
    """
    import os

    filename = _LOGO_BY_KEY[key][0]
    _DIR = os.path.join(
        os.path.dirname(__file__),
        "assets",
        "logos",
    )
    return os.path.join(_DIR, filename)