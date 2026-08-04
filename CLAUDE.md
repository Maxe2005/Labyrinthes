# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Two French-language Tkinter desktop apps for maze ("labyrinthe") generation and solving:

- **`Creer_labyrinthes.py`** ("builder") — lets the user design/edit mazes on a grid and save them.
- **`Labyrinthes_copy.py`** ("player" / "parcoureur") — lets the user navigate a ball through classic mazes or randomly generated ones, with levels, difficulty settings, and a timer.

This is a long-running learning project: code quality and conventions vary a lot between older and newer parts, since it evolved alongside the author's Python skills.

The `main` branch holds that original, unmodularized code as-is (no build system, no dependency manifest, no linter, no tests) — treat it as read-only reference for behavior/logic, not a base to extend. The **`rewrite` branch is the active branch**: a from-scratch, modular reimplementation built incrementally under `src/labyrinthes/`, with proper tooling from the start. New feature work happens there. See "Rewrite branch (active development)" below for the workflow, and "Legacy implementation (reference only)" for how the original apps are structured, since that's what the rewrite is porting logic from.

## Rewrite branch (active development)

Setup (once):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e . --group dev
```

Common commands:

```bash
ruff check .            # lint
ruff format .           # format
pytest                  # run tests
```

Tooling: `ruff` (lint + format, config in `pyproject.toml`) and `pytest`. The package lives under `src/labyrinthes/` (src-layout, installed editable); tests live under `tests/` and mirror the package layout. `ruff` is configured to exclude the legacy monolith files/`Autres/` — they're kept for reference and are not part of the code being linted or ported yet.

Approach: port functionality from the legacy monoliths incrementally, one module/feature at a time, rather than a big-bang rewrite. Prefer small, focused modules over recreating the "one giant class owns everything" pattern described below — that pattern is exactly what this rewrite is meant to replace.

Note: there is also an older `refonte` branch (mirrored as `origin/refonte-labyrinthes`) from an earlier rewrite attempt, which split the code into `src/Create_labyrinthe/`/`src/Labyrinthes/` and extracted shared widgets into an external `Outils_Tkinter` package. It has no tooling (no ruff/pytest/pyproject) and is unrelated to the `rewrite` branch — useful as prior art on the desired module split, not as a base to merge from.

## Legacy implementation (reference only)

The following describes `Creer_labyrinthes.py` / `Labyrinthes_copy.py` / `Autres/` on `main`, useful when porting a feature to `src/labyrinthes/` on the `rewrite` branch.

### Running the legacy apps

The only external dependency is Pillow (`PIL`), used for logo/image handling in the builder. Everything else is stdlib (`tkinter`).

```bash
pip install pillow

# Run the builder (maze editor)
python3 Creer_labyrinthes.py

# Run the player (maze game)
python3 Labyrinthes_copy.py
```

Each entry point can also launch the other at runtime (see "Builder ↔ Player linkage" below), so from the builder you can open the player and vice versa without restarting.

There is no test suite for the legacy code. `Autres/test_texte.py` is a standalone manual scratch script (imports `Creer_labyrinthes` and opens a Tk window with sample buttons) — it is not a pytest file and isn't run automatically.

### Architecture

#### The "Entité supérieure" pattern

Both monoliths follow the same composition-root pattern: a single top-level class owns all the major subsystems and wires them together by hand:

- `Entite_superieure_crea` (builder, in `Creer_labyrinthes.py`) owns `fenetre` (window), `grille` (grid/model), `canvas` (rendering), `balle` (the cursor/ball entity).
- `Entite_superieure` (player, in `Labyrinthes_copy.py`) owns the same four, plus `niveau` (`Niveaux`) and `difficultee` (`Difficultee`).

Wiring happens in two passes: subsystems are constructed in `__init__`, then each is given references to its siblings via an `init_entitees(...)` call, since they're mutually dependent (e.g. the canvas needs the grille and balle, the grille needs the canvas and balle). When adding a new subsystem, follow this same construct-then-inject pattern rather than reaching into `self.big_boss` chains mid-`__init__`.

Almost every widget/subsystem class keeps a `big_boss` (or `boss`) reference back up to the owning `Entite_superieure*`, which is how deeply nested UI code reads/writes shared state like `self.parametres`, `self.mode_actif`, or `self.commentaires`. There's no event bus or observer pattern — cross-component communication is direct method calls through these back-references.

#### Builder ↔ Player linkage

The two apps can launch each other from a running session:

- `Creer_labyrinthes.py`'s `lancement_parcoureur_labs()` lazily imports `Labyrinthes_copy` and instantiates `Entite_superieure(self)`, passing itself in as `Parcoureur_labs`'s `Lab_builtder`.
- `Labyrinthes_copy.py`'s `lancement_builder_labs()` does the mirror image, importing `Creer_labyrinthes` and passing itself as `Parcoureur_labs`.

The cross-imports are guarded by `if __name__ == "__main__"` at module level specifically to avoid an import cycle when one module imports the other — keep that guard if you touch either entry point.

#### Shared UI toolkit (`Autres/Outils.py`)

Reusable Tkinter building blocks used by both apps:

- `Boutons` — a button/combobox factory+registry (`def_bouton`, `afficher`/`cacher`, `renommer`) used instead of placing raw `tk.Button`s, so buttons can be shown/hidden/resized as a group.
- `Commentaire` — a hover-tooltip `Toplevel` attached to a widget, with auto-positioning logic that tries several sides (`L`/`B`/`R`/`T`) to stay on-screen.
- `Reglages` / `Base_Reglages` — a generic scrollable "settings" window and the base class each settings-panel subclasses (see `Reglages_lab_alea`, `Reglages_apparence`, `Reglages_balle`, etc. in `Labyrinthes_copy.py`, and `Reglages_generaux_crea` in `Creer_labyrinthes.py`).

`Autres/Labyrinthes.py` is a legacy standalone version of the player predating `Labyrinthes_copy.py`/`Autres/Outils.py` split — it is not imported by anything and is effectively dead code kept for reference.

#### Settings persistence

`Autres/Parametres_defaut.csv` stores all default settings as `entité,nom,valeur` rows (entité is `builder` or `parcoureur`). `Entite_superieure_crea.ouvrir_param_defaut()`/`save_param_defaut()` read/write this file on startup/`on_closing`; values that are lists are comma-joined. There's no schema validation — column order and the `entité` tag are load-bearing.

#### Maze/save data layout

Maze data is stored as plain CSV under dedicated top-level folders, each with a `#_Doc_index.csv` listing the saved items:

- `Labyrinthes_classiques/` — hand-built "classic" mazes shipped with the game (one file per maze; first line is start coords, second is grid size, remaining lines encode cell walls).
- `Labyrinthes_creation/` — work in progress from the builder.
- `Labyrinthes_croquis/` — incomplete "sketch" saves that can be reopened for editing.
- `Labyrinthes_aléatoires_enregistrés/` — saved random mazes.

#### Language and naming

Code, identifiers, comments, and UI strings are in French throughout (`grille`, `balle`, `fenetre`, `parcoureur`, `réglages`, `Aller à`, etc.). Keep this convention when porting logic to `src/labyrinthes/` — identifiers and UI text should stay French, only the project's structure/tooling is being modernized.

## Known repo debt to be aware of (legacy code, `main`)

- On `main`, compiled `__pycache__/*.pyc` files are tracked in git (no `.gitignore` there) — don't be surprised by them showing as modified if you check out that branch.
- Some data folders/index files use non-ASCII names (`Labyrinthes_aléatoires_enregistrés`, `Idées LOGO`) — be careful with path handling/encoding when scripting against them.
