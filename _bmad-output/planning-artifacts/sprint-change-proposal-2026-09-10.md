# Sprint Change Proposal — Epic 5 scope reduction

**Date:** 2026-09-10
**Author:** Amelia (dev), with Max
**Mode:** Incremental
**Scope classification:** Moderate (PRD + Architecture + Epics + sprint tracking updated; no code written yet, no rollback needed)

## 1. Issue Summary

On re-reading Epic 5 (Legacy Data Migration to English) after Epic 4 landed, Max flagged that two of its three stories no longer earn their keep:

- **Story 5.1** (folder & file renaming) was scoped as if creating the new English-named folder layout were significant work. It isn't: `MazeKind.value` already names every folder, and both `write_maze_csv` and `write_setting_value` already create the destination folder (`path.parent.mkdir(parents=True, exist_ok=True)`) on every write. There's no dedicated "create 2 folders" task to do.
- **Story 5.2** (settings CSV header renaming) is hard to do meaningfully because not every legacy setting is even implemented yet in the rewrite, and migrating the handful that are isn't necessary.

Only **Story 5.3** (MazeId backfill) was judged to still carry real value, and Max asked for the epic to be trimmed down to it — refined using the code actually produced since the stories were written.

## 2. Impact Analysis

### Evidence gathered from the codebase

- `src/labyrinthes/adapters/storage/paths.py`: `DEFAULT_MAZES_ROOT`/`maze_file_path` already declare every `MazeKind` folder name; nothing left for a migration script to "invent."
- `src/labyrinthes/adapters/storage/csv_maze_format.py`: `write_maze_csv` creates the parent folder on every write and matches the **legacy line shape exactly** (entry line, exit line, grid rows) — confirmed against `Labyrinthes_copy.py::ouvrir_lab` (line 1 = `entrée_lab`, line 2 = `sortie_lab`, remaining = grid) and against a real file (`Labyrinthes_classiques/Labyrinthe classique 1`). The only structural difference is the new, additive `MazeId` line. **There is no content-format conversion to write** — a legacy file can be read with the legacy line order and re-written through `MazeRepository.save()` unchanged in shape.
- `src/labyrinthes/adapters/storage/csv_maze_repository.py`: `save()` already auto-mints a `MazeId` via `mint_maze_id()` for any `Maze` of an `ID_ELIGIBLE_KINDS` kind (`CLASSIC`, `SAVED_RANDOM`, `CREATION`) that doesn't have one yet — the backfill Max wants to keep is a *side effect of calling `save()` normally*, not a bespoke routine.
- `src/labyrinthes/adapters/storage/json_settings_repository.py` + `settings_format.py`: settings are now one **JSON file per `(scope, key)`**, not a single CSV with an `entité,nom,valeur` header. `get()` raises `SettingNotFoundError` on a missing file; every caller (`window_settings.py`, `defaults_settings.py`, etc.) falls back to a **hardcoded Python default** (e.g. `DEFAULT_WINDOW_WIDTH = 1280`), never to the legacy CSV. There is no live dependency on `Autres/Parametres_defaut.csv` anywhere in the rewrite — confirming Story 5.2 is not just low-value but technically moot.
- `CsvMazeRepository.list_names()` lists a kind's folder by globbing `*.csv` directly — the legacy per-folder `#_Doc_index.csv` has no equivalent in the new layout and was never going to be read by anything.

### Epic impact

Epic 5 collapses from three stories to one. No rollback is needed: `sprint-status.yaml` shows all three stories as `backlog` — none started.

### Artifact conflicts (now resolved by this proposal)

