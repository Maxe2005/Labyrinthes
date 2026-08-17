---
title: 'Story 1.3: Persistence port interfaces — MazeRepository & SettingsRepository'
type: 'feature'
created: '2026-08-06'
status: 'done'
review_loop_iteration: 0
followup_review_recommended: false
context: ['_bmad-output/implementation-artifacts/epic-1/epic-1-context.md']
warnings: [oversized]
baseline_revision: '996fd7fabc2bdf412f6ece7312cf6dc0acf600f4'
final_revision: 'b8801b7bb18aa4f03d0679d1e2cbb7d21e74d627'
---

<intent-contract>

## Intent

**Problem:** No `application/` package exists yet, so nothing pins `MazeRepository`'s or `SettingsRepository`'s method signatures — Stories 1.4/1.5 (concrete implementations) and every Epic 2/3/5 story that consumes a repository would otherwise each guess independently and drift.

**Approach:** Create `application/` and define both as `abc.ABC` port interfaces with `@abstractmethod` methods only (no bodies beyond a docstring + `raise NotImplementedError`) — no concrete storage, no on-disk format decision (that's Story 1.4/1.5's job). Also add `application/settings_keys.py` declaring the `shared`-scope key names once, and `application/errors.py` for the two new not-found errors, extending the existing `LabyrinthesError` hierarchy.

## Boundaries & Constraints

**Always:** Define both ports as `abc.ABC` subclasses (no `Protocol` precedent in this codebase; ABC raises a real `TypeError` on incomplete implementations). Everything lives under `application/`, importing nothing from `adapters/` or any UI framework (AD-1) — enforced by the existing `tests/test_architecture_boundaries.py` scanner, which already covers `application/`. Every abstract method gets a docstring stating its contract (return value, raised errors) since there's no implementation yet to read for behavior. New errors subclass `LabyrinthesError` (`domain/errors.py`) — the project's one typed exception hierarchy, not a bespoke per-port shape. `MazeRepository` uses only existing `domain/` types (`Maze`, `MazeId`, `MazeKind`) — no new domain types, no display-name field on `Maze` (Story 1.1's shape is settled). `SettingsScope` is a plain `enum.Enum` with string values, mirroring `MazeKind`'s style.

**Block If:** None identified — signatures are fully determined by epics.md's ACs plus AD-5/AD-6/AD-7/AD-9/AD-12 (AD-12's `RecordsRepository` is the direct pattern to mirror: minimal, mechanical, no business logic on the port).

