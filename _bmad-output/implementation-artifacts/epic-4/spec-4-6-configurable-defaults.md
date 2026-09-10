---
baseline_commit: 9cf8c97
---
# Story 4.6: Configurable defaults — Builder tool, new-maze & random dimensions

Status: done

## Story

As the project's author,
I want the default Builder tool, the default new-maze dimensions, and the default random-maze dimensions to be configurable in Settings,
So that the dialogs and session start match my habits without editing values each time.

## Acceptance Criteria

1. **Given** the Settings window, **when** opened, **then** a Defaults section offers the default Builder tool and the default dimensions (new-maze and random), each persisting via the scoped `SettingsRepository`.

2. **Given** the Builder New Maze dialog, **when** opened, **then** its dimension fields default to the configured values, clamped within the shared 3–50 / 3–35 bounds, falling back to the bounds' minimum when unset.

3. **Given** the Player Generate Random dialog, **when** opened, **then** its dimension fields default to the configured values, with the same clamping and fallback.

4. **Given** a Builder session starting, **when** it opens, **then** the configured default tool is active (fallback: Break), read in the adapter and passed into the session service — the application layer gains no settings dependency.

## Tasks & Acceptance

**Execution:**
- [ ] `src/labyrinthes/application/settings_keys.py` -- add new setting keys: `BUILDER_DEFAULT_TOOL`, `NEW_MAZE_DEFAULT_COLUMNS`, `NEW_MAZE_DEFAULT_ROWS`, `RANDOM_MAZE_DEFAULT_COLUMNS`, `RANDOM_MAZE_DEFAULT_ROWS`
- [ ] `src/labyrinthes/application/defaults_settings.py` (new file) -- add scoped readers/writers for the five new settings with independent fallback and clamping; builder scope for tool and new-maze defaults, game scope for random-maze defaults
- [ ] `src/labyrinthes/adapters/tkinter/common/settings_window.py` -- add "Defaults" category with controls for default Builder tool (dropdown) and four dimension fields (Entries with inline validation)
- [ ] `src/labyrinthes/adapters/tkinter/common/new_maze_dialog.py` -- read default columns/rows from `defaults_settings` at construction time, use as initial values (clamped to bounds)
- [ ] `src/labyrinthes/adapters/tkinter/player/generate_random_dialog.py` -- read default columns/rows from `defaults_settings` at construction time, use as initial values (clamped to bounds)
- [ ] `src/labyrinthes/application/builder_session.py` -- add optional `default_tool` parameter to `start_builder_session`, defaulting to `BuilderTool.BREAK`
- [ ] `src/labyrinthes/adapters/tkinter/builder/screen.py` -- read default tool from `defaults_settings` when `state is None`, pass to `start_builder_session` via the navigate lambda
- [ ] `src/labyrinthes/adapters/tkinter/builder/edit_area.py` -- no change needed (receives session with correct initial tool)

**Acceptance Criteria:**
- Given the Settings window, when opened, then a Defaults section offers the default Builder tool and the default dimensions (new-maze and random), each persisting via the scoped `SettingsRepository`
- Given the Builder New Maze dialog, when opened, then its dimension fields default to the configured values, clamped within the shared 3–50 / 3–35 bounds, falling back to the bounds' minimum when unset
- Given the Player Generate Random dialog, when opened, then its dimension fields default to the configured values, with the same clamping and fallback
- Given a Builder session starting, when it opens, then the configured default tool is active (fallback: Break), read in the adapter and passed into the session service — the application layer gains no settings dependency

## Code Map

