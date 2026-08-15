"""Setting key names, one module every consumer imports.

Declaring names here once is what keeps Builder/Game/Home from drifting
into duplicate or typo'd key strings for the same setting. `shared`-scope
keys are read by both Builder and Game; `game`-scope keys belong to the
Player (game) application only. Only key *names* live here -- default values
are the individual readers'/writers' concern.
"""

MAZE_MIN_COLUMNS = "maze_min_columns"
MAZE_MAX_COLUMNS = "maze_max_columns"
MAZE_MIN_ROWS = "maze_min_rows"
MAZE_MAX_ROWS = "maze_max_rows"
THEME = "theme"
MOVEMENT_MODE = "movement_mode"
MOVEMENT_SPEED = "movement_speed"
HARD_MODE_READY_COLOR = "hard_mode_ready_color"
HARD_MODE_MOVING_COLOR = "hard_mode_moving_color"
TIMER_LIMIT_ENABLED = "timer_limit_enabled"
TIMER_LIMIT_SECONDS = "timer_limit_seconds"