**Never:** Do not implement either port (no CSV reading/writing, no file paths, no `adapters/storage/`) — that's Story 1.4/1.5. Do not add a `list()`/browse method — not required by this story's ACs; a later consumer can extend the port. Do not populate actual `shared`-scope default values (e.g. FR-4's 3–50/3–35 bounds) — only key *names* are in scope here. Do not use a raw filesystem `Path` in `MazeRepository`'s signatures — keep the port storage-agnostic (name + kind); the on-disk format is Story 1.4's concern.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Instantiate `MazeRepository` directly | `MazeRepository()` | Raises `TypeError` (abstract methods not implemented) | N/A — this is the expected error |
| Instantiate `SettingsRepository` directly | `SettingsRepository()` | Raises `TypeError` (abstract methods not implemented) | N/A — this is the expected error |
| Subclass implements all abstract methods | a fake test subclass overriding `save`/`load`/`find_by_id` | Instantiates successfully, is a `MazeRepository` instance | N/A |
| Subclass omits one abstract method | a fake test subclass missing `find_by_id` | Raises `TypeError` on instantiation | N/A — this is the expected error |
| `SettingsScope` membership | iterate `SettingsScope` | Exactly `BUILDER="builder"`, `GAME="game"`, `SHARED="shared"`, no others | N/A |
| Shared-scope key constants | import `application/settings_keys.py` | Module exposes distinct string constants for FR-4's maze size bounds (min/max columns, min/max rows), each a non-empty `str` | N/A |

</intent-contract>

## Code Map

- `src/labyrinthes/application/__init__.py` -- new package; re-exports the two ports, `SettingsScope`, and the two new errors via `__all__`, mirroring `domain/__init__.py`'s pattern
- `src/labyrinthes/application/errors.py` -- new file; `MazeNotFoundError`, `SettingNotFoundError`, both subclassing `LabyrinthesError`
- `src/labyrinthes/application/maze_repository.py` -- new file; `MazeRepository(ABC)` with `save`/`load`/`find_by_id` abstract methods
- `src/labyrinthes/application/settings_repository.py` -- new file; `SettingsScope(enum.Enum)`, `SettingValue` type alias, `SettingsRepository(ABC)` with `get`/`set` abstract methods
- `src/labyrinthes/application/settings_keys.py` -- new file; `shared`-scope key name constants (FR-4's maze size bounds), the single module every consumer imports instead of inventing its own key strings
- `src/labyrinthes/domain/errors.py` -- existing; read-only, `LabyrinthesError` is the base the new application errors extend
- `tests/application/test_maze_repository.py` -- new file; ABC instantiation/subclassing tests
- `tests/application/test_settings_repository.py` -- new file; `SettingsScope` membership + ABC instantiation/subclassing tests
- `tests/application/test_settings_keys.py` -- new file; pins the shared-scope key constants exist, are distinct, non-empty strings
- `tests/test_architecture_boundaries.py` -- existing; no changes needed, but its `application/`-scanning tests now have real content to scan for the first time

## Tasks & Acceptance

**Execution:**
- [x] `src/labyrinthes/application/errors.py` -- add `MazeNotFoundError`, `SettingNotFoundError` subclassing `LabyrinthesError` -- gives the two new ports a not-found error to raise, in the project's existing single-hierarchy style
- [x] `src/labyrinthes/application/maze_repository.py` -- add `MazeRepository(ABC)` with `save(self, maze: Maze, name: str) -> Maze`, `load(self, name: str, kind: MazeKind) -> Maze`, `find_by_id(self, maze_id: MazeId) -> Maze | None`, each `@abstractmethod` with a docstring stating its contract -- pins the exact signatures Story 1.4 must implement
- [x] `src/labyrinthes/application/settings_repository.py` -- add `SettingsScope(enum.Enum)` (`BUILDER`/`GAME`/`SHARED`), `SettingValue = str | int | float | bool | tuple[str, ...]` type alias, `SettingsRepository(ABC)` with `get(self, scope: SettingsScope, key: str) -> SettingValue`, `set(self, scope: SettingsScope, key: str, value: SettingValue) -> None`, each `@abstractmethod` with a docstring -- pins the exact signatures Story 1.5 must implement
- [x] `src/labyrinthes/application/settings_keys.py` -- add string constants for FR-4's maze size bounds (`MAZE_MIN_COLUMNS`, `MAZE_MAX_COLUMNS`, `MAZE_MIN_ROWS`, `MAZE_MAX_ROWS`) -- the one module Builder/Game/Home import instead of hardcoding key strings per consumer
- [x] `src/labyrinthes/application/__init__.py` -- re-export `MazeRepository`, `SettingsRepository`, `SettingsScope`, `SettingValue`, `MazeNotFoundError`, `SettingNotFoundError` via `__all__` -- matches `domain/__init__.py`'s existing package-level import convention
- [x] `tests/application/test_maze_repository.py` -- cover the I/O matrix's `MazeRepository` rows (direct instantiation fails, complete fake subclass instantiates, incomplete fake subclass fails) -- proves the ABC actually enforces its contract
- [x] `tests/application/test_settings_repository.py` -- cover the I/O matrix's `SettingsRepository`/`SettingsScope` rows (enum membership, direct instantiation fails, complete/incomplete fake subclasses) -- same enforcement proof plus pins the three scope values
- [x] `tests/application/test_settings_keys.py` -- cover the I/O matrix's key-constants row (four distinct non-empty string constants) -- guards against a future accidental duplicate/typo'd key name

**Acceptance Criteria:**
- Given `application/`, when `MazeRepository` is defined, then it exposes saving a `Maze`, loading a `Maze` by name/kind, and looking one up by `MazeId` — not only by name/path
- Given `application/`, when `SettingsRepository` is defined, then it exposes `get(scope, key)`/`set(scope, key, value)` covering the `builder`/`game`/`shared` scopes via `SettingsScope`
- Given the set of `shared`-scope key names (FR-4's size bounds), when declared, then they live in exactly one module (`application/settings_keys.py`), not duplicated per consumer
- Given `MazeRepository`/`SettingsRepository`, when either is instantiated directly or via an incomplete subclass, then Python raises `TypeError` — proving they are genuine abstract contracts, not documentation-only stubs
- Given `tests/test_architecture_boundaries.py`'s existing `application/`-scanning tests, when run against this story's new files, then they still pass (no `tkinter`/`adapters` import introduced)

## Spec Change Log

## Review Triage Log

### 2026-08-06 — Review pass
- intent_gap: 0
- bad_spec: 0
- patch: 4 (medium 3, low 1)
- defer: 0
- reject: 9 (medium 0, low 9)
- addressed_findings:
  - `[low]` `[patch]` `MazeNotFoundError`/`SettingNotFoundError` had no test verifying they subclass `LabyrinthesError` (an explicitly stated "Always" constraint) — added `tests/application/test_errors.py`
  - `[medium]` `[patch]` `MazeRepository.save()` didn't say who's responsible for a `GENERATED`→`SAVED_RANDOM`-style kind transition on save, or what happens saving over an existing `name`+`kind` — clarified in its docstring: the caller passes a `Maze` already carrying its target kind, and a same-`name`+`kind` save overwrites (duplicate-name *prevention* is a caller/service concern, not this port's)
  - `[medium]` `[patch]` `MazeRepository.find_by_id()` didn't state whether `MazeId` uniqueness holds per-kind or globally — clarified in its docstring: unique across both id-eligible kinds combined, a single global lookup
  - `[medium]` `[patch]` (bundled with the above) confirmed no method signature changed — both fixes are docstring-only, no re-implementation needed

Findings rejected as noise (each judged non-actionable without over-specifying "how" or expanding this story's scope beyond epics.md's ACs): no static type-checker in the toolchain to enforce signatures beyond docstrings (pre-existing, whole-project, out of scope); `SettingValue`'s `bool`/`int` ordering (Python `isinstance` dispatch order is a call-site concern, unrelated to `Union` member order); the "complete" test doubles not exercising trivial stub bodies (no meaningful signal to gain); `settings_keys.py` naming (`COLUMNS`/`ROWS`) vs. `Grid`'s (`width`/`height`) (intentional — traces to FR-4's own product-language vocabulary, single declared translation point); `SettingsRepository` lacking a `has()`/default-arg convenience (explicitly out of scope per this story's Never section); `SettingsRepository.set()`'s behavior on an out-of-`SettingValue`-union runtime value, empty-string keys, and non-ASCII/empty maze `name`s (all Story 1.4/1.5 on-disk/validation concerns, explicitly this port-only story's non-goal); the shared-scope-keys AC being currently unfalsifiable (inherent — by design, no consumers exist yet).

## Design Notes

- **`name: str` + `kind: MazeKind`, not a `Path`:** the legacy layout is one file per maze under a kind-specific folder; Story 3.6 already establishes author-chosen "name" + duplicate-name handling. `kind` is needed on `load()` since a bare name isn't unique across kinds. Keeps the port storage-agnostic — filesystem details are Story 1.4's concern.
- **`load()` raises, `find_by_id()` returns `Maze | None`:** `load()` targets a specific, already-known maze (like `open()` raising `FileNotFoundError`) — not finding it is a real error. `find_by_id()` is inherently a "does this still exist" lookup (e.g. Home resolving a `Record.maze_id` that may reference a since-deleted maze) — absence is expected, so `None` fits better than an exception.
- **Mirrors AD-12's `RecordsRepository`:** "minimal and mechanical... no 'record and decide' method on the port itself." Same restraint here — no validation, no business rules beyond epics.md's ACs.
- **`SettingValue` includes `tuple[str, ...]`:** the legacy settings CSV comma-joins list-valued settings; `tuple` (not `list`) matches the project's immutable-value-object convention (`Grid.cells` is already nested tuples).

## Verification

**Commands:**
- `pytest -q` -- expected: full suite passes, including the new `tests/application/` tests and the existing (now newly-exercised) `application/`-scanning architecture boundary tests
- `ruff check .` -- expected: no findings
- `ruff format --check .` -- expected: no findings

## Auto Run Result

**Summary:** Created `src/labyrinthes/application/`, the project's first `application/`-layer package, defining `MazeRepository` and `SettingsRepository` as `abc.ABC` port interfaces (no concrete storage), plus the supporting `SettingsScope` enum, `settings_keys.py` shared-scope key constants, and an application-layer error hierarchy. This unblocks Story 1.4 (concrete `MazeRepository`) and Story 1.5 (concrete `SettingsRepository`), and every Epic 2/3/5 story that consumes either repository, from starting with divergent method-signature assumptions.

**Files changed:**
- `src/labyrinthes/application/__init__.py` -- new; package `__all__` re-exporting both ports, `SettingsScope`, `SettingValue`, and the two new errors
- `src/labyrinthes/application/errors.py` -- new; `MazeNotFoundError`, `SettingNotFoundError`, both subclassing `LabyrinthesError`
- `src/labyrinthes/application/maze_repository.py` -- new; `MazeRepository(ABC)` with `save`/`load`/`find_by_id` abstract methods, docstrings clarified in review to cover kind-transition and MazeId-uniqueness edge cases
- `src/labyrinthes/application/settings_repository.py` -- new; `SettingsScope(enum.Enum)`, `SettingValue` type alias, `SettingsRepository(ABC)` with `get`/`set` abstract methods
- `src/labyrinthes/application/settings_keys.py` -- new; `MAZE_MIN_COLUMNS`/`MAZE_MAX_COLUMNS`/`MAZE_MIN_ROWS`/`MAZE_MAX_ROWS` shared-scope key constants (FR-4's size bounds)
- `tests/application/test_maze_repository.py`, `tests/application/test_settings_repository.py`, `tests/application/test_settings_keys.py` -- new; ABC instantiation/subclassing tests, `SettingsScope` membership, key-constant distinctness
- `tests/application/test_errors.py` -- new (review patch); pins both new errors subclass `LabyrinthesError`

**Review findings breakdown:** 4 patches applied (1 low: missing subclass test for the two new errors; 3 medium: `MazeRepository.save()`/`find_by_id()` docstring gaps around kind-transition-on-save, overwrite-on-duplicate-name, and cross-kind `MazeId` uniqueness — all resolved as docstring-only clarifications, no signature changes). 9 findings rejected as noise (pre-existing whole-project lack of static type-checking; a confused bool/int `Union`-ordering claim; test doubles not exercising trivial stub bodies; `settings_keys.py`'s `COLUMNS`/`ROWS` naming vs. `Grid`'s `width`/`height` — judged intentional, traces to FR-4's own vocabulary; a `has()`/default-arg convenience method — explicitly out of scope; `SettingsRepository.set()`/`get()` edge cases on invalid values, empty keys, and non-ASCII maze names — all Story 1.4/1.5's on-disk/validation concerns; the shared-key AC being currently unfalsifiable with no consumers yet — inherent by design). No `intent_gap` or `bad_spec` findings; zero deferred (nothing found was genuinely pre-existing/unrelated to this story).

**Verification performed:** `pytest -q` -- 75 passed (72 from initial implementation + 3 new from the review-patch `test_errors.py`). `ruff check .` -- all checks passed. `ruff format --check src/labyrinthes/application tests/application` -- all formatted (a `ruff format .` run incidentally reformatted an unrelated pre-existing story-1.1 doc, which was reverted — out of scope for this story). All 5 acceptance criteria and all 8 execution tasks verified satisfied by direct inspection and test run, not just file existence.

**Residual risks:** Low. This is an interface-only story with no runtime behavior beyond ABC enforcement (already tested). The main residual risk is that Story 1.4/1.5's concrete implementations could still diverge on the newly-documented-but-unenforced edge cases (overwrite-on-duplicate-name, kind-transition timing) since nothing but docstrings pins them — acceptable, as encoding that behavior in the port itself would have meant adding validation logic explicitly out of scope for a port-definition story (mirroring AD-12's "minimal and mechanical" precedent).
