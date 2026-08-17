---
title: 'Story 1.4: Concrete MazeRepository — single shared CSV read/write implementation'
type: 'feature'
created: '2026-08-06'
status: 'done'
review_loop_iteration: 0
followup_review_recommended: false
context: ['_bmad-output/implementation-artifacts/epic-1/epic-1-context.md']
warnings: [oversized]
baseline_revision: '02362f3707352555a5a6ea98deda35307ae6cd7b'
final_revision: '02787aee5a7d009d68725a229e425c5ce9fe195f'
---

<intent-contract>

## Intent

**Problem:** `MazeRepository` (Story 1.3) is an interface with no implementation — there is no `adapters/storage/` package yet, so nothing actually reads/writes the maze CSV format, and every future Builder/Player/Home story that persists a maze would otherwise have nothing to depend on.

**Approach:** Add `adapters/storage/` with one `CsvMazeRepository(MazeRepository)` implementing `save`/`load`/`find_by_id` against the legacy CSV shape (entry line, exit line, optional `MazeId` line, then grid rows), one folder per `MazeKind` under a single declared root, plus the shared `MazeId`-minting function and CSV read/write routines a future migration script (Epic 4) will reuse.

## Boundaries & Constraints

**Always:** Cell encoding and grid-row shape are copied byte-for-byte from what `Grid`/`Cell` already decode — never reinterpreted (AD-6). Entry/exit CSV lines are `col,row` order (verified against the legacy reader/writer: `Position(row=int(tab[1]), col=int(tab[0]))`), decoded into the shared `Position(row, col)` type. A `MazeId` line is present iff `kind` is `CLASSIC`/`SAVED_RANDOM` — determined from the `kind` parameter already known by the caller (`load(name, kind)`, or the directory being scanned in `find_by_id`), never sniffed from file content. `save()` mints a `MazeId` only when `maze.kind` is id-eligible and `maze.id is None`; an already-set id is carried forward unchanged (AD-3). Storage layout: one root directory (`DEFAULT_MAZES_ROOT = Path("mazes")`, overridable via `CsvMazeRepository.__init__`), one subfolder per `MazeKind` named after `kind.value` (already English: `classic`/`sketch`/`saved-random`/`generated`), one `<name>.csv` file per maze — this scheme lives in `adapters/storage/paths.py` as the single module Epic 4's migration script will later import (AD-8). All new code lives under `adapters/storage/`, importing only `domain/`/`application/` — never `adapters/tkinter/` (AD-1, enforced by the existing architecture-boundary test).

