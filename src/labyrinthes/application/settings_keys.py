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
TIME_LIMIT_SECONDS = "time_limit_seconds"
THEME_LOGO = "theme_logo"
CONFIRM_SWITCH_MAZE = "confirm_switch_maze"
CONFIRM_RESTART = "confirm_restart"
CONFIRM_LEVEL_CHANGE = "confirm_level_change"
CONFIRM_INVALID_INPUT = "confirm_invalid_input"
CONFIRM_REDEFINE_MARKER = "confirm_redefine_marker"
BUILDER_DEFAULT_TOOL = "builder_default_tool"
NEW_MAZE_DEFAULT_COLUMNS = "new_maze_default_columns"
NEW_MAZE_DEFAULT_ROWS = "new_maze_default_rows"
RANDOM_MAZE_DEFAULT_COLUMNS = "random_maze_default_columns"
RANDOM_MAZE_DEFAULT_ROWS = "random_maze_default_rows"
WINDOW_WIDTH = "window_width"
WINDOW_HEIGHT = "window_height"
