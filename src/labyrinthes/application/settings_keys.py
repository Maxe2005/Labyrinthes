"""`shared`-scope setting key names.

The one module every consumer imports instead of hardcoding key strings —
declaring names here once is what keeps Builder/Game/Home from drifting
into duplicate or typo'd key strings for the same setting.

Only key *names* live here — FR-4's actual default bound values are not
this story's concern.
"""

MAZE_MIN_COLUMNS = "maze_min_columns"
MAZE_MAX_COLUMNS = "maze_max_columns"
MAZE_MIN_ROWS = "maze_min_rows"
MAZE_MAX_ROWS = "maze_max_rows"
THEME = "theme"