**Block If:** None identified — the format and id-minting rules are fully pinned by AD-3/AD-6/epics.md's ACs, and the new-layout folder scheme is this story's own greenfield decision (Epic 4 hasn't run yet, so nothing on disk depends on a different name).

**Never:** Do not touch the legacy top-level folders (`Labyrinthes_classiques/`, etc.) or write a dual-format/legacy read path — that's Epic 4's one-time migration script, out of scope here. Do not implement `list()`/browse (Story 1.3 already deferred this; still not needed by this story's ACs). Do not add duplicate-name prompting or a `GENERATED`→`SAVED_RANDOM` kind transition inside the repository — `MazeRepository.save()`'s own docstring (Story 1.3) already assigns both to the caller. Do not handle a Builder-style "entry/exit not yet set" sketch (legacy's `"off"` sentinel) — out of scope; domain `Maze` requires concrete `entry`/`exit`, and no AC in epics.md's Story 1.4 exercises this case (Epic 3's entry/exit-marking stories own how in-progress sketches represent that state, if at all).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Save a new `classic`/`saved-random` maze (`id=None`) | `save(maze, "foo")` | Returns a `Maze` with a freshly minted `MazeId`; file has entry/exit/id/grid lines | No error |
| Re-save a maze that already has an id | `save(maze_with_id, "foo")` | Existing id written unchanged, not re-minted | No error |
| Save a `sketch`/`generated` maze | `save(maze, "foo")` | File has entry/exit + grid lines, no `MazeId` line | No error |
| Load an existing maze | `load("foo", MazeKind.CLASSIC)` | Returns a `Maze` matching what was saved (round-trip) | No error |
| Load a maze that doesn't exist | `load("missing", MazeKind.CLASSIC)` | — | Raises `MazeNotFoundError` |
| `find_by_id` on an existing classic/saved-random maze | `find_by_id(maze_id)` | Returns the matching `Maze` | No error |
| `find_by_id` when nothing matches | `find_by_id(unknown_id)` | Returns `None` | No error |
| Save with an empty or path-separator-containing `name` | `save(maze, "")` / `save(maze, "a/b")` | — | Raises `InvalidMazeNameError` |
| Read a hand-written legacy-shaped CSV (no `MazeId`, sketch kind) | fixture matching real legacy entry/exit/grid content | Decodes into the exact same entry/exit `Position`s and grid `Cell` values | No error |

</intent-contract>

## Code Map

- `src/labyrinthes/adapters/__init__.py` -- new; empty package marker, mirrors `domain/__init__.py`'s docstring style
- `src/labyrinthes/adapters/storage/__init__.py` -- new; re-exports `CsvMazeRepository`, `DEFAULT_MAZES_ROOT`, `maze_file_path`, `mint_maze_id`, `InvalidMazeNameError` via `__all__`
- `src/labyrinthes/adapters/storage/errors.py` -- new; `InvalidMazeNameError(LabyrinthesError)`
- `src/labyrinthes/adapters/storage/maze_id_minting.py` -- new; `mint_maze_id() -> MazeId` (`uuid.uuid4().hex`), the single shared function AD-3/AD-8 require
- `src/labyrinthes/adapters/storage/paths.py` -- new; `DEFAULT_MAZES_ROOT`, `MAZE_FILE_SUFFIX`, `maze_file_path(root, kind, name) -> Path` (validates `name`, raises `InvalidMazeNameError`) — the one path/naming module AD-8 says both this repository and the future migration script import
- `src/labyrinthes/adapters/storage/csv_maze_format.py` -- new; `read_maze_csv(path, kind) -> Maze`, `write_maze_csv(path, maze) -> None` — the shared serialization routine AD-6 requires every writer to reuse
- `src/labyrinthes/adapters/storage/csv_maze_repository.py` -- new; `CsvMazeRepository(MazeRepository)` implementing `save`/`load`/`find_by_id` on top of `paths.py`/`csv_maze_format.py`/`maze_id_minting.py`
- `src/labyrinthes/application/maze_repository.py` -- existing (Story 1.3); read-only, pins the exact signatures implemented here
- `src/labyrinthes/domain/maze.py`, `grid.py`, `cell.py`, `position.py`, `maze_id.py` -- existing; read-only, consumed as-is
- `tests/adapters/storage/test_paths.py` -- new; `maze_file_path` layout + `InvalidMazeNameError` cases from the I/O matrix
- `tests/adapters/storage/test_maze_id_minting.py` -- new; `mint_maze_id()` returns distinct, non-empty `MazeId`s
- `tests/adapters/storage/test_csv_maze_format.py` -- new; `read_maze_csv`/`write_maze_csv` round-trip + the legacy-fixture compatibility case
- `tests/adapters/storage/test_csv_maze_repository.py` -- new; covers the I/O matrix's `save`/`load`/`find_by_id` rows end-to-end via `tmp_path`

## Tasks & Acceptance

**Execution:**
- [x] `src/labyrinthes/adapters/__init__.py` -- create empty-package marker -- first file under `adapters/`, needed before `adapters/storage/` can be a subpackage
- [x] `src/labyrinthes/adapters/storage/errors.py` -- add `InvalidMazeNameError(LabyrinthesError)` -- names the one new error this story introduces, in the project's existing single-hierarchy style
- [x] `src/labyrinthes/adapters/storage/maze_id_minting.py` -- add `mint_maze_id() -> MazeId` -- single shared minting function Story 1.4's `save()` and Epic 4's migration script both call
- [x] `src/labyrinthes/adapters/storage/paths.py` -- add `DEFAULT_MAZES_ROOT`, `MAZE_FILE_SUFFIX`, `maze_file_path(root, kind, name)` with name validation -- declares the new-layout path scheme once, per AD-8
- [x] `src/labyrinthes/adapters/storage/csv_maze_format.py` -- add `read_maze_csv`/`write_maze_csv` covering entry/exit `col,row` lines, the conditional `MazeId` line, and grid rows -- the one shared serializer AD-6 requires
- [x] `src/labyrinthes/adapters/storage/csv_maze_repository.py` -- add `CsvMazeRepository(MazeRepository)` wiring the above into `save`/`load`/`find_by_id` -- the concrete port implementation this story delivers
- [x] `src/labyrinthes/adapters/storage/__init__.py` -- re-export the public names via `__all__` -- matches `application/__init__.py`'s existing convention
- [x] `tests/adapters/storage/test_paths.py` -- cover the I/O matrix's name-validation row -- proves invalid names fail fast before any file I/O
- [x] `tests/adapters/storage/test_maze_id_minting.py` -- proves minted ids are distinct and non-empty -- guards against a degenerate always-same-value implementation
- [x] `tests/adapters/storage/test_csv_maze_format.py` -- round-trip a `classic` maze (with id) and a `sketch` maze (without), plus the legacy-fixture case -- proves byte-shape fidelity independent of the repository's file-lookup logic
- [x] `tests/adapters/storage/test_csv_maze_repository.py` -- cover the I/O matrix's `save`/`load`/`find_by_id`/not-found rows via `tmp_path` -- proves the full port contract end-to-end

**Acceptance Criteria:**
- [x] Given a maze CSV in the new-layout format, when `MazeRepository.load()` reads it, then entry/exit, the `MazeId` (if present), and the grid decode correctly into a `Maze` value
- [x] Given a `Maze` being saved as `classic` or `saved-random` for the first time, when `MazeRepository.save()` writes it, then a `MazeId` is minted once, via the shared minting function, and written as the header line immediately after entry/exit and before the grid rows
- [x] Given a `Maze` that already carries a `MazeId`, when it is re-saved, then the existing id is carried forward unchanged, never re-minted
- [x] Given a `sketch` or `generated` maze, when it is saved, then no `MazeId` line is written
- [x] Given `tests/test_architecture_boundaries.py`'s existing scanning tests, when run against this story's new `adapters/storage/` files, then they still pass unchanged (no `tkinter` import introduced)

## Spec Change Log

## Review Triage Log

### 2026-08-06 — Review pass
- intent_gap: 0
- bad_spec: 0
- patch: 5 (medium 1, low 4)
- defer: 2 (medium 1, low 1)
- reject: 7
- addressed_findings:
  - `[low]` `[patch]` `test_load_round_trips_a_saved_maze` never exercised `MazeKind.GENERATED` — added it to the parametrize list
  - `[medium]` `[patch]` `find_by_id` deserialized every candidate file's full grid, so one unrelated corrupt/malformed file anywhere in `classic/`/`saved-random/` crashed an otherwise-unrelated lookup — wrapped the per-file `read_maze_csv` call in `try`/`except (OSError, ValueError, LabyrinthesError)` to skip and keep scanning, plus a new `test_find_by_id_skips_an_unrelated_file_that_fails_to_parse`
  - `[low]` `[patch]` `adapters/storage/__init__.py`'s `__all__` omitted `MAZE_FILE_SUFFIX`, even though `paths.py`'s own docstring frames the whole module (not just `maze_file_path`) as what Epic 4's migration script will import — added it to the import and `__all__`
  - `[low]` `[patch]` `load()`'s `InvalidMazeNameError` path (via `maze_file_path`) had no test, only `save()`'s did — added `test_load_rejects_invalid_names`
  - `[low]` `[patch]` `save()`'s overwrite-on-duplicate-`name` behavior (documented in the port's own Story 1.3 docstring) was untested beyond id-preservation — added `test_save_overwrites_an_existing_maze_with_different_content`, saving a smaller grid over a larger one and asserting no stale trailing rows survive

Findings routed to `deferred-work.md` (real, but out of this story's declared minimal/mechanical scope, mirroring Story 1.3's `RecordsRepository`-style restraint precedent): `write_maze_csv` is not atomic (no temp-file-plus-rename), so a crash mid-write can corrupt/lose a maze file — mirrors the legacy app's own non-atomic writes, not a regression; `read_maze_csv` raises raw `IndexError`/`ValueError` rather than a typed `LabyrinthesError` on truncated/malformed CSV content — best paired with a future format-validation or Epic 4 migration-hardening pass.

Findings rejected as noise (each judged non-actionable without expanding this story's scope beyond epics.md's ACs, or already correct as designed): the architecture-boundary test suite doesn't scan `adapters/storage/` for a `tkinter` import in the reverse direction (pre-existing Story 1.2 test-scope decision, no actual violation exists in this diff); `DEFAULT_MAZES_ROOT`'s CWD-relative, untested-at-runtime default (explicitly deferred to Story 1.7's composition-root wiring per this spec's own Design Notes); `maze_file_path`'s name validation not covering NUL bytes/reserved characters/whitespace (explicitly scoped out — narrow-on-purpose per this spec's Design Notes and Never section, full validation is Story 3.6/`BuilderService`'s job); the legacy-fixture compatibility test covering only `sketch` kind (matches the I/O matrix's literally-specified scenario, not a gap); `InvalidMazeNameError` living in `adapters/storage/errors.py` rather than `application/errors.py` (correct layering — an adapter-level concern, not application-level — both still subclass the one project `LabyrinthesError` hierarchy); no defense against two files sharing the same `MazeId` across kinds (uniqueness is an invariant the port's own Story 1.3 docstring already assumes, not something this story's `find_by_id` needs to defensively police); `path.parent` being occupied by a regular file instead of a directory (unrealistic manual-tampering scenario for a folder layout the repository itself creates, not worth guarding).

## Design Notes

- **`col,row` line order, not `row,col`:** verified directly against the legacy reader (`Laby_grille.ouvrir_lab`: `self.entrée_lab = tab` then `self.canvas.balle.def_position(entrée_lab[0], entrée_lab[1])`, and `def_position` assigns `self.x = x` where `x` indexes columns — `self.grille.lab[self.y][self.x]`). Getting this backwards would silently transpose every entry/exit on load.
- **No content-sniffing for the `MazeId` line:** `load(name, kind)` and `find_by_id`'s per-directory scan both already know `kind` before opening a file, so whether line 3 is an id or the first grid row is a pure function of `kind`, not something parsed heuristically.
- **New-layout folder names reuse `MazeKind.value` directly** (`"classic"`, `"sketch"`, `"saved-random"`, `"generated"`) instead of a separate name-mapping table — those values are already the intended English folder names, so this is the single declaration AD-8 asks for, with no risk of the mapping and the enum drifting apart.
- **`find_by_id` scans files, no id index:** Story 1.3 explicitly deferred a `list()`/browse method; without one, the only way to resolve a `MazeId` is to open each `classic`/`saved-random` file's header and compare. Acceptable for this milestone's expected maze counts (tens, not thousands) — an index file is an optimization for later if it ever matters.
- **`InvalidMazeNameError` is narrow:** it only rejects what would break the on-disk mapping (empty name, path separators) — not a general name-validation feature (length, character set, duplicate-name prompting). Those are Story 3.6/`BuilderService` concerns.

## Verification

**Commands:**
- `pytest -q` -- expected: full suite passes, including the new `tests/adapters/storage/` tests
- `ruff check .` -- expected: no findings
- `ruff format --check .` -- expected: no findings

## Auto Run Result

**Summary:** Added `adapters/storage/`, the single concrete `MazeRepository` implementation (`CsvMazeRepository`), backed by one CSV file per maze under a declared root, one subfolder per `MazeKind`. Implements `save`/`load`/`find_by_id` against the legacy CSV shape (entry/exit `col,row` header lines, an optional `MazeId` line for `classic`/`saved-random` mazes, then grid rows), preserving cell encoding byte-for-byte. This unblocks every future Builder/Player/Home story that persists or loads a maze, and gives Epic 4's migration script the shared path-naming module (`paths.py`), CSV serializer (`csv_maze_format.py`), and `MazeId` minting function (`maze_id_minting.py`) it will reuse.

**Files changed:**
- `src/labyrinthes/adapters/__init__.py` -- new; `adapters/` package marker
- `src/labyrinthes/adapters/storage/__init__.py` -- new; re-exports `CsvMazeRepository`, `DEFAULT_MAZES_ROOT`, `MAZE_FILE_SUFFIX`, `maze_file_path`, `mint_maze_id`, `InvalidMazeNameError`
- `src/labyrinthes/adapters/storage/errors.py` -- new; `InvalidMazeNameError(LabyrinthesError)`
- `src/labyrinthes/adapters/storage/maze_id_minting.py` -- new; `mint_maze_id()` (`uuid.uuid4().hex`)
- `src/labyrinthes/adapters/storage/paths.py` -- new; `DEFAULT_MAZES_ROOT`, `MAZE_FILE_SUFFIX`, `maze_file_path(root, kind, name)`
- `src/labyrinthes/adapters/storage/csv_maze_format.py` -- new; `read_maze_csv`/`write_maze_csv`, the shared CSV serializer
- `src/labyrinthes/adapters/storage/csv_maze_repository.py` -- new; `CsvMazeRepository(MazeRepository)`, with a review-patched corrupt-file-tolerant `find_by_id`
- `tests/adapters/storage/test_paths.py`, `test_maze_id_minting.py`, `test_csv_maze_format.py`, `test_csv_maze_repository.py` -- new; full I/O-matrix coverage plus review-patched additions (`GENERATED` load round-trip, `find_by_id` corrupt-file skip, `load()` invalid-name, `save()` overwrite-with-different-content)
- `_bmad-output/implementation-artifacts/deferred-work.md` -- appended two review-deferred findings (non-atomic writes, untyped errors on malformed CSV content)

**Review findings breakdown:** 5 patches applied (1 medium: `find_by_id` crashing on an unrelated corrupt file instead of skipping it; 4 low: missing `GENERATED`-kind round-trip test, missing `MAZE_FILE_SUFFIX` in `__all__`, missing `load()` invalid-name test, missing save-overwrite-with-different-content test). 2 findings deferred (non-atomic `write_maze_csv`, medium; untyped exceptions on malformed CSV read, low) — both real but outside this story's declared minimal/mechanical scope, logged to `deferred-work.md` for a future hardening pass. 7 findings rejected as noise: architecture-boundary test not scanning `adapters/storage/` for `tkinter` imports in the reverse direction (pre-existing Story 1.2 test-scope decision, no actual violation); `DEFAULT_MAZES_ROOT`'s untested runtime default (explicitly Story 1.7's job); `maze_file_path`'s narrow name validation (explicitly scoped out per this spec's own Design Notes); the legacy fixture covering only `sketch` kind (matches the I/O matrix's literal scenario); `InvalidMazeNameError`'s module placement (correct layering, not fragmentation); no duplicate-`MazeId` defense (an assumed port invariant, not this story's job to police); `path.parent` occupied by a regular file (unrealistic tampering scenario). No `intent_gap` or `bad_spec` findings — the spec needed no amendment.

**Verification performed:** `pytest -q` -- 114 passed (109 from initial implementation + 5 new from the review-patch pass). `ruff check .` -- all checks passed. `ruff format --check .` -- all 12 of this story's files (7 source, 4 test, 1 spec) formatted clean; the one pre-existing unformatted file in the repo (`_bmad-output/implementation-artifacts/1-1-domain-model-foundation.md`) predates this story and was left untouched. All 5 acceptance criteria and all 11 execution tasks verified satisfied by direct inspection and test run, not just file existence. Two independent review passes (adversarial + edge-case) ran in parallel against the full diff; every finding was triaged, with 5 patched, 2 deferred, and 7 rejected as either out-of-scope-by-design or already covered.

**Residual risks:** Low. The two deferred findings (non-atomic writes, untyped exceptions on malformed input) are real but bounded: the non-atomic-write risk mirrors the legacy app's own behavior (not a regression), and the untyped-exception risk only surfaces on a hand-corrupted or externally-damaged file, which is not a normal operating condition for this milestone. `DEFAULT_MAZES_ROOT`'s real-world resolution is intentionally left to Story 1.7's composition-root wiring, as this story's Design Notes already state. The new-layout folder-naming scheme (`mazes/<kind.value>/<name>.csv`) is this story's own greenfield decision, made explicit and self-documenting (folder names reuse `MazeKind.value` directly) so Epic 4's migration script has a single, unambiguous target to write into.
