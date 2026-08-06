# Deferred Work

## Deferred from: code review of 1-1-domain-model-foundation (2026-08-05)

- `Grid.filled` has no type validation; a non-`int` width/height raises a raw `TypeError` instead of `DomainValidationError` [src/labyrinthes/domain/grid.py:54] — deferred, pre-existing pattern across the whole diff (no value object in this story validates argument *types*, only business-domain invariants; consistent with the codebase having no static type-checker configured yet).
- `MazeId` performs zero validation — an empty/whitespace string is accepted as a valid opaque id [src/labyrinthes/domain/maze_id.py:11] — deferred, the story explicitly scopes `MazeId` to "an opaque identifier only, no minting scheme here"; a validation rule is better decided alongside Story 1.4's minting function.

## Deferred from: code review of spec-1-2-automated-domain-ui-boundary-test (2026-08-06)

- `TYPE_CHECKING`-guarded imports are not excluded from the AST scan and would false-positive once `domain/`/`application/` first use type-only imports [tests/test_architecture_boundaries.py] — deferred, pre-existing scope boundary; revisit when a story first needs a `TYPE_CHECKING` import in `domain/`/`application/`.
- Minor untested/low-probability edge branches in the scanner: bare `from . import x` (logic re-read, correct), a relative import climbing above the top-level package (Python itself would crash on this at runtime), a directory shadowed by a same-named file [tests/test_architecture_boundaries.py] — deferred, no reachable consequence today.
- `_format_violations` reports no line number, only file + module [tests/test_architecture_boundaries.py:117] — deferred, optional debuggability improvement, not required by any AC.
- A future `adapters/tkinter/__init__.py` barrel re-export would bypass the screen-isolation check [tests/test_architecture_boundaries.py] — deferred, speculative/forward-looking, no such file exists yet.

## Deferred from: code review of spec-1-4-concrete-mazerepository-single-shared-csv-read-write-implementation (2026-08-06)

- source_spec: `_bmad-output/implementation-artifacts/spec-1-4-concrete-mazerepository-single-shared-csv-read-write-implementation.md`
  summary: `write_maze_csv` (`src/labyrinthes/adapters/storage/csv_maze_format.py`) truncates and writes in place, not atomically (no temp-file-plus-rename) — a crash or interruption mid-write can leave a corrupted or empty maze file, destroying whatever was previously saved under that name.
  evidence: confirmed by direct inspection — `write_maze_csv` opens `path` in `"w"` mode (immediate truncation) and writes rows incrementally via `csv.writer`; there is no atomic-replace fallback. Mirrors the legacy app's own non-atomic `save_as`/`save_param_defaut` writes, so it is not a regression, but the rewrite has no NFR yet committing to fixing it either.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-4-concrete-mazerepository-single-shared-csv-read-write-implementation.md`
  summary: `read_maze_csv` (`src/labyrinthes/adapters/storage/csv_maze_format.py`) raises raw `IndexError`/`ValueError` on a truncated, too-short, or non-numeric-header maze CSV instead of a typed `LabyrinthesError` subclass.
  evidence: confirmed by direct inspection — `lines[0].split(",")`/`lines[1].split(",")`/`remaining[0]` index unconditionally with no length check, and `int(value)` has no `try`/`except`. Out of this story's declared minimal/mechanical scope (mirrors Story 1.3's `RecordsRepository`-style restraint); best paired with a future format-validation or Epic 4 migration-hardening pass, where corrupt/legacy-edge-case files are already a live concern.

## Deferred from: code review of spec-1-5-concrete-settingsrepository-scoped-persistence (2026-08-06)

- source_spec: `_bmad-output/implementation-artifacts/spec-1-5-concrete-settingsrepository-scoped-persistence.md`
  summary: `write_setting_value` (`src/labyrinthes/adapters/storage/settings_format.py`) truncates and writes in place, not atomically (no temp-file-plus-rename) — a crash mid-write, or a concurrent `get()` from another `JsonSettingsRepository` instance sharing the same root (the exact Builder/Game-running-at-once scenario this story targets), can observe a corrupted or empty setting file.
  evidence: confirmed by direct inspection — `write_setting_value` opens `path` in `"w"` mode (immediate truncation) and writes via `json.dump` with no atomic-replace fallback. Mirrors `write_maze_csv`'s (Story 1.4) identical, already-deferred gap — not a new regression, but the rewrite has no NFR yet committing to fixing it for either writer.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-5-concrete-settingsrepository-scoped-persistence.md`
  summary: `JsonSettingsRepository.get()`/`read_setting_value` raise raw `json.JSONDecodeError`/`FileNotFoundError` rather than a typed `LabyrinthesError` subclass when a setting file is malformed, corrupted, or removed/replaced between the `path.is_file()` check and the read (a TOCTOU gap).
  evidence: confirmed by direct inspection — `read_setting_value` calls `json.load(handle)` with no `try`/`except`, and `JsonSettingsRepository.get()`'s `is_file()` check and the subsequent read are two separate, non-atomic steps. Mirrors `read_maze_csv`'s (Story 1.4) identical, already-deferred finding for malformed CSV content; out of this story's declared minimal/mechanical scope, best paired with a future format-validation or hardening pass.

