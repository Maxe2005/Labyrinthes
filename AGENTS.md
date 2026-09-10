<!-- bmad:context -->
<!-- Verified 2026-09-03 against 9ff760a. Managed by bmad-project-context; edits inside this block are replaced on refresh. Keep anything you want preserved outside the markers. -->

## Labyrinthes

Two French-language Tkinter desktop apps (maze editor + maze game), being rewritten from scratch under `src/labyrinthes/`. Two live branches: `rewrite` (active, all new work happens here) and `main` (legacy monoliths, read-only reference — and the repo's actual default branch on the remote, per `origin/HEAD`). `CLAUDE.md` is the authoritative architecture/workflow doc; read it for anything beyond this block. Planning artifacts live under `_bmad-output/`.

## Policy

- Check `git branch --show-current` before editing anything — `main` and `rewrite` have very different purposes (see above).
- Never edit or lint `main`'s legacy monoliths (`Creer_labyrinthes.py`, `Labyrinthes_copy.py`, `Autres/`) — read-only reference; they're excluded from `ruff` via `extend-exclude`.
- Never commit directly to an epic branch — every story gets its own branch off the epic.
- Conventional Commits in English, atomic per logical unit, with the story number in the subject line — e.g. `feat(domain): add Cell value object (story 1.1)`.
- Never merge a story into its epic before code review is done on the story branch (`review` → `done` in `sprint-status.yaml`).
- Epic branches accumulate stories and live until every story in them is `done` — never merge an epic into `rewrite` just because one of its stories is done, and only via a pull request even then (full detail in `CLAUDE.md` § Git workflow).
- `bmad-loop`'s merge commits (`Merge bmad-loop/<run>/<story> …`) are orchestration history — leave them as-is.
- `.claude/skills/`, `_bmad/`, `.bmad-loop/runs|cache` are gitignored, regenerable BMad install output — never commit them; only `_bmad-output/` (what BMad produces) is committed. Restore skills after a fresh clone with `npx bmad-method install`.

## Where things are

- Entry point: `src/labyrinthes/app/__main__.py` → `app/composition_root.py`.
- Layers: `domain/` (pure logic), `application/` (services + repository ports), `adapters/storage/` (CSV/JSON persistence), `adapters/tkinter/` (`home/`, `builder/`, `player/`, `common/`), `app/` (composition root, router, theme controller).
- Import boundaries are machine-checked by `tests/test_architecture_boundaries.py` (AST-based, runs on every `pytest`): `domain/`/`application/` never import `tkinter` or `adapters/`; the three screens never import each other; `adapters/tkinter/` never imports `adapters/storage/` directly.
- Planning sources of truth: PRD at `_bmad-output/planning-artifacts/prds/prd-Labyrinthes-2026-08-04/`, architecture spine at `.../architecture/architecture-Labyrinthes-2026-08-04/ARCHITECTURE-SPINE.md`, epics/stories at `_bmad-output/planning-artifacts/epics.md`, task records under `_bmad-output/implementation-artifacts/`.

## Running and verifying

- `make help` lists every target; verification order after a change is `ruff check .` → `ruff format --check .` → `pytest`.
- GUI tests (`tests/adapters/tkinter/`) open real `Tk()` windows via the `tk_root` fixture — they need a working X display and fail headless without `xvfb`.

## Conventions that differ from defaults

- On `rewrite`, code, identifiers, comments, UI strings, docs, and on-disk data are all English, even though the legacy `main` tree is French — don't carry that style forward.
- Maze cell walls stay digit-encoded (`0`/`1`/`2`/`3`, language-independent) through the English migration — never localize the encoding itself.

## Known pitfalls

- Some focus-dependent GUI tests (e.g. `test_gameplay_screen.py::test_move_is_a_no_op_while_focus_is_on_a_non_entry_widget_in_another_toplevel`) are flaky in a full-suite run but pass in isolation — re-run the single test alone before assuming a regression.

<!-- /bmad:context -->
