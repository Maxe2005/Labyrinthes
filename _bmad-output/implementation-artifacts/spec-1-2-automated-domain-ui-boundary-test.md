---
title: 'Story 1.2: Automated domain/UI boundary test'
type: 'chore'
created: '2026-08-05'
status: 'in-progress'
baseline_commit: f6d4df8e9b31ecaee43968f5019d277cff3d919d
review_loop_iteration: 1
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

- `tests/test_architecture_boundaries.py` -- new file; AST-based import scanner + the four boundary tests
- `src/labyrinthes/domain/` -- existing package the scan targets (read-only, no changes)
- `pyproject.toml` -- confirms `[tool.pytest.ini_options] testpaths = ["tests"]` already covers this file; no changes needed

## Tasks & Acceptance

**Execution:**
- [x] `tests/test_architecture_boundaries.py` -- add an AST-based helper that walks a directory's `.py` files (returning empty for a missing directory) and resolves each file's imports to dotted module paths -- must handle both plain (`import x.y`) and submodule-style `from x import y` forms (an `ast.ImportFrom`'s imported names, not just its `.module`, can themselves be forbidden submodules — e.g. `from labyrinthes.adapters.tkinter import builder`), plus relative imports -- shared foundation for all four checks
- [x] `tests/test_architecture_boundaries.py` -- `test_domain_and_application_do_not_import_tkinter_or_adapters` -- scans `domain/` and `application/`, fails on any `tkinter`/`tkinter.*` or `labyrinthes.adapters*` import
- [x] `tests/test_architecture_boundaries.py` -- `test_tkinter_screens_do_not_import_each_other` -- for each of `home`/`builder`/`player`, fails if it imports either of the other two
- [x] `tests/test_architecture_boundaries.py` -- `test_common_does_not_import_screens` -- fails if `adapters/tkinter/common/` imports `home/`, `builder/`, or `player/`
- [x] `tests/test_architecture_boundaries.py` -- `test_tkinter_screens_do_not_import_storage_adapters` -- (new, per AD-9) for each of `home`/`builder`/`player`, fails if it imports `labyrinthes.adapters.storage` directly -- storage access must always go through an `application/` service, never a direct adapter-to-adapter reach

**Acceptance Criteria:**
- Given the test suite, when it scans `domain/` and `application/` source, then it fails if any forbidden import (`tkinter`, `adapters`) is found
- Given `adapters/tkinter/home`, `adapters/tkinter/builder`, `adapters/tkinter/player`, when any one imports another directly, then the test fails
- Given `adapters/tkinter/common/`, when it imports `home/`, `builder/`, or `player/`, then the test fails
- Given `adapters/tkinter/home`, `adapters/tkinter/builder`, `adapters/tkinter/player`, when any one imports `adapters/storage/` directly, then the test fails (AD-9)
- Given the current codebase (before feature code exists), when the test runs, then it passes, establishing the gate ahead of the code it will guard

## Spec Change Log

- **Finding (review, iteration 1):** Blind Hunter and Edge Case Hunter both independently found, and this was verified directly against `ARCHITECTURE-SPINE.md`'s AD-9, that Tasks & Acceptance omitted a required check: AD-9 explicitly bundles `adapters/tkinter/` → `adapters/storage/` direct-import detection into the *same* test mechanism as the other three checks, even though epics.md's own terser AC wording for Story 1.2 didn't spell it out. **Amended:** added a fourth task/test (`test_tkinter_screens_do_not_import_storage_adapters`) and a matching AC. **Avoids:** shipping a "boundary test" story that silently leaves one of AD-9's four enforced rules unguarded. **KEEP:** the AST-only static-parse approach, the missing-directory-is-zero-violations behavior (this is what lets AC5/pre-feature-codebase pass), and the one-shared-helper-many-tests structure — all worked well and must survive re-derivation.
- **Finding (review, iteration 1), same root cause folded in here rather than as a separate loopback:** both reviewers independently found, and manual repro confirmed, that the first implementation's `ImportFrom` resolution only inspected `node.module`, never `node.names` — so `from labyrinthes.adapters.tkinter import builder` (inside `home/`) and `from labyrinthes import adapters` (inside `domain/`) silently bypassed every check, since the resolved string was the *parent* package, not the actually-imported submodule. **Amended:** the first Execution task now explicitly calls out that submodule-style `from x import y` must be resolved too, not just `.module`. **Avoids:** a boundary test that only catches `from ..sibling import x`-style relative imports while missing the equally natural absolute/name-based form the story exists to guard against. **KEEP:** none of the prior code survives as-is (it's being re-derived), but the manual-sanity-check discipline from Verification below — reproducing an actual violation and confirming the test catches it before cleanup — is what caught this the first time and must be kept, extended to explicitly cover the name-based forms.

## Design Notes

- **Resolving `from <pkg> import <name>`:** a statically-parsed `ast.ImportFrom` cannot tell, without filesystem introspection, whether `<name>` refers to a submodule (`labyrinthes.adapters.tkinter.builder`) or a plain attribute of `<pkg>`. For a boundary gate, over-approximating is correct and safe: for each imported name, also yield `f"{resolved_base}.{name}"` in addition to `resolved_base` itself, so both readings are checked against the forbidden-prefix list. Concretely, both of these must be caught by the amended implementation:
  ```python
  # inside src/labyrinthes/adapters/tkinter/home/foo.py
  from labyrinthes.adapters.tkinter import builder  # must be caught (name-based)
  from ..builder import something  # already caught (module-based)
  ```
  ```python
  # inside src/labyrinthes/domain/foo.py
  from labyrinthes import adapters  # must be caught (name-based)
  ```
- Prefer repo-relative paths in assertion failure messages over `PACKAGE_ROOT`'s absolute `.resolve()`d form — keeps output stable/portable across machines and CI.

## Verification

**Commands:**
- `pytest -q` -- expected: full suite passes, including the 4 new architecture-boundary tests
- `ruff check .` -- expected: no findings
- `ruff format --check .` -- expected: no findings (aside from the pre-existing, out-of-scope Story 1.1 markdown note, if still present)

**Manual checks (in addition to the commands above):** temporarily create throwaway violating files, confirm the relevant test fails, then delete the throwaway files and confirm the suite is green again. Cover at minimum:
- `import tkinter` in a throwaway `domain/` file
- `from labyrinthes import adapters` in a throwaway `domain/` file (name-based -- the exact form that bypassed the first implementation)
- `from labyrinthes.adapters.tkinter import builder` in a throwaway `home/` file (name-based submodule import -- the exact form that bypassed the first implementation)
- `from ..builder import something` in a throwaway `home/` file (relative/module-based)
- `from labyrinthes.adapters.storage import x` (and the name-based form) in a throwaway `home/`, `builder/`, or `player/` file, for the new storage check
- `from ..home import y` in a throwaway `common/` file
Leave no `adapters/`/`application/` directories behind afterward -- the current codebase must stay pre-feature per AC5.
