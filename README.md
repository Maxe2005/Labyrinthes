# Labyrinthes

A maze editor and game: design mazes cell by cell (walls encoded as `0`/`1`/`2`/`3`), then solve them with levels, difficulty settings, and a timer.

This is a long-running learning project, currently being rewritten from scratch on the `rewrite` branch into a clean, modular, tested codebase. See [`CLAUDE.md`](CLAUDE.md) for the full architecture notes (legacy and rewrite), and [`_bmad-output/planning-artifacts/prds/`](_bmad-output/planning-artifacts/prds/) for the product requirements driving the rewrite.

## Setup (rewrite branch)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e . --group dev
```

```bash
ruff check .            # lint
ruff format .           # format
pytest                  # run tests
```

## Running the legacy apps (`main` branch, reference only)

```bash
pip install pillow

python3 Creer_labyrinthes.py   # maze editor ("builder")
python3 Labyrinthes_copy.py    # maze game ("player")
```

## BMad Method tooling

This repo uses [BMad Method](https://github.com/bmad-code-org) (installed version `6.10.0`, see `_bmad/_config/manifest.yaml` history in git for the exact module set once reinstalled) for planning workflows (PRD, architecture, epics/stories) surfaced as Claude Code skills. The installed tooling itself — `.claude/skills/` and `_bmad/` — is gitignored: it's regenerable third-party install output, not project source. Only what it *produces* (`_bmad-output/`) is committed.

To get the skills back after cloning:

```bash
npx bmad-method install
```

Point the installer at this repo root and select the same modules the project already uses: `core`, `bmm` (BMad Method), `bmad-loop`, `tea` (Test Architecture Enterprise), `bmb` (BMad Builder), `cis` (Creative Intelligence Suite), `gds` (Game Dev Studio), `wds` (Web Design Studio), with the Claude Code IDE integration. Re-running the installer is safe — `_bmad/config.toml` and `_bmad/config.user.toml` are installer-managed and get regenerated from your answers each time.
