---
title: 'Story 2.7: Difficulty — unified threshold formula'
type: 'feature'
created: '2026-08-14'
status: 'done'
baseline_commit: 'd716269'
review_loop_iteration: 1
followup_review_recommended: false
context: ['_bmad-output/implementation-artifacts/epic-2/epic-2-context.md']
baseline_revision: 'd716269'
---

# Story 2.7: Difficulty — unified threshold formula

Status: done

## Story

As a player,
I want a Difficulty setting (1–3, unlockable from Level 2 onward) that adjusts the partition size/reveal thresholds Levels use,
so that the challenge scales consistently regardless of which Level I'm on.

## Acceptance Criteria

1. **Given** Level 1 is selected, **when** the Difficulty control is checked, **then** it is disabled, per the unlockable-from-Level-2 rule.
2. **Given** Level 2 or higher, **when** Difficulty 1/2/3 is selected, **then** the reveal-threshold calculation applies a single shared formula, used identically by Level 2's and Level 4's mechanics (fixing the legacy inconsistency).
3. **Given** a Difficulty change mid-session, **when** applied, **then** the active Level's visibility recalculates using the new threshold immediately.

## Intent Contract

### Problem

Story 2.6 parameterized the visibility engine by `Difficulty` (`partition_size_for_difficulty`, `reveal_threshold`, and a session `difficulty` field defaulting to `Difficulty.ONE`) but shipped **no Difficulty control**: the HUD Difficulty chip still shows the Story 2.4/2.6 placeholder `"—"`, the sidebar has no Difficulty group, the control is not gated behind the "unlockable from Level 2 onward" rule (FR-13), and there is no session operation to change Difficulty mid-run. The legacy app's two divergent threshold formulas (Level 2 `count > round(lab_xx*lab_yy/(difficultee+1))` vs Level 4 fixed `/2,/5,/10` division) are already unified in the engine's single `reveal_threshold`, but that function is spec-pinned as a *placeholder* for this story to finalize (two deferred-work items from Story 2.6's review).

### Approach

Wire the Difficulty control end-to-end on the session and the gameplay screen, and finalize the single shared threshold formula:

- **Application:** add `set_difficulty(session, difficulty) -> PlayerSession` in `application/player_session.py`, mirroring `set_level` exactly: a no-op once solved; otherwise `replace(session, difficulty=difficulty, visibility=initial_level_visibility(session.maze, session.level, difficulty, session.position))` — visibility recomputes from the ball's current cell with the new partition sizing/threshold, everything else (position, elapsed, mode, speed, in-flight leg) preserved. This is the AC-3 mechanism: an identity change on `session.visibility` makes the screen redraw under the new Difficulty without restarting the run.
- **Screen:** add a "Difficulty" sidebar group mirroring the "Levels" group (Story 2.6): a `−` `ToolButton`, a monospace value label (`TYPOGRAPHY.hud_stat`), and a `+` `ToolButton`, cycling `Difficulty.ONE→TWO→THREE→ONE` with wraparound (matching legacy `Difficultee.plus`/`moins`), Tab+Enter/Space-operable with **no global shortcut** (the level/speed precedents), sharing the toplevel focus guard. Replace the `_PLACEHOLDER_DIFFICULTY = "—"` HUD chip with a real chip fed from `session.difficulty`. Sync both the chip and the sidebar value on every change and on level changes (so a level cycle re-evaluates the control's enabled state).
- **Level-1-disable gating (AC-1):** the Difficulty controls are disabled whenever `session.level is Level.ONE` (and, faithful to the legacy `Niveau_max` gate, at `Level.MAX` too — see Design Notes). This needs a genuine disabled state on `ToolButton`, which has none today: add `ToolButton.set_enabled(enabled: bool)` to the shared `common/` toolkit — disabled buttons are non-focusable (`takefocus=False`), ignore clicks/Enter/Space, and render in the `colors.ghost` palette (the design system's "disabled or not-yet-set state" token); re-enabling restores focusability, activation, and normal styling.
- **Formula finalization:** confirm `reveal_threshold(axis_counts, difficulty) = round(cols*rows/(difficulty+1))` as the final single shared formula and pin it with tests. Two review findings ground this (see Design Notes): the legacy code actually uses Python's built-in `round()` (banker's) — there is **no** `arrondi` helper anywhere in the shipped legacy tree — so `round(...)` is *faithful*, not divergent; and the unified `/(d+1)` at D1 equals legacy Level-4's `/2` exactly, so the "Level-4 degeneracy" flag is legacy-faithful behavior, not a regression. No domain formula change is required — the story finalizes and documents it.

## Boundaries & Constraints

**Always:** `adapters/tkinter/player/` never imports `adapters/storage/` directly (AD-9). All Difficulty visibility logic stays in `domain/` (pure) and `application/` (session orchestration); the screen only applies `set_difficulty` and reads the visibility object back (NFR1, AD-1..AD-3). Difficulty is **session-scoped, not persisted** — no new `SettingsRepository` keys, no `settings_keys.py` change (the epic context's game-scoped list — movement speed, confirmation toggles, HARD color, theme, logo, time-limit — has no Level/Difficulty entry; a fresh maze mount starts at `Difficulty.ONE`). The `GameplayScreen` `.after()` loops and toplevel focus guard stay intact — the new Difficulty buttons share the same guard. No new global keyboard shortcut (Tab-operable per NFR6; `m` is taken by the mode toggle, and there is no free single-letter convention to spend).

**Block If:** Nothing needs human input — the formula finalization, the Level-1/MAX disable gating, the session-scoped non-persistence, the chip always showing the difficulty value, the wraparound cycle, and the sidebar placement are all documented decisions below.

**Never:** No HARD-mode fog/status light (2.8), no timer/timeout (2.9), no confirmation prompts on Level/Difficulty change (2.10), no first-activation explainers (Epic 5 — but leave the Difficulty control's location/state in a shape that won't block later ⓘ-anchor wiring). No change to `composition_root.py`, `screen.py`, `settings_keys.py`, or `keybindings.py`. No new persisted setting. No change to `PlayerSession`'s existing `mode`/`speed`/leg fields or to `attempt_move`/`Duration`. No redraw on every animation sub-step — structure redraws only when the visibility object actually changes (a Difficulty change re-initializes it). Do **not** change the formula's meaning or add per-level threshold code — there is exactly one `reveal_threshold` and this story pins it, it does not redesign it.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Initial mount | Maze mounted, fresh session (`level=ONE`, `difficulty=ONE`) | Difficulty group renders with value `1`, disabled (non-focusable, ghost palette); HUD Difficulty chip shows `1` | No error |
| Level 1 selected | `_cycle_level` to `ONE` (or initial mount) | Difficulty controls disabled; a `−`/`+` click or Enter/Space is a no-op | No error |
| Level 2 selected | `_cycle_level` to `TWO` | Difficulty controls enabled; difficulty change allowed | No error |
| Difficulty change at Level 2/3 | `set_difficulty(TWO)` mid-session | `session.difficulty == TWO`; visibility re-initialized from the ball's current cell with the new partition sizing (e.g. 8×6: D1 → 3×3 partitions vs D2 → 2×2); identity change → canvas redraw | No error |
| Difficulty change at Level 4 | `set_difficulty(THREE)` | `total_interior_walls` unchanged but threshold recomputes to `round(total/(3+1))`; discovered-walls behavior uses the new threshold on the next collision/accumulation | No error |
| Difficulty wraparound | `+` at `THREE` / `−` at `ONE` | `THREE + 1 → ONE`; `ONE - 1 → THREE` (both directions wrap, matching legacy `plus`/`moins`) | No error |
| Difficulty change mid-leg | `set_difficulty` while a leg is in flight | In-flight leg geometry untouched (mirrors Story 2.5 mid-leg switch / Story 2.6 `set_level`); visibility resets fresh for the current ball cell; next commit re-applies | No error |
| Difficulty change after solve | `set_difficulty` with `solved=True` | No-op — returns the session unchanged (Story 2.5/2.6 convention) | No error |
| Level MAX selected | `_cycle_level` to `MAX` | Difficulty controls disabled (legacy `Niveau_max` parity — difficulty has no effect at MAX, which has no partitions/walls) | No error |
| Input while focus is in another toplevel | `−`/`+` clicked or activated while `SaveMazeDialog` has focus | No-op — Difficulty unchanged behind the dialog (shared toplevel focus guard) | No error |
| Screen destroyed mid-session | `.after()` jobs pending, Difficulty buttons present | Existing tick/animation cancellation + `bind_shortcut` cleanup on `<Destroy>` unchanged | No error |
| Disabled ToolButton receives focus attempt | `set_enabled(False)` then tab/click | No focus acquisition (`takefocus=False`), no activation, ghost rendering | No error |
| Disabled ToolButton re-enabled | `set_enabled(True)` after level leaves ONE/MAX | Focusability, activation, and normal styling restored | No error |

## Code Map

- `src/labyrinthes/application/player_session.py` — **UPDATE**:
  - `set_difficulty(session, difficulty) -> PlayerSession` — **NEW**, mirroring `set_level` (line 258): no-op once solved; otherwise `replace(session, difficulty=difficulty, visibility=initial_level_visibility(session.maze, session.level, difficulty, session.position))` — visibility recomputes from the current cell, everything else preserved. Update the module docstring and `__all__`.
  - No change to `start_session` (already defaults `difficulty=Difficulty.ONE`), `set_level` (already preserves `session.difficulty`), or the movement hooks.
- `src/labyrinthes/domain/level_visibility.py` — **finalize only**:
  - `reveal_threshold` stays `round(axis_cols * axis_rows / (difficulty + 1))` — the single shared formula applied to Level 2's partition count and Level 4's discovered-wall count. Update its docstring: drop the "Story 2.7 finalizes this function" placeholder wording and document the final decision (banker's `round()` is what legacy actually ships — see Design Notes). **No behavior change.**
- `src/labyrinthes/adapters/tkinter/common/tool_btn.py` — **UPDATE**:
  - `ToolButton.set_enabled(enabled: bool) -> None` — **NEW**: a real disabled state. `self._enabled` defaults `True` in `__init__`. When disabled: `takefocus=False`; `_on_click` returns early; `_on_focus_in`/`_on_focus_out` no-op (no ring); `_apply_style()` renders the disabled branch (background `colors.window`, border/text `colors.ghost`). When re-enabled: `takefocus=True`, activation and styling restored. Leave `ToolButtonGroup` untouched.
- `src/labyrinthes/adapters/tkinter/player/gameplay_screen.py` — **UPDATE**:
  - Replace `_PLACEHOLDER_DIFFICULTY = "—"` with a real chip fed from `session.difficulty`. Add `_DIFFICULTY_CYCLE: tuple[Difficulty, ...] = tuple(Difficulty)` and `_difficulty_label(difficulty) -> str` returning `str(difficulty.value)` (`"1"`/`"2"`/`"3"`).
  - Add a "Difficulty" sidebar group directly below the "Levels" group (mirroring the legacy `<-`/`Niveau`/`->` then `<-`/`Difficultée`/`->` triads): a `−` `ToolButton`, a monospace value label (`TYPOGRAPHY.hud_stat`), and a `+` `ToolButton`, wired to `functools.partial(self._cycle_difficulty, ±1)`. No shortcut.
  - `_cycle_difficulty(delta) -> None` — **NEW**: guard with `_toplevel_has_focus()`; if the control is currently disabled (Level ONE/MAX) return; compute the wrapped next `Difficulty` from `_DIFFICULTY_CYCLE`; `self._session = session_set_difficulty(self._session, next)`; then `_sync_difficulty_widgets()` and `_sync_visibility()` (the visibility identity change drives the redraw — AC-3).
  - `_sync_difficulty_widgets() -> None` — **NEW**: set the disabled state of the `−`/`+` buttons (and the value label's foreground) from `self._difficulty_enabled()`; update the HUD chip and the sidebar value label to `_difficulty_label(self._session.difficulty)`.
  - `_difficulty_enabled() -> bool` — **NEW**: `self._session.level not in (Level.ONE, Level.MAX)`.
  - `_cycle_level` — **UPDATE**: after syncing level widgets, call `_sync_difficulty_widgets()` so entering/exiting ONE (or MAX) re-evaluates the Difficulty control's enabled state.
  - Import `Difficulty` and alias `set_difficulty as session_set_difficulty` (matching the existing `session_set_*` import block). Keep the `session_set_difficulty` call a screen-side orchestration only.
- `tests/domain/test_level_visibility.py` — **UPDATE**: pin the finalized formula — explicit D1/D2/D3 threshold values for a known axis pair (e.g. `(3,2)` → `3`/`2`/`2` via `round(6/2)=3`, `round(6/3)=2`, `round(6/4)=2` — the last is banker's rounding, `round(1.5)==2`) and a Level-4-style `(total, 1)` pair, plus a comment-backed assertion that Level 2 and Level 4 share this one function (they already call the same `reveal_threshold`).
- `tests/application/test_player_session.py` — **UPDATE**: `set_difficulty` replaces difficulty and re-initializes visibility at the current position; preserves position/elapsed/mode/speed; preserves an in-flight leg; no-op once solved. Mirror the existing `set_level` tests.
- `tests/adapters/tkinter/common/test_tool_btn.py` — **UPDATE**: `set_enabled(False)` — click is a no-op (command not fired), `takefocus` is falsy, ghost styling rendered; `set_enabled(True)` — focusability, activation, and normal styling restored; a disabled button does not show a focus ring on `_on_focus_in`.
- `tests/adapters/tkinter/player/test_gameplay_screen.py` — **UPDATE**: Difficulty group renders at `Level.ONE` disabled; `−`/`+` cycle `session.difficulty` + HUD chip + sidebar label (wrap both directions); a Difficulty change redraws the canvas (assert the wall/partition set changed) without restarting the run (position/elapsed/mode/speed preserved); controls disabled at Level ONE and MAX, enabled at TWO; a level cycle re-evaluates the enabled state; focus guard applies to the Difficulty controls; no-op after solve. Update `test_hud_shows_level_and_difficulty_and_initial_time_and_pos` (line ~173): the Difficulty chip now shows `"1"`, not `"—"`.

## Tasks & Acceptance

**Execution:**
- [x] `src/labyrinthes/application/player_session.py` — add `set_difficulty` (fresh visibility at current cell, preserves run, no-op when solved); update docstring + `__all__`
- [x] `src/labyrinthes/domain/level_visibility.py` — finalize `reveal_threshold` docstring (no behavior change)
- [x] `src/labyrinthes/adapters/tkinter/common/tool_btn.py` — add `ToolButton.set_enabled` disabled state
- [x] `src/labyrinthes/adapters/tkinter/player/gameplay_screen.py` — "Difficulty" sidebar group, real HUD chip, `_cycle_difficulty`/`_sync_difficulty_widgets`/`_difficulty_enabled`, level-change re-sync
- [x] `tests/domain/test_level_visibility.py` — pin final D1/D2/D3 threshold values
- [x] `tests/application/test_player_session.py` — `set_difficulty` coverage
- [x] `tests/adapters/tkinter/common/test_tool_btn.py` — `set_enabled` coverage
- [x] `tests/adapters/tkinter/player/test_gameplay_screen.py` — Difficulty group/cycle/redraw/disable/no-op coverage; update the Difficulty-chip assertion

**Acceptance Criteria:**
- [x] Given Level 1 selected → Difficulty control disabled (non-focusable, ghost-styled, activation no-op)
- [x] Given Level 2 or higher → Difficulty 1/2/3 applies one shared `round(cols*rows/(d+1))` formula to Level 2 and Level 4 alike
- [x] Given a Difficulty change mid-session → active Level's visibility recalculates (redraw) immediately without restarting the run

### Review Findings

- [x] [Review][Patch] Stale `_focused` flag across disable→re-enable leaves a phantom focus ring [`src/labyrinthes/adapters/tkinter/common/tool_btn.py`] — disabling a focused button leaves `_focused=True` (both `_on_focus_out` and `_on_focus_in` early-return while disabled), so re-enabling renders a focus ring with no focus event. Not reachable through the Difficulty controls today (a level cycle moves focus first), but this is shared-toolkit code promised for Stories 2.9/2.10.
- [x] [Review][Patch] Difficulty→visibility re-init paths under-verified (AC-2/AC-3) [`tests/domain/test_level_visibility.py`, `tests/application/test_player_session.py`] — the Level FOUR path is never exercised: `set_difficulty` at FOUR asserts only preserved fields, and `note_collision` (Level-4 wall-threshold consumer) is tested at `Difficulty.ONE` only. `test_set_difficulty_preserves_an_in_flight_leg` runs at Level ONE where difficulty has no effect (proves leg preservation, not difficulty re-init mid-leg). The "Level 2 and Level 4 share one `reveal_threshold`" property is asserted only in a test comment, not through the real call paths.
- [x] [Review][Patch] Screen "no-op once solved" test never exercises the solved path [`tests/adapters/tkinter/player/test_gameplay_screen.py`] — the run is solved at default `Level.ONE`, so `_cycle_difficulty` returns at the disabled-guard before `session_set_difficulty` is reached; the solved no-op is only genuinely covered at the application layer.
- [x] [Review][Patch] Spec Code Map worked example `(3,2) → 3/2/1` is wrong under banker's rounding [`_bmad-output/implementation-artifacts/spec-2-7-difficulty-unified-threshold-formula.md`] — `round(6/4) == 2`, so the correct pinned values are `3/2/2`; the spec body was never corrected to match the tests (Dev Agent Record acknowledges this).
- [x] [Review][Patch] Spec "Review Findings"/"Review Triage Log" still say "fresh (`ready-for-dev`)" while frontmatter/Status say `review` [`_bmad-output/implementation-artifacts/spec-2-7-difficulty-unified-threshold-formula.md`]
- [x] [Review][Patch] `set_enabled(True)` unconditionally forces `takefocus=True` rather than restoring the pre-disable value [`src/labyrinthes/adapters/tkinter/common/tool_btn.py`] — latent today (all `ToolButton`s are constructed `takefocus=True`), but wrong for any future non-focusable button.
- [x] [Review][Patch] `set_enabled` does not reconcile a lingering `_active` [`src/labyrinthes/adapters/tkinter/common/tool_btn.py`] — a grouped active button disabled→re-enabled renders active without interaction. Not hit by the Difficulty controls (not grouped, never active); latent in shared toolkit.
- [x] [Review][Patch] `reveal_threshold` docstring "exactly `total/2`" overstates fidelity under banker's rounding [`src/labyrinthes/domain/level_visibility.py`] — for odd totals `round(total/2)` rounds half-to-even (e.g. `round(7/2)==4`) vs legacy integer division `3`; wording should say "rounds to the nearest even integer of `total/2`" or similar.
- [x] [Review][Patch] Screen redraw test omits `elapsed` preservation and level-cycle label/chip re-sync assertions [`tests/adapters/tkinter/player/test_gameplay_screen.py`] — `test_difficulty_change_redraws_the_structure_without_restarting_the_run` asserts position/mode but not elapsed (covered at app layer); `test_difficulty_controls_disable_at_level_max_and_at_level_one` never asserts the value-label foreground or HUD chip after a level cycle.

## Spec Change Log

- 2026-08-14 — Created spec from epics.md Story 2.7 ACs (lines 628-646), epic-2-context.md (Difficulty mechanics, game-scoped settings list, mid-session recalculation), PRD FR-13 + addendum "Level detail" (Level 2 vs Level 4 formula inconsistency), deferred-work.md (the two Story-2.7 seams), legacy `Labyrinthes_copy.py` (`Difficultee.plus`/`moins`, `refresh_difficultee`, `init_taille_partition_par_difficultées`, `Position_joueur_sur_back_lab_partition`, `test_nb_murs_niv_4`), Story 2.6's spec/review learnings, and the current `rewrite` codebase (post-Story 2.6).
- 2026-08-14 — Implemented Story 2.7: `set_difficulty` in `player_session.py`, `reveal_threshold` docstring finalized (no behavior change), `ToolButton.set_enabled` disabled state, Difficulty sidebar group + real HUD chip in `gameplay_screen.py`; status `ready-for-dev` → `review`.
- 2026-08-14 — Code review: applied all 9 `patch` findings (stale `_focused`/`_active` cleared on disable, `takefocus` restored, Level-FOUR + mid-leg difficulty coverage, solved no-op screen test, spec example + placeholders corrected, docstring precision, redraw/disable assertions); 5 dismissed; status `review` → `done`.

## Review Triage Log

- 2026-08-14 — Code review (9 findings, all `patch`): stale `_focused` across disable→re-enable; Level-FOUR difficulty path under-verified; solved no-op test never exercising the solved path; spec worked example wrong; stale spec placeholder; `takefocus` forced `True` on re-enable; lingering `_active` not reconciled; docstring "exactly `total/2`" overstatement; redraw/disable test gaps. 5 findings dismissed as noise/by-design. All 9 patches applied. Status `review` → `done`.

## Design Notes

**The formula is already unified — this story finalizes it.** The engine shipped one shared `reveal_threshold` (`round(cols*rows/(d+1))`) applied to both Level 2's visited-partition count and Level 4's discovered-wall count, so FR-13's legacy inconsistency (Level 2 `/(d+1)` vs Level 4 `/2,/5,/10`) is *already* not reproduced. AC-2 therefore requires confirming/pinning that single function, **not** redesigning it. Do not add per-level threshold branches; there is exactly one `reveal_threshold`.

**Banker's `round()` is faithful to legacy — the deferred item's premise is wrong.** Deferred item 2 claims legacy used a half-up `arrondi`; a full-tree grep of the shipped legacy (`.py` + `.md`, excluding the rewrite) finds **no `arrondi` anywhere**. The legacy Level-2 formula in `Labyrinthes_copy.py` (`Position_joueur_sur_back_lab_partition`) literally uses Python's built-in `round(...)` — the same banker's rounding the rewrite's `reveal_threshold` uses. So keeping `round(...)` is a faithful port, not a divergence; the story documents this and pins the values (`round(2.5)==2`, `round(0.5)==0`).

**The "Level-4 degeneracy" flag is legacy-faithful, not a regression.** Deferred item 1 notes `round(total_interior_walls/(d+1))` at D1 means ~half of a 10×10 grid's ~180 interior walls must be discovered before "all discovered walls hide again" fires. But legacy Level-4 at D1 was exactly `/2` (`test_nb_murs_niv_4`), i.e. the same half-the-walls threshold. The unified formula reproduces legacy Level-4 D1 semantics precisely while fixing only the D2/D3 divergence (unified `/3`,`/4` replace legacy `/5`,`/10`). The behavior is the product's, as specified by AC-2/FR-13; the story finalizes and documents it rather than "fixing" it into something new.

**Level-1 (and Level-Max) gating.** AC-1 mandates disabling the Difficulty control at Level 1 ("unlockable from Level 2 onward", FR-13). This story also disables it at `Level.MAX`: MAX has no partitions and no walls for a threshold to act on, and legacy blocked difficulty changes at `Niveau_max` (`Difficultee.plus` gates on `self.niveau.Niveau_max is False`), so the parity is both sensible and legacy-faithful. The HUD Difficulty chip, by contrast, always shows the session difficulty value (`1`/`2`/`3`) — it is a readout, and disabling it would hide real state (matches how the Level chip always shows a value).

**Disabled state belongs on `ToolButton`, not in the screen.** A screen-local `_cycle_difficulty` guard alone would leave the buttons focusable, clickable-looking, and without the design system's disabled affordance. `colors.ghost` is DESIGN.md's explicit "disabled or not-yet-set state" token. Adding `ToolButton.set_enabled()` as a reusable capability in the shared `common/` toolkit (AD-11) keeps the gating at the widget level (non-focusable + non-activating + ghost-styled), ready for any future disabled control (e.g. Story 2.9's timer field or 2.10's confirmation toggles).

**Placement & interaction.** The Difficulty group sits directly under the "Levels" group, mirroring the legacy `<-`/`Niveau`/`->` then `<-`/`Difficultée`/`->` stacking, and keeping the control on the gameplay surface where FR-28's ⓘ-anchor will later attach. It is a plain `−`/value/`+` stepper (no `ToolButtonGroup`, no exclusivity), wraps in both directions, is Tab+Enter/Space-operable, and shares the Story 2.5/2.6 toplevel focus guard. No global shortcut.

**Difficulty is session-scoped, not persisted.** The epic context's game-scoped settings list has no Level/Difficulty entry, and legacy `Difficultee.numero` was session state. A fresh mount (re-navigate) starts at `Difficulty.ONE`. Do not add a `game`-scoped `DIFFICULTY` key.

## Previous Story Intelligence

- **Story 2.6 (levels)** established the exact seams this story completes: the session already carries `level`/`difficulty`/`visibility`; `set_level` is the template for `set_difficulty` (fresh visibility at the current cell, preserves run, no-op once solved); the "Levels" sidebar group (`−`/value/`+` ToolButtons, `TYPOGRAPHY.hud_stat` value label, wraparound, no shortcut, focus-guarded) is the template for the "Difficulty" group; the HUD Level chip went real via `HudChip.set_value`; and `_sync_visibility()` redraws on visibility-identity change. The 2.6 Design Notes explicitly reserve "the Difficulty control, its Level-1-disable gating, and the final shared-formula decision" for this story.
- **Story 2.5 (movement modes)** supplies the `session_set_*` import-alias convention, the sidebar `ToolButton` pattern, the toplevel focus guard, and the `_settle()` test-driver convention.
- **Regression watchlist:** the `GameplayScreen(...)` construction sites in `test_gameplay_screen.py` (all pass `settings_repository=`); the Difficulty-chip assertion in `test_hud_shows_level_and_difficulty_and_initial_time_and_pos` (changes `"—"` → `"1"`); the `set_level`/`set_speed`/`set_mode` no-op-after-solve guards (the new `set_difficulty` must match); `ToolButton`'s existing tests (the new `set_enabled` must not disturb active/focus styling); the AD-9 import-boundary test must still pass.

## Git Intelligence

- Working branch: `epic-2-play-a-maze-game-player` (the epic-2 accumulation branch, current HEAD `d716269`). **Never commit directly to it** — create `story-2-7-difficulty-unified-threshold-formula` from it, merge story → epic via `git merge --no-ff` when done; epic → `rewrite` only via PR once the whole epic is done.
- Mirror the per-story rhythm: `feat(player): ...` (feature) → `refactor(player): ...` / `test(player): ...` (cleanup/tests) → `docs(planning): record Story 2.x review, mark done, log deferred work` → `Merge story-2-x-... into epic-2-... (story 2.x)`. Conventional Commits in English, story number in the subject (`(story 2.7)`).
- `uv.lock` is untracked — leave it alone.

## Latest Technical Information

No new external dependencies: the stack is pinned in `pyproject.toml` (Python ≥3.12, tkinter, pytest ≥8.0, ruff ≥0.6, hatchling). Everything here uses stdlib (`enum`, `dataclasses`, `functools`) and the existing `domain/`/`application/`/`common/` types — no web research was needed, and no version/API changes affect this story.

## Verification

**Commands:**
- `ruff check .` — expected: no new lint violations (line-length 100, rules `E, F, I, UP, B, SIM`; no comments unless asked)
- `ruff format --check .` — expected: no formatting diffs
- `pytest` — expected: full suite green, including the new `set_difficulty`/`set_enabled`/Difficulty-group tests and the updated Difficulty-chip assertion

**Regression watchlist:** `ToolButton` active/focus styling tests (`test_tool_btn.py`) must stay green with the new disabled branch; `set_level`-family no-op-after-solve tests; the `GameplayScreen` construction sites; the AD-9 import-boundary test; the existing `test_hud_shows_level_and_difficulty_and_initial_time_and_pos` assertion update (`"1"`, not `"—"`).

## Project Structure Notes

- All Difficulty logic stays under `src/labyrinthes/domain/` (pure, already built) and `src/labyrinthes/application/` (session orchestration, one new function); only rendering/input/disabled-styling lands in `adapters/` (`common/tool_btn.py` for the reusable capability, `player/gameplay_screen.py` for the control). No new screen, no new port, no new settings key, no composition-root change.
- Naming is English throughout (NFR4); maze data (`0/1/2/3`) untouched; the `Difficulty` type already exists and stays as-is (Story 1.1).
- No `tkinter`/`adapters` import may appear in `player_session.py` or `level_visibility.py` (AD-1, AD-9).

## References

- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 2.7 ACs (lines 628-646); FR-13 (lines 49, 140-146); FR-28 anchor note (line 79)]
- [Source: `_bmad-output/planning-artifacts/prds/prd-Labyrinthes-2026-08-04/prd.md` — FR-13 (lines 143-147)]
- [Source: `_bmad-output/planning-artifacts/prds/prd-Labyrinthes-2026-08-04/addendum.md` — "Level detail" (lines 28-34), incl. the Level 2 vs Level 4 formula inconsistency]
- [Source: `_bmad-output/implementation-artifacts/epic-2-context.md` — Difficulty mechanics (line 35: one single shared reveal-threshold formula; mid-session change recalculates immediately), game-scoped settings list (line 50), technical decisions (lines 45-51)]
- [Source: `_bmad-output/implementation-artifacts/deferred-work.md` — the two Story-2.7 seams: banker's `round()` vs legacy `arrondi` (line 8); Level-4 threshold degenerate at real maze sizes (line 6)]
- [Source: `_bmad-output/implementation-artifacts/spec-2-6-levels-progressive-visibility-1-4-max.md` — the 2.6/2.7 seam (lines 45, 53, 161); `set_level` template; Level-group code map (lines 105-113)]
- [Source: `Labyrinthes_copy.py` (legacy, read-only) — `Difficultee.plus`/`moins` (2084-2116), `Difficultee.difficultees` (2118-2135), `refresh_difficultee` (1232-1241), `init_taille_partition_par_difficultées` (747-770), `Position_joueur_sur_back_lab_partition` Level-2 threshold (772-806), `test_nb_murs_niv_4` Level-4 `/2,/5,/10` (965-979)]
- [Source: `src/labyrinthes/application/player_session.py` (`set_level`, line 258), `domain/level_visibility.py` (`reveal_threshold`, line 193), `adapters/tkinter/common/tool_btn.py` (no disabled state today), `adapters/tkinter/player/gameplay_screen.py` (`_PLACEHOLDER_DIFFICULTY`, Levels group, `_cycle_level`, `_sync_level_widgets`, focus guard, `_sync_visibility`), `adapters/tkinter/common/hud_chip.py`, `common/tokens.py` (`colors.ghost`, `TYPOGRAPHY.hud_stat`)]

## Dev Agent Record

### Agent Model Used

opencode/deepseek-v4-flash-free

### Debug Log References

- Implemented `set_difficulty` mirroring `set_level` (fresh `initial_level_visibility` at the current cell, preserves position/elapsed/mode/speed/in-flight leg, no-op once solved); threaded through `application/player_session.py` docstring + `__all__`.
- Finalized `reveal_threshold` docstring only — no behavior change (the single shared `round(cols*rows/(d+1))` already drives both Level 2 and Level 4). Noted that banker's `round()` is faithful to legacy (no `arrondi` helper exists in the shipped legacy tree) and that D1 Level-4 is legacy `/2`.
- Added `ToolButton.set_enabled` (disabled = `takefocus=False`, `_on_click` no-op, focus in/out no-op, ghost palette; re-enable restores focusability/activation/styling). `ToolButtonGroup` untouched.
- Wired the "Difficulty" sidebar group under "Levels" (`−`/value/`+`, `_DIFFICULTY_CYCLE` wraparound both directions, no shortcut), replaced the `"—"` HUD placeholder chip with the real `session.difficulty` feed, added `_cycle_difficulty`/`_sync_difficulty_widgets`/`_difficulty_enabled` (enabled iff level not ONE/MAX), and re-synced difficulty widgets on level changes. Shares the toplevel focus guard; `_sync_visibility()` drives the redraw on the visibility identity change.
- Testing note: the spec's worked `(3,2) → D3 == 1` example is wrong under Python's banker's `round(1.5) == 2`; pinned the *correct* D1/D2/D3 values plus explicit banker's-rounding edge cases instead.

### Completion Notes List

- Created spec from epics.md Story 2.7 ACs, epic-2-context.md, PRD FR-13 + addendum, deferred-work.md, legacy `Labyrinthes_copy.py` Difficulty mechanics, Story 2.6's spec/review learnings, and the current `rewrite` codebase (post-Story 2.6).
- Implemented Story 2.7 end-to-end: `set_difficulty` session operation, finalization of the unified `reveal_threshold` formula, `ToolButton.set_enabled` disabled state, and the Difficulty sidebar control + real HUD chip. All 8 execution tasks and 3 acceptance criteria checked. Full suite green (611 passed), `ruff check .` and `ruff format --check .` clean on `src/`/`tests/`.
- Marked story status `review` in both the story file and `sprint-status.yaml`.

### File List

- This spec: `_bmad-output/implementation-artifacts/spec-2-7-difficulty-unified-threshold-formula.md`
- Story-2.7 entry in `_bmad-output/implementation-artifacts/sprint-status.yaml` (2-7: in-progress -> review)
- `src/labyrinthes/application/player_session.py` — `set_difficulty`
- `src/labyrinthes/domain/level_visibility.py` — finalize `reveal_threshold` docstring (no behavior change)
- `src/labyrinthes/adapters/tkinter/common/tool_btn.py` — `ToolButton.set_enabled`
- `src/labyrinthes/adapters/tkinter/player/gameplay_screen.py` — "Difficulty" sidebar group, real HUD chip, cycle/sync/enabled helpers
- `tests/domain/test_level_visibility.py` — pin final D1/D2/D3 thresholds
- `tests/application/test_player_session.py` — `set_difficulty` coverage
- `tests/adapters/tkinter/common/test_tool_btn.py` — `set_enabled` coverage
- `tests/adapters/tkinter/player/test_gameplay_screen.py` — Difficulty-group coverage + chip assertion update