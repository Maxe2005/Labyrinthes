"""`GameplayScreen` package (Stories 2.4-2.10, 3.8) -- split by UI region:

- `screen.py` -- `GameplayScreen`, the session-orchestrating controller
  (construction wiring, movement/animation, tick/timeout, save flow).
- `hud.py` -- `_HudRow`, the Level/Difficulty/Time/Pos chip row + HARD
  status light.
- `sidebar.py` -- `_LeftPanel` (Mode/Levels/Difficulty/Edit-in-Builder) and
  `_RightPanel` (Movement + the conditional Save button's zone), flanking
  the centered `Stage` (Story 4.10).
- `banners.py` -- `_OutcomeBanner`, the shared win/timeout inline banner.

`hud.py`/`sidebar.py`/`banners.py` hold no session state of their own --
`GameplayScreen` owns `self._session` and pushes updates into them through
small setters after each session change.
"""

from labyrinthes.adapters.tkinter.player.gameplay.screen import GameplayScreen

__all__ = ["GameplayScreen"]
