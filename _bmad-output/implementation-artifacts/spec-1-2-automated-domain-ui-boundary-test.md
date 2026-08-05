---
title: 'Story 1.2: Automated domain/UI boundary test'
type: 'chore'
created: '2026-08-05'
status: 'in-progress'
baseline_commit: f6d4df8e9b31ecaee43968f5019d277cff3d919d
review_loop_iteration: 0
context: ['_bmad-output/implementation-artifacts/epic-1-context.md']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Nothing currently stops `domain/`/`application/` code from importing Tkinter or a storage adapter, or `adapters/tkinter/` screen packages from importing each other laterally — the exact silent architecture erosion the legacy `big_boss` pattern suffered from.

**Approach:** Add a static, AST-based pytest test that scans source files under `domain/`, `application/`, and `adapters/tkinter/{home,builder,player,common}` for forbidden imports and fails the suite on any violation. It must pass today, against the current pre-feature codebase, establishing the gate ahead of the code it will guard.

## Boundaries & Constraints

**Always:** Detect imports via static AST parsing only (never actually `import` the scanned modules) — must not require Tkinter to be available and must not execute scanned code as a side effect. Correctly resolve both absolute (`import labyrinthes.adapters...`) and relative (`from ..builder import x`) imports to their true dotted module path. Directories that don't exist yet (`application/`, `adapters/`) count as zero files / zero violations, not an error. English-only, ruff-clean, stdlib + pytest only, per CLAUDE.md rewrite conventions.

**Ask First:** None identified — self-contained test addition with no ambiguity.

**Never:** Do not add a runtime/import-hook enforcement mechanism (e.g. a `sys.meta_path` guard) — this story is a test-suite gate, per its own AC wording ("the test suite... fails"), not a runtime blocker. Do not create stub `application/`/`adapters/` packages or touch existing `domain/` files just to exercise the test — AC4 explicitly requires it to pass against today's codebase as-is.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Domain imports tkinter | a `domain/*.py` file contains `import tkinter` (or `from tkinter import ...`) | boundary test fails, reporting the offending file | N/A |
| Application imports adapters, relatively | an `application/*.py` file contains `from ..adapters import y` | boundary test fails (relative import resolved to `labyrinthes.adapters...`) | N/A |
| Screens import each other laterally | `adapters/tkinter/home/foo.py` contains `from ..builder import bar` | boundary test fails | N/A |
| Common imports a screen | `adapters/tkinter/common/x.py` contains `from ..home import y` | boundary test fails | N/A |
| Today's pre-feature codebase | only `domain/` is populated; `application/`/`adapters/` don't exist yet | all boundary tests pass (nothing to scan / nothing forbidden found) | N/A |

</frozen-after-approval>

## Code Map

- `tests/test_architecture_boundaries.py` -- new file; AST-based import scanner + the three boundary tests
- `src/labyrinthes/domain/` -- existing package the scan targets (read-only, no changes)
- `pyproject.toml` -- confirms `[tool.pytest.ini_options] testpaths = ["tests"]` already covers this file; no changes needed

## Tasks & Acceptance

**Execution:**
- [x] `tests/test_architecture_boundaries.py` -- add an AST-based helper that walks a directory's `.py` files (returning empty for a missing directory) and resolves each file's imports (absolute + relative) to dotted module paths -- shared foundation for all three checks
- [x] `tests/test_architecture_boundaries.py` -- `test_domain_and_application_do_not_import_tkinter_or_adapters` -- scans `domain/` and `application/`, fails on any `tkinter`/`tkinter.*` or `labyrinthes.adapters*` import
- [x] `tests/test_architecture_boundaries.py` -- `test_tkinter_screens_do_not_import_each_other` -- for each of `home`/`builder`/`player`, fails if it imports either of the other two
- [x] `tests/test_architecture_boundaries.py` -- `test_common_does_not_import_screens` -- fails if `adapters/tkinter/common/` imports `home/`, `builder/`, or `player/`

**Acceptance Criteria:**
- Given the test suite, when it scans `domain/` and `application/` source, then it fails if any forbidden import (`tkinter`, `adapters`) is found
- Given `adapters/tkinter/home`, `adapters/tkinter/builder`, `adapters/tkinter/player`, when any one imports another directly, then the test fails
- Given `adapters/tkinter/common/`, when it imports `home/`, `builder/`, or `player/`, then the test fails
- Given the current codebase (before feature code exists), when the test runs, then it passes, establishing the gate ahead of the code it will guard

## Spec Change Log

## Verification

**Commands:**
- `pytest -q` -- expected: full suite passes, including the 3 new architecture-boundary tests
- `ruff check .` -- expected: no findings
- `ruff format --check .` -- expected: no findings (aside from the pre-existing, out-of-scope Story 1.1 markdown note, if still present)