- **PRD** — FR-23 committed to converting "folder names, save file naming, and CSV headers (e.g. the `entité,nom,valeur` settings file)". Revised to drop the settings-file commitment and reflect that maze-file migration reuses `MazeRepository.save()` rather than a bespoke serializer.
- **PRD addendum** — the FR-23 naming-reference inventory listed `Autres/Parametres_defaut.csv` and the per-folder `#_Doc_index.csv` files as in scope. Both dropped, with a note explaining why.
- **Architecture spine (AD-8)** — referenced `entité,nom,valeur` header conversion and scoped MazeId backfill to "classic and saved-random" only. Revised to drop the settings-conversion clause and extend the backfill to all three `ID_ELIGIBLE_KINDS` (adding `creation`, which the domain code already treats as id-eligible but the epic text never mentioned).
- **Epics.md** — Epic 5's description and its three stories (5.1/5.2/5.3) replaced by a single, renumbered Story 5.1 that merges 5.1's file-relocation intent with 5.3's MazeId-backfill mechanism, informed by the code evidence above.
- **sprint-status.yaml** — `5-1-migration-script-folder-file-renaming`, `5-2-migration-script-settings-csv-header-renaming`, `5-3-migration-script-mazeid-backfill` replaced by a single `5-1-migration-script-legacy-maze-data-mazeid-backfill` (all `backlog`).

No UX-spec impact (Epic 5 has no UI surface). No PRD MVP impact — legacy migration is a one-time housekeeping task for the author's own data, not a user-facing MVP feature; FR-23 stays satisfied, just narrower.

### Incidental finding (not fixed by this proposal)

AD-3's `Maze` domain-object description (architecture spine, line 77) still says `MazeId` is "present only for `classic`/`saved-random` mazes" and lists the kind tag as `classic | sketch | saved-random | generated` — it never mentions `creation`, even though `domain/maze.py`'s `ID_ELIGIBLE_KINDS` already includes it (added later, likely alongside Story 4.11's "classic vs creation maze kind"). This proposal's AD-8 edit now correctly cites `ID_ELIGIBLE_KINDS` for the migration's `creation` handling, but AD-3's own prose remains out of date. Flagging for a future small doc-fix — out of scope here since it predates and is independent of the Epic 5 correction.

## 3. Recommended Approach

**Direct Adjustment (Option 1).** No stories are rolled back (none started), and the MVP is unaffected. Trim Epic 5 to a single, better-informed story and update the four planning artifacts that referenced the dropped scope, so they don't drift from what will actually be built.

- Effort: Low (documentation-only change; no code yet).
- Risk: Low — verified against the actual implementation, not just re-read intent.

## 4. Detailed Change Proposals

All five edits below were presented to Max and approved as-is.

### 4.1 `epics.md` — Epic 5

Replaced the epic description and its three stories with one merged, renumbered Story 5.1 ("Migration script — legacy maze data to new layout with MazeId backfill"). See diff applied to `_bmad-output/planning-artifacts/epics.md`.

### 4.2 PRD — FR-23

Reworded to drop the settings-file migration commitment and reflect the `MazeRepository.save()` reuse mechanism; extended the MazeId-backfill consequence to `creation` mazes. See diff applied to `_bmad-output/planning-artifacts/prds/prd-Labyrinthes-2026-08-04/prd.md`.

### 4.3 PRD addendum — FR-23 naming reference

Dropped the settings-file and index-file bullets from the inventory, with a note on why. See diff applied to `_bmad-output/planning-artifacts/prds/prd-Labyrinthes-2026-08-04/addendum.md`.

### 4.4 Architecture spine — AD-8

Dropped the settings-header conversion clause, extended MazeId backfill to all three `ID_ELIGIBLE_KINDS`, and noted that index files aren't migrated. See diff applied to `_bmad-output/planning-artifacts/architecture/architecture-Labyrinthes-2026-08-04/ARCHITECTURE-SPINE.md`.

### 4.5 `sprint-status.yaml`

Replaced the three `5-*` backlog entries with a single renumbered `5-1-migration-script-legacy-maze-data-mazeid-backfill: backlog`.

## 5. Implementation Handoff

- **Scope:** Moderate — backlog/documentation reorganization, no code changes required by this proposal itself.
- **Applied by:** Amelia (dev), in this session, with Max's explicit approval of every edit.
- **Next steps for whoever picks up Story 5.1:** write the migration script per the refined acceptance criteria in `epics.md` — read each legacy maze file with the legacy line order, call `MazeRepository.save()` (never a bespoke writer), skip the dropped `#_Doc_index.csv` files, and verify every migrated classic/saved-random/creation maze reloads with a non-`None` id.
- **Success criteria:** `epics.md`, PRD, PRD addendum, architecture spine, and `sprint-status.yaml` all agree on a single Story 5.1 with no dangling references to settings-file migration or index-file renaming.