## Deferred from: code review of spec-1-6-design-token-system-shared-tkinter-widget-primitives (2026-08-06)

- source_spec: `_bmad-output/implementation-artifacts/spec-1-6-design-token-system-shared-tkinter-widget-primitives.md`
  summary: `FontSpec.to_tk_font()` (`src/labyrinthes/adapters/tkinter/common/tokens.py`) calls `int(self.weight)` unconditionally, so a `FontSpec` built with a non-numeric `weight` string raises `ValueError` instead of degrading to a valid Tk `"normal"`/`"bold"` weight.
  evidence: confirmed by direct inspection — no `try`/`except` around the `int()` call. Not reachable today: all 7 `TYPOGRAPHY` entries this story defines use numeric-string weights (`"400"`/`"600"`/`"700"`); becomes live risk only if a future caller constructs its own `FontSpec` with a non-numeric weight.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-6-design-token-system-shared-tkinter-widget-primitives.md`
  summary: `SPACING`/`RADII` (`src/labyrinthes/adapters/tkinter/common/tokens.py`) are plain mutable module-level `dict`s with no `MappingProxyType`/frozen guard, so one importer mutating a key (e.g. `SPACING["xs"] = 999`) silently changes spacing/radii for every other module sharing the same imported dict.
  evidence: confirmed by direct inspection — both are declared as ordinary `dict[str, ...]` literals, unlike `ColorTokens`/`FontSpec`, which are frozen dataclasses. No AC in this story commits to immutability for these two token categories.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-6-design-token-system-shared-tkinter-widget-primitives.md`
  summary: `ToolButtonGroup.activate()` (`src/labyrinthes/adapters/tkinter/common/tool_btn.py`) called with a `ToolButton` that was never registered in that group silently deactivates every member instead of raising, leaving the group with zero active members and no error surfaced.
  evidence: confirmed by direct inspection — the loop iterates `self._buttons` and compares each `candidate is button` with no membership check on `button` itself. Only reachable via manual group/button wiring that bypasses `ToolButton.__init__`'s own `group.add(self)` auto-registration, which is the only construction path this story uses/tests.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-6-design-token-system-shared-tkinter-widget-primitives.md`
  summary: a grouped `ToolButton` that is `.destroy()`ed while still registered in its `ToolButtonGroup` (no `remove()`/unregister API exists) raises `_tkinter.TclError: bad window path name` out of the group's next `activate()` call, breaking every subsequent tool selection in that group, not just the destroyed button.
  evidence: confirmed by direct inspection — `activate()` calls `candidate._set_active_direct()` → `_apply_style()` → `self.configure(...)` on every registered member unconditionally, including a destroyed one. Not reachable today: no consuming screen exists yet (Stories 1.7+) to ever call `.destroy()` on a `ToolButton`.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-6-design-token-system-shared-tkinter-widget-primitives.md`
  summary: `Tooltip` (`src/labyrinthes/adapters/tkinter/common/tooltip.py`) only binds `<Enter>`/`<Leave>` on its anchor widget, with no `<Destroy>` handling -- if the anchor is destroyed while the popup is shown, without a preceding `<Leave>`, the popup `Toplevel` can be left referenced with no owning widget to trigger its normal hover-leave cleanup.
  evidence: confirmed by direct inspection — `_on_enter`/`_on_leave` are the only two bindings registered in `__init__`. Affects every primitive that attaches a `Tooltip` (`ToolButton`, `IconButton`); not reachable today since no consuming screen performs teardown yet.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-6-design-token-system-shared-tkinter-widget-primitives.md`
  summary: `HudChip(value=None)`/`HudChip.set_value(None)` (`src/labyrinthes/adapters/tkinter/common/hud_chip.py`) renders the literal text `"None"` instead of a placeholder, since `value: object` type-checks fine for `None` and `str(value)` is applied unconditionally.
  evidence: confirmed by direct inspection — no `None`/empty special-case before `str(value)`. Reachable only if a future caller passes an unset stat straight through rather than a placeholder string itself; no current call site in this story does so (no consuming screen exists yet).
