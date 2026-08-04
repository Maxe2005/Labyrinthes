# Addendum — Labyrinthes — Modular Rewrite

Reference material extracted from the legacy code during PRD Discovery, too detailed to live in the PRD itself. Consult during architecture and epics/stories work.

## Detailed inventory — Builder (`Creer_labyrinthes.py`)

### Cell-encoding scheme (0/1/2/3) — the engine's core
Each cell is a `"0"`/`"1"`/`"2"`/`"3"` string: bit 1 = top wall, bit 2 = left wall, `3` = both. The grid has one extra column and row (closed border) to seal the right/bottom edges (`grille_pleine`). Editing functions (`fleches`, `detruire_aire`, `restorer_aire`, `sortie_end`) manipulate these codes directly via lookup tables (`conbinaisons = ["1","3","0","2"]`). The lookup table and the CSV save format must be preserved strictly (naming aside — see FR-23).

### Identified debt (not to be reproduced)
- **Broken, dead `aller_a_coord`**: call commented out (`#self.aller_a_coord()`), never wired to any button, uses `tk.simpledialog` while `tkinter.simpledialog` is never imported in the file → would raise `AttributeError` if ever invoked.
- **Disabled "Open the Player" button** (`state='disabled', bg="grey"`) in `Fen_infos_generales` — backend logic ready (`lancement_parcoureur_labs`) but no UI access.
- **Duplicated size bounds**: min/max columns/rows (3–50, 3–35) hardcoded in the UI (`Fen_chose_new_lab`) while equivalent `parcoureur` settings already exist in the CSV — no single source of truth.
- **Misplaced setting**: the "Alert on invalid input" checkbox (random maze) appears in the *builder's* general settings even though it only concerns the *player* — inherited from the shared `Outils.Reglages` component.
- **Minor integration bug**: `Modifier lab` uses `messagebox.askquestion` (Yes/No) for a plain info message, showing unnecessary buttons.
- **Partial dead code**: `coutours_compris_dans_detruire_aire`/`restorer_aire` are always `False`, never exposed in the UI.
- **Unprotected write**: `save_param_defaut` rewrites the entire settings file (builder + player) on close — no protection against concurrent access if both apps run in parallel (underlies FR-21).
- **Empirical workaround**: startup resizing via three repeated `self.fenetre.after(500+(i*100), redimentionner)` calls — likely a patch for a startup size-calculation issue.

### Data-contract files (legacy names — to be renamed under FR-23)
`Labyrinthes_croquis/Croquis__*.csv`, `Labyrinthes_creation/Labyrinthe__*.csv` (Entry/Exit + 0/1/2/3 grid format), `Autres/Parametres_defaut.csv` (`builder,...` rows).

## Detailed inventory — Game / Player (`Labyrinthes_copy.py`)

### Encoding scheme, reused for gameplay
Same encoding as the Builder. Read/written in `Laby_grille` (`grille_pleine`, `ouvrir_lab`, `generateur_lab`, `decompte_nb_murs_dans_lab`) and interpreted for movement in `Laby_balle.ou_aller` (direct string comparisons against `"1"`/`"2"`/`"3"`). Levels 2-4 and Difficulty all derive from that same array (partitioning, wall counting) — no separate abstraction layer in the legacy code.

### Level detail
- **Level 1**: normal, everything visible.
- **Level 2**: the maze is split into rectangular partitions; each visited partition stays shown, but past a reveal threshold (depends on Difficulty), everything hides again (`Position_joueur_sur_back_lab_partition`).
- **Level 3**: only one partition visible at a time.
- **Level 4**: walls invisible until collision; past a threshold of discovered walls, they all hide again (`test_nb_murs_niv_4`).
- **Level Max**: all walls permanently invisible.
- **Identified inconsistency (underlies FR-13)**: the reveal-threshold calculation differs between Level 2 (`count > round(lab_xx*lab_yy/(difficultee+1))`) and Level 4 (fixed division `/2, /5, /10` by Difficulty) — two different formulas for a similar concept.

### Identified debt and bugs (underlying the fixes in PRD §4.2-4.4)
- **Dead-end random-maze save** (`sauvegarder_lab_alea`, writes into `Labyrinthes aléatoires enregistrés/`): nothing in the player reloads/lists these files afterward — the folder isn't even present in the current repo, never used in practice (underlies FR-11).
- **Disabled timer**: the `Chrono` class is complete (start/stop/reset, time limit) but its instantiation and label update are commented out — 100% disabled in shipped code (underlies FR-16).
- **Ghost `reglages_lab_alea`**: `Laby_grille.reglages_lab_alea` is an empty stub (`def reglages_lab_alea(self): return`), never called, superseded by `Reglages_lab_alea` — dead code, not to be reimplemented.
- **Hardcoded HARD-mode color**: `Laby_balle.mouve` fires `change_voyant_mode_hard("ready", "blue")` with `"blue"` hardcoded, while the actual "moving" state color is configurable via the CSV (`colors mode hard moving`) — if the user changes that color, the return-to-"ready" toggle breaks silently (underlies FR-14).
- **`r` keyboard-shortcut collision**: bound first to "Settings" (`init_boutons_barre_laterale_droite`), then overwritten for "Restart" (`init_boutons_barre_top_right`). The Settings button's tooltip still claims "(shortcut: 'r')" while that shortcut actually triggers "Restart" (underlies FR-22).
- **One-way Player → Builder link**: the "Open the Builder" button is disabled in `Fen_infos_generales` when the player is launched standalone; launching the builder only wires up when the player was itself opened from the builder (depends on `__name__ == "__main__"`) (underlies FR-19).
- **Unprotected write**: `Entite_superieure.on_closing` rewrites the entire settings CSV on close, with no schema validation or protection against concurrent access (same defect as the builder, underlies FR-21).

### Mature features, no issue identified
Classic maze selection (previous/next/restart/jump to a number), random maze generation (DFS/backtracking-style algorithm, exit = cell farthest from the entry), two movement modes (Smooth/Discrete) with configurable speed, color theme + logo selection, per-action confirmation prompts, main info bar, maze-completion popup.

## New-mode ideas (FR-24, FR-25) — raw capture, to be refined

- **Water Chase**: water falls from the top of the maze and naturally flows downward, progressively filling cells. Several difficulty tiers based on an allowed underwater breath time (in number of cells or in elapsed time) before the solve fails. Implementation lead to explore later: the fill mechanic could reuse the same grid partitioning (0/1/2/3) already used by Levels.
- **Exploration**: several mazes chained together on a 2D map, with optional narration, and collectible items (e.g. keys) scattered across the different mazes to progress toward the end of the exploration.

Low priority, explicitly confirmed by the author — to be tackled after the existing features are fully ported. More ideas are expected as the rewrite progresses; the PRD stays a living document on this point (see PRD §9).

## Legacy-to-English data migration (FR-23) — naming reference

Existing legacy paths/headers and their role, to inform the migration script/shim decision (PRD §8, Open Question 4):

- `Labyrinthes_classiques/` — hand-built classic mazes shipped with the game.
- `Labyrinthes_creation/` — work in progress from the builder.
- `Labyrinthes_croquis/` — incomplete sketch saves.
- `Labyrinthes_aléatoires_enregistrés/` — saved random mazes (currently unused in practice, see FR-11).
- `Autres/Parametres_defaut.csv` — settings file, header `entité,nom,valeur`, `entité` value `builder` or `parcoureur`.
- Per-folder `#_Doc_index.csv` files listing saved items.

None of this affects the 0/1/2/3 cell-encoding values themselves — migration is a renaming/restructuring concern, not a re-encoding one.
