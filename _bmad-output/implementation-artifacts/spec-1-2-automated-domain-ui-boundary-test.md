---
title: 'Story 1.2: Automated domain/UI boundary test'
type: 'chore'
created: '2026-08-05'
status: 'done'
baseline_commit: f6d4df8e9b31ecaee43968f5019d277cff3d919d
review_loop_iteration: 2
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

- `tests/test_architecture_boundaries.py` -- new file; AST-based import scanner + the boundary tests
- `tests/test_architecture_boundaries_scanner.py` -- new file; fixture-based regression tests pinning the scanner's own resolution behavior against synthetic violations (via `tmp_path`), so a silently-broken scanner fails loudly instead of the boundary tests trivially passing because the current codebase has nothing to violate yet
- `src/labyrinthes/domain/` -- existing package the scan targets (read-only, no changes)
- `pyproject.toml` -- confirms `[tool.pytest.ini_options] testpaths = ["tests"]` already covers these files; no changes needed

## Tasks & Acceptance

**Execution:**
- [x] `tests/test_architecture_boundaries.py` -- add an AST-based helper that walks a directory's `.py` files (returning empty for a missing directory) and resolves each file's imports to dotted module paths -- must handle both plain (`import x.y`) and submodule-style `from x import y` forms (an `ast.ImportFrom`'s imported names, not just its `.module`, can themselves be forbidden submodules), plus relative imports -- shared foundation for all checks
- [x] `tests/test_architecture_boundaries.py` -- `test_domain_and_application_do_not_import_tkinter_or_adapters` -- scans `domain/` and `application/`, fails on any `tkinter`/`tkinter.*` or `labyrinthes.adapters*` import
- [x] `tests/test_architecture_boundaries.py` -- `test_tkinter_screens_do_not_import_each_other` -- for each of `home`/`builder`/`player`, fails if it imports either of the other two
- [x] `tests/test_architecture_boundaries.py` -- `test_common_does_not_import_screens` -- fails if `adapters/tkinter/common/` imports `home/`, `builder/`, or `player/`
- [x] `tests/test_architecture_boundaries.py` -- `test_tkinter_does_not_import_storage_adapters` -- (per AD-9) scans the **whole** `adapters/tkinter/` tree -- `home/`, `builder/`, `player/`, **and `common/`** -- fails if any of them imports `labyrinthes.adapters.storage` directly; storage access must always go through an `application/` service
- [x] `tests/test_architecture_boundaries_scanner.py` -- fixture-based tests (using `tmp_path` to build a throwaway `src/labyrinthes/...`-shaped tree, not the real `src/`) that pin the scanner's own resolution behavior: assert a submodule-style `from pkg import name` import is caught, a name-based `from pkg import attr` import of a forbidden package is caught, a relative import (`from ..sibling import x`) is caught, and a directory with no matching files yields zero violations -- this is what makes the boundary tests themselves regression-proof, rather than only trivially passing because `application/`/`adapters/` don't exist yet

**Acceptance Criteria:**
- Given the test suite, when it scans `domain/` and `application/` source, then it fails if any forbidden import (`tkinter`, `adapters`) is found
- Given `adapters/tkinter/home`, `adapters/tkinter/builder`, `adapters/tkinter/player`, when any one imports another directly, then the test fails
- Given `adapters/tkinter/common/`, when it imports `home/`, `builder/`, or `player/`, then the test fails
- Given any package under `adapters/tkinter/` (`home`, `builder`, `player`, or `common`), when it imports `adapters/storage/` directly, then the test fails (AD-9 -- the whole `adapters/tkinter/` tree, not only the three screens)
- Given the current codebase (before feature code exists), when the test runs, then it passes, establishing the gate ahead of the code it will guard
- Given the scanner's own resolution logic, when exercised against synthetic fixtures covering submodule-style, name-based, and relative imports, then each known-violation fixture is reported and each known-clean fixture is not

## Spec Change Log

- **Finding (review, iteration 1):** Blind Hunter and Edge Case Hunter both independently found, verified directly against `ARCHITECTURE-SPINE.md`'s AD-9, that Tasks & Acceptance omitted a required check: AD-9 bundles `adapters/tkinter/` → `adapters/storage/` direct-import detection into the *same* test mechanism as the other three checks, though epics.md's terser AC wording for Story 1.2 didn't spell it out. **Amended:** added a fourth task/test and a matching AC (scoped, at the time, to `home`/`builder`/`player` only). **KEEP:** AST-only static-parse approach; missing-directory-is-zero-violations behavior; one-shared-helper-many-tests structure.
- **Finding (review, iteration 1), same loopback:** both reviewers independently found, and manual repro confirmed, that `ImportFrom` resolution only inspected `node.module`, never `node.names` — so `from labyrinthes.adapters.tkinter import builder` and `from labyrinthes import adapters` silently bypassed every check. **Amended:** the helper task now explicitly requires resolving submodule-style `from x import y` too.
- **Finding (review, iteration 2):** Blind Hunter found, and this was independently reproduced with a throwaway `adapters/tkinter/common/` file importing `labyrinthes.adapters.storage`, that iteration 1's storage-import fix only iterated `home`/`builder`/`player` — omitting `common/` — even though AD-9's own rule text scopes the check to "`adapters/tkinter/` importing `adapters/storage/` directly" (the whole tree) and AD-1 states `adapters/tkinter/` (unqualified) never depends on `adapters/storage/` directly. **Amended:** renamed the task/test to `test_tkinter_does_not_import_storage_adapters` and its AC to explicitly cover all four subpackages including `common/`. **Avoids:** a second silent enforcement gap in the exact same AD-9 clause. **KEEP:** everything from iteration 1's KEEP list.
- **Finding (review, iteration 2), same loopback:** Blind Hunter's strongest structural point: both prior bugs (iteration 1's name-based-import miss, iteration 2's `common/` omission) went undetected by the four `assert not violations` tests themselves, because `domain/` is clean by construction and `application/`/`adapters/` don't exist yet — the tests were tautologically green regardless of whether the scanner's resolution logic actually worked. Only ad hoc, uncommitted manual sanity checks (run once, then deleted) ever exercised the scanner against a real violation. **Amended:** added a new task and file, `tests/test_architecture_boundaries_scanner.py`, with committed `tmp_path`-based fixture tests that assert the scanner catches known synthetic violations (submodule-style, name-based, relative) and passes known-clean fixtures -- turning what were previously one-off manual checks into permanent regression coverage. **Avoids:** a third recurrence of "the scanner has a resolution bug and nothing in the committed suite would ever catch it." **KEEP:** the AC5 "passes against today's pre-feature codebase" property stays governed by the four boundary tests scanning the real `src/labyrinthes/` tree; the new fixture tests are scoped to `tmp_path` synthetic trees only, never asserting anything about the real codebase, so they don't duplicate or risk contradicting AC5.

## Design Notes

- **Resolving `from <pkg> import <name>`:** a statically-parsed `ast.ImportFrom` cannot tell, without filesystem introspection, whether `<name>` refers to a submodule or a plain attribute of `<pkg>`. Over-approximate for safety: for each imported name, also yield `f"{resolved_base}.{name}"` in addition to `resolved_base` itself. Both of these must be caught:
  ```python
  # inside src/labyrinthes/adapters/tkinter/home/foo.py
  from labyrinthes.adapters.tkinter import builder  # must be caught (name-based)
  from ..builder import something  # already caught (module-based)
  ```
  ```python
  # inside src/labyrinthes/domain/foo.py
  from labyrinthes import adapters  # must be caught (name-based)
  ```
- **Storage-import check scope:** iterate all four `adapters/tkinter/` subpackages (`home`, `builder`, `player`, `common`), not only the three screens — this check is orthogonal to the screens-vs-common lateral-import rule and has its own, broader scope per AD-9/AD-1.
- **Fixture tests, not real-tree assertions:** `tests/test_architecture_boundaries_scanner.py` builds its own throwaway package tree under `tmp_path` (e.g. `tmp_path / "src" / "labyrinthes" / "adapters" / "tkinter" / "home" / "foo.py"`) and points the scanner helper at that root, rather than at `src/labyrinthes`. It must not create or leave behind any files under the real `src/labyrinthes/` tree — that would violate AC5.
- Prefer repo-relative paths in assertion failure messages over an absolute `.resolve()`d form — keeps output stable/portable across machines and CI.
- **Known, accepted limitation:** static AST parsing cannot see dynamic imports (`importlib.import_module(...)`, `__import__(...)`). This is an accepted tradeoff of the "static analysis only, never execute scanned code" constraint (Boundaries & Constraints), not a gap to close in this story.
- **Malformed source file:** if `ast.parse` raises `SyntaxError` on a scanned file, let it propagate rather than swallowing it — a syntax error in a file this test is supposed to be scanning is itself a real problem worth a loud failure, and the current codebase has no such files.

## Verification

**Commands:**
- `pytest -q` -- expected: full suite passes, including the new architecture-boundary tests and the new scanner fixture tests
- `ruff check .` -- expected: no findings
- `ruff format --check .` -- expected: no findings (aside from the pre-existing, out-of-scope Story 1.1 markdown note, if still present)

**Manual checks (in addition to the commands above and the committed fixture tests):** temporarily create throwaway violating files under the real `src/labyrinthes/` tree, confirm the relevant test fails, then delete the throwaway files and confirm the suite is green again. Cover at minimum:
- `import tkinter` in a throwaway `domain/` file
- `from labyrinthes import adapters` in a throwaway `domain/` file (name-based)
- `from labyrinthes.adapters.tkinter import builder` in a throwaway `home/` file (name-based submodule import)
- `from ..builder import something` in a throwaway `home/` file (relative/module-based)
- `from labyrinthes.adapters.storage import x` in a throwaway file under **each** of `home/`, `builder/`, `player/`, **and `common/`** (the exact gap iteration 2 fixed)
- `from ..home import y` in a throwaway `common/` file
Leave no `adapters/`/`application/` directories behind afterward under the real `src/labyrinthes/` tree -- it must stay pre-feature per AC5.

## Suggested Review Order

**Scanner core (import resolution)**

- Entry point: over-approximates `from x import y` to also yield `x.y`, catching name-based/submodule-style forbidden imports (iteration 1's fix).
  [`test_architecture_boundaries.py:64`](../../tests/test_architecture_boundaries.py#L64)

- Relative-import resolution mirrors CPython's `__package__` semantics for both regular modules and `__init__.py` files.
  [`test_architecture_boundaries.py:53`](../../tests/test_architecture_boundaries.py#L53)

**The four boundary checks**

- `domain/`/`application/` reject `tkinter` and `labyrinthes.adapters*` — the core AD-1/AD-9 gate.
  [`test_architecture_boundaries.py:119`](../../tests/test_architecture_boundaries.py#L119)

- Storage-import check now scans all four `adapters/tkinter/` subpackages including `common/` (iteration 2's fix — this exact loop previously silently excluded `common/`).
  [`test_architecture_boundaries.py:146`](../../tests/test_architecture_boundaries.py#L146)

- The three screens never import each other directly.
  [`test_architecture_boundaries.py:129`](../../tests/test_architecture_boundaries.py#L129)

- `common/` never imports any of the three screens (one-way toolkit dependency).
  [`test_architecture_boundaries.py:139`](../../tests/test_architecture_boundaries.py#L139)

**Regression coverage & tooling**

- Fixture-based tests pin the scanner's own resolution logic against synthetic violations, so a future resolution bug fails loudly instead of the boundary tests trivially passing pre-feature.
  [`test_architecture_boundaries_scanner.py:29`](../../tests/test_architecture_boundaries_scanner.py#L29)

- `pythonpath` config fix so plain `pytest` (not only `python -m pytest`) can resolve the scanner-fixture file's cross-module import.
  [`pyproject.toml:30`](../../pyproject.toml#L30)
