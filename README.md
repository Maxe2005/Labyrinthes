# Labyrinthes

A maze editor and game: design mazes cell by cell (walls encoded as `0`/`1`/`2`/`3`), then solve them with levels, difficulty settings, and a timer.

This is a long-running learning project, currently being rewritten from scratch on the `rewrite` branch into a clean, modular, tested codebase. See [`CLAUDE.md`](CLAUDE.md) for the full architecture notes (legacy and rewrite), and [`_bmad-output/planning-artifacts/prds/`](_bmad-output/planning-artifacts/prds/) for the product requirements driving the rewrite.

## Setup (rewrite branch)

```bash
python3 -m venv .venv --upgrade-deps
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


# Possible new ideas

## maze generation :
### different maze generation algorithms :
chose between different maze generation algorithms and their parameters.
#### division method
So I hit on the following algorithm. It’s not really anything new—just recursive subdivision with a different rule for splitting regions in half—but the results are much more promising.

1. Collect all the cells in the maze into a single region.

2. Split the region into two, using the following process:
    2.1 Choose two cells from the region at random as “seeds”. Identify one as subregion A and one as subregion B. Put them into a set S.
    2.2 Choose a cell at random from S. Remove it from the set.
    2.3 For each of that cell’s neighbors, if the neighbor is not already associated with a subregion, add it to S, and associate it with the same subregion as the cell itself.
    2.4 Repeat 2.2 and 2.3 until the entire region has been split into two.

3. Construct a wall between the two regions by identifying cells in one region that have neighbors in the other region. Leave a gap by omitting the wall from one such cell pair.

4. Repeat 2 and 3 for each subregion, recursively.

### visualization of the maze generation process
we can chose before the maze generation process to visualize the maze generation process or not. If we chose to visualize it, we can chose the speed of the visualization in live (slow, medium, fast) and stop at any time.

## maze solving :
### different maze solving algorithms :
chose between different maze solving algorithms and their parameters.