- `src/labyrinthes/application/settings_keys.py` -- central key names; add 5 new constants
- `src/labyrinthes/application/defaults_settings.py` (new) -- scoped readers/writers for defaults; follows `confirmation_settings.py` pattern
- `src/labyrinthes/application/builder_session.py` -- `start_builder_session` gains optional `default_tool` parameter
- `src/labyrinthes/adapters/tkinter/common/settings_window.py` -- add "Defaults" category with dropdown + 4 entry fields
- `src/labyrinthes/adapters/tkinter/common/new_maze_dialog.py` -- read defaults at construction, use as initial values
- `src/labyrinthes/adapters/tkinter/player/generate_random_dialog.py` -- read defaults at construction, use as initial values
- `src/labyrinthes/adapters/tkinter/builder/screen.py` -- read default tool when opening NewMazeDialog, pass to session start
- `src/labyrinthes/domain/maze_size_bounds.py` -- `DEFAULT_MAZE_SIZE_BOUNDS` provides clamp bounds (3-50, 3-35)
- `src/labyrinthes/application/maze_size_bounds.py` -- `read_maze_size_bounds` provides bounds for clamping

## Spec Change Log

## Design Notes

### Settings scoping and keys

Per the epic context (Technical Decisions): "New settings follow AD-7 (scoped keys, single readers): `game` scope for random defaults, `builder` scope for Builder defaults, plus a 'Defaults' category in the shared `SettingsWindow`."

Five new keys:
- `BUILDER_DEFAULT_TOOL` (builder scope, enum string: "break" | "pass-through" | "destroy-zone" | "restore-zone" | "set-entry" | "set-exit")
- `NEW_MAZE_DEFAULT_COLUMNS` (builder scope, int)
- `NEW_MAZE_DEFAULT_ROWS` (builder scope, int)
- `RANDOM_MAZE_DEFAULT_COLUMNS` (game scope, int)
- `RANDOM_MAZE_DEFAULT_ROWS` (game scope, int)

### Clamping and fallback logic

The `defaults_settings` readers follow the pattern from `read_maze_size_bounds`:
- Each field independently falls back on `SettingNotFoundError`/`SettingCorruptError`/`ValueError`/`TypeError`
- Non-positive stored values are rejected (fall back to default)
- Values are clamped to `DEFAULT_MAZE_SIZE_BOUNDS` (3–50 columns, 3–35 rows)
- The fallback for unset is the bounds' minimum (3), not a hardcoded value

### Builder tool default

The default tool is an adapter-side concern (epic context): "The default Builder tool is an adapter-side concern: read the setting in `builder/screen.py`, pass it into `start_builder_session(...)` — the application layer gains no settings dependency."

`start_builder_session` gains an optional `default_tool: BuilderTool = BuilderTool.BREAK` parameter. The builder screen reads the setting and passes it when navigating from the New Maze dialog confirmation.

### Settings window "Defaults" category

Adds a third category to `_CATEGORIES` ("Appearance", "Confirmation", "Defaults"). The content pane includes:
- Dropdown (`tk.OptionMenu` or `ttk.Combobox`) for default Builder tool, populated from `BuilderTool` enum values
- Four `tk.Entry` fields for dimensions, with inline validation mirroring `NewMazeDialog`/`GenerateRandomDialog`
- Per-field validation on `<KeyRelease>` showing errors inline (typography.body_secondary/colors.exit)
- Persist on change via the writer functions

### Dialog initial values

Both dialogs read defaults at construction time (not at module load):
- `NewMazeDialog`: calls `read_new_maze_defaults(settings_repository)` -> `(columns, rows)`
- `GenerateRandomDialog`: calls `read_random_maze_defaults(settings_repository)` -> `(columns, rows)`
- These are used as initial `Entry` text instead of the bounds' minimums

## Verification

**Commands:**
- `ruff check .` -- expected: all checks pass
- `ruff format --check .` -- expected: all files formatted
- `pytest -q` -- expected: all tests pass

**Manual checks:**
- Open Settings window -> verify "Defaults" category exists and is selectable
- In Defaults category: change default tool, verify it persists after reopening Settings
- In Defaults category: change default dimensions, verify they persist and are clamped to 3-50/3-35
- Open Builder -> New Maze dialog -> verify columns/rows show configured defaults
- Open Player -> Generate Random dialog -> verify columns/rows show configured defaults
- Start Builder session -> verify the configured default tool is active (highlighted in tool sidebar)
- Restart app -> verify all configured defaults persist