# AGENTS.md

## Repository layout & which branch to work on

Two live branches, different purposes — check `git branch --show-current` before touching anything:

- **`rewrite` (ACTIVE, default HEAD)** — modular, tested reimplementation under `src/labyrinthes/`. All new work happens here. Only this tree is linted/type-checked/tested.
- **`main`** — legacy French Tkinter monoliths (`Creer_labyrinthes.py`, `Labyrinthes_copy.py`, `Autres/`). Read-only reference for behavior/logic. **Never edit or lint them.** They are excluded from `ruff` via `extend-exclude` in `pyproject.toml`; the old `refonte` branch is unrelated prior art.

`CLAUDE.md` is the authoritative architecture/workflow doc (legacy + rewrite); it is thorough — read it for details beyond this file.

## Setup & commands

```bash
python3 -m venv .venv --upgrade-deps
source .venv/bin/activate
pip install -e . --group dev      # editable install + dev group (ruff, pytest)
```

| Task | Command |
|---|---|
| lint | `ruff check .` |
| format | `ruff format .` (check-only: `ruff format --check .`) |
| test (all) | `pytest` |
| test (one file/module) | `pytest tests/domain/test_cell.py` |
| test (one test) | `pytest tests/domain/test_cell.py::test_name` |
| run the app | `python -m labyrinthes.app` |

Equivalent `make` targets exist (`make lint`, `make test`, `make run`, …). Verification order after a change: `ruff check .` → `ruff format --check .` → `pytest`.

## Architecture (rewrite)

Clean-layered, under `src/labyrinthes/`; entry point is `app/__main__.py` → `app/composition_root.py`:

- `domain/` — pure business logic (grid, cell, maze, movement, generation). No `tkinter`, no adapters.
- `application/` — services + port interfaces (maze/settings repositories). No `tkinter`, no adapters.
- `adapters/storage/` — CSV/JSON persistence implementations of the ports.
- `adapters/tkinter/` — UI, split into `home/`, `builder/`, `player/` screens plus shared `common/` widgets.
- `app/` — composition root, router (screen navigation), theme controller.

**Import boundaries are machine-checked** by an AST-based test (`tests/test_architecture_boundaries.py`, runs on every `pytest`, doesn't import the scanned modules):

- `domain/` and `application/` must not import `tkinter` or anything from `adapters/`.
- The three screens (`home`, `builder`, `player`) never import each other; `common/` never imports any screen.
- The whole `adapters/tkinter/` tree never imports `adapters/storage/` directly — persistence access always goes through an `application/` service.

## Testing quirks

- GUI tests (`tests/adapters/tkinter/`) create **real `Tk()` windows** via the `tk_root` fixture (see `tests/conftest.py`) — they require a working X display; they fail headless (no `xvfb`). Machine-specific note: the working tree here can be set up for it.
- Some focus-dependent GUI tests (e.g. `test_gameplay_screen.py::test_move_is_a_no_op_while_focus_is_on_a_non_entry_widget_in_another_toplevel`) are flaky in a full-suite run but pass in isolation. Re-run a single failing GUI test alone before assuming a regression.
- `pyproject.toml` sets `pythonpath = ["."]` so the boundary scanner test can import its sibling under plain `pytest`.

## Language conventions

- On `rewrite`: code, identifiers, comments, UI strings, docs, and on-disk data are all **English**. Only conversation with the user stays French. The legacy `main` tree is French — don't copy that style forward.
- Maze cell wall encoding is digits `0`/`1`/`2`/`3` (language-independent) and must be preserved as-is; legacy save files need migration to the English layout (see PRD).
- `ruff`: line-length 100, target `py312`, rules `E, F, I, UP, B, SIM`. No comments unless asked.

## Git workflow

Strict, story-driven convention (full detail in `CLAUDE.md` "Git workflow"):

- One **epic branch** from `rewrite` (named after the epic in `_bmad-output/planning-artifacts/epics.md`); one **story branch** from that epic (named after its sprint-status key). Never commit directly to an epic branch.
- Atomic commits, Conventional Commits **in English**, with the story number in the subject line (e.g. `feat(domain): add Cell value object with wall-bit decoding (story 1.1)`).
- Story → epic via `git merge --no-ff`; epic → `rewrite` only via pull request.
- `bmad-loop` automates story dev/review/merge in gitignored worktrees; its merge commits (`Merge bmad-loop/<run>/<story> …`) are orchestration history — leave them as-is.

## BMad planning artifacts

- `.claude/skills/`, `_bmad/`, `.bmad-loop/runs|cache` are gitignored, regenerable third-party install output — do not commit them. Only what BMad **produces** (`_bmad-output/`) is committed.
- Planning sources of truth: PRD at `_bmad-output/planning-artifacts/prds/prd-Labyrinthes-2026-08-04/`, architecture spine at `.../architecture/architecture-Labyrinthes-2026-08-04/ARCHITECTURE-SPINE.md`, story/epic breakdown at `_bmad-output/planning-artifacts/epics.md`, implementation/task records under `_bmad-output/implementation-artifacts/`.
- Restore the skills after a fresh clone with `npx bmad-method install` (see `README.md` for the module list).
