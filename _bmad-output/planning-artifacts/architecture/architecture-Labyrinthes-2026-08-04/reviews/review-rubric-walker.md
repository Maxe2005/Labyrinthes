# Rubric Walk Review — ARCHITECTURE-SPINE.md (Labyrinthes)

Reviewer role: independent rubric walker, fresh context, no deference to the author's framing.

Target: `_bmad-output/planning-artifacts/architecture/architecture-Labyrinthes-2026-08-04/ARCHITECTURE-SPINE.md`
Checked against: PRD (`prd.md`, `addendum.md`), `CLAUDE.md`, existing `pyproject.toml`, existing `src/labyrinthes/` skeleton, existing `_bmad-output/.../ux-designs/ux-Labyrinthes-2026-08-04/` state.

## Verdict

Solid, lean spine that correctly ratifies existing project conventions and covers the large majority of real divergence points. One **high-severity** gap (settings persistence does not actually mandate a single shared implementation, unlike the analogous maze-persistence rule) undercuts the exact defect (FR-21 clobbering bug) an AD was written to prevent. A few medium-severity gaps (no shared UI-toolkit decision, incomplete automated-boundary coverage, one inaccurate map entry) and low-severity polish items round out the findings. Nothing here is a "critical" blocker, but AD-6 should be tightened before downstream epics/stories are cut from this document.

---

## 1. Does the spine fix the real divergence points for the level below, and miss none?

Mostly yes. The nine ADs cover the load-bearing forks well: layering direction (AD-1), state mutation model (AD-2), rendering-vs-port split (AD-3), single maze-persistence implementation (AD-4), on-disk encoding contract (AD-5), settings access pattern (AD-6), migration lifecycle (AD-7), automated boundary enforcement (AD-8), and cross-launch wiring (AD-9). These map directly onto named legacy defects in the addendum (big_boss coupling, FR-21 clobbering, FR-19 one-way link, FR-11 dead-end save), which is exactly the kind of "port the feature, not the architecture" grounding the PRD asks for.

Two real gaps found:

### 1a. [HIGH] AD-6 does not mandate a single shared `SettingsRepository` implementation — the FR-21 fix has a loophole

AD-4 explicitly protects `MazeRepository`: "exactly one `MazeRepository` implementation lives under `adapters/storage/` and is used by both composition roots... no per-app duplicate parsing." This is precisely the kind of structural rule that prevents Builder and Game from silently diverging.

AD-6 has no equivalent clause for `SettingsRepository`. Its Rule fixes the *access pattern* (`get(scope, key)`/`set(scope, key, value)`, written immediately, three scopes) but never states that both composition roots must wire up the *same* `SettingsRepository` implementation/backing store for the `shared` scope. The phrase "shared (global — e.g. the FR-4/FR-10 size bounds, defined once and read identically by both apps)" describes the *intended semantics* of the shared scope but is not phrased as an enforceable Rule the way AD-4's "no per-app duplicate parsing" is.

This matters because the Deferred section compounds it: "Exact settings file format (JSON/TOML/CSV per scope). AD-6 fixes the access pattern (scoped, granular); the on-disk format is an implementation detail below this spine's altitude — left to Epics/Stories." If the format is genuinely left open per-story, and nothing forces both apps' composition roots to instantiate the *same* `SettingsRepository` object/backing file for the `shared` scope, two independently-built stories (a Builder-settings story and a Game-settings story) could each implement their own `SettingsRepository` against the same interface but pointed at different files/formats for `shared` data — which is not the byte-for-byte legacy clobbering bug, but is the same *category* of bug AD-6 exists to prevent (two apps disagreeing about the one shared value, e.g. the FR-4/FR-10 size bounds). This is a genuine "two independently-built units diverge incompatibly" scenario per the review checklist, and it directly threatens FR-4's "single-source-of-truth" requirement that AD-6's own history note says it was written to satisfy.

**Recommendation:** add to AD-6's Rule an explicit clause parallel to AD-4's: exactly one `SettingsRepository` implementation lives under `adapters/storage/` and is used by both composition roots (no per-app duplicate implementation), at minimum for the `shared` scope.

### 1b. [MEDIUM] No decision on a shared/common Tkinter UI toolkit, despite it being an established, valued pattern in the codebase being ported

`CLAUDE.md` documents `Autres/Outils.py` as a real, reused cross-app toolkit (`Boutons` factory, `Commentaire` tooltips, `Reglages`/`Base_Reglages` generic settings panel) shared by both legacy monoliths. The PRD requires both apps to expose theme toggling (FR-6 builder, FR-18 game) and per-action confirmation prompts (FR-17), which in the legacy app come from that shared toolkit.

The spine's directory layout only shows:
```
adapters/
  tkinter/         # builder/ and player/ UI — owns its own rendering
  storage/
```
with no `adapters/tkinter/common/` (or equivalent) called out, and AD-3's Rule ("each UI adapter implements its own rendering directly... no over-constrained rendering abstraction") could be read as endorsing full independence between the two Tkinter adapters. AD-3 is correctly scoped to *rendering* (a good call — forcing one rendering abstraction across present Tkinter and a future web adapter would be the over-constrained trap), but it doesn't address the narrower, real question of whether Builder's and Game's Tkinter adapters share generic widget/settings-panel code with each other today. Leaving this fully silent risks the two adapters independently reinventing near-identical button/tooltip/settings-panel code — not a data-correctness bug like 1a, but a real, foreseeable duplication/inconsistency risk given the pattern already exists in the code being ported.

**Recommendation:** either add a short AD (or a Deferred bullet with reasoning, if intentionally left to story level) stating whether `adapters/tkinter/builder` and `adapters/tkinter/player` may/should share a `common/` module for generic widgets, or explicitly note that duplication is accepted for now.

## 2. Is every AD's Rule enforceable and does it actually prevent its stated divergence?

Each Rule is individually coherent and the paradigm choice (hexagonal, ports only for persistence) is well-reasoned and correctly scoped — AD-3 in particular resists the temptation to over-abstract rendering. However, enforcement is uneven:

- **AD-1** is enforced mechanically by **AD-8**'s import-scan test. Good — this is the strongest AD/enforcement pairing in the doc.
- **AD-8**'s scan is stated as covering only `domain/` and `application/` source for forbidden imports of `tkinter`/`adapters`. It does **not** cover two adjacent risks the doc itself calls out elsewhere:
  - [MEDIUM] `adapters/tkinter/*` importing `adapters/storage/*` directly, bypassing `application/` services — which would undercut both AD-3 ("calling `application/` services") and AD-4 ("no per-app duplicate parsing," since a direct import re-opens the door to per-adapter storage logic).
  - [MEDIUM] `adapters/tkinter/builder` and `adapters/tkinter/player` importing each other directly — exactly the divergence **AD-9** exists to prevent, stated as a Rule ("never import each other directly") but with no automated guard, unlike AD-1's equivalent rule.
  Both are cheap additions to the same import-scan test and would close the gap between "stated as a Rule" and "actually enforced," which is the standard the doc itself sets with AD-1/AD-8.
- **AD-2** (immutability) is enforceable via language mechanism (frozen dataclasses/similar) but the spine doesn't say so, and there's no test analogous to AD-8 guarding against a mutable method creeping back in — a plausible regression path given the whole point of the anti-`big_boss`-pattern goal is exactly this kind of silent erosion. [LOW]
- **AD-4, AD-6, AD-7** are convention-level rules with no automated backstop; acceptable at this altitude (not everything needs a test) but worth naming as a residual risk rather than leaving it implicit.

## 3. Could anything under "Deferred" let two independently-built units diverge incompatibly?

Six of seven Deferred bullets are legitimate: web/mobile stack (genuinely undecided, doesn't block current work since AD-1–3 keep the door open), FR-24/25 detailed design (explicit PRD P2), UX visual identity (traced and confirmed — the referenced UX run really is stalled at `status: draft` with empty `EXPERIENCE.md`/`DESIGN.md` files, verified directly), migration script mechanics (single-script decision already fixed by AD-7, only *mechanics* deferred), packaging/distribution (no PRD NFR requires it — checked; confirmed absent from PRD §6), and porting order (explicitly PRD Open Question 2).

The seventh — "Exact settings file format... AD-6 fixes the access pattern" — is the problematic one, covered in finding 1a above: the deferral's own justification overstates what AD-6 actually fixes, and deferring the format without also mandating single-implementation reuse for the shared scope creates a real incompatible-divergence path.

## 4. Named tech: plausible/current?

`Python >=3.12`, `ruff >=0.6`, `pytest >=8.0`, `hatchling`, `Tkinter` (stdlib) — all mirror `pyproject.toml` exactly (verified by reading the file). Version floors (`>=`) rather than exact pins is the right call for a spine document; nothing here looks fabricated or obviously wrong. No live-web verification performed per instructions (that's a separate reviewer's pass) — nothing jumped out as needing it.

## 5. Does the spine ratify rather than contradict the existing project?

Yes, cleanly:
- Stack table is byte-for-byte consistent with the actual `pyproject.toml` (Python floor, ruff/pytest floors and selected rule codes' intent, hatchling backend, legacy-exclude convention referenced implicitly).
- `src/labyrinthes/` currently contains only `__init__.py` (verified) — the proposed `domain/application/adapters/app` layout doesn't contradict anything on disk, it's genuinely greenfield.
- English-only convention, anti-`big_boss` framing, and "port features not architecture" all directly echo `CLAUDE.md` and the PRD's Explicit Non-Goals — no re-litigation of settled matters found.
- Correctly treats `main` (legacy) as read-only reference and doesn't propose touching it.

## 6. Coverage of PRD capabilities FR-1 through FR-25

All 25 FRs are accounted for via the Capability → Architecture Map or Deferred section — no FR is silently missing. One accuracy issue found:

**[MEDIUM] FR-22 (keyboard shortcuts) is miscategorized in the Capability → Architecture Map.** It's lumped into the "Cross-cutting data & integration (FR-20–FR-23)" row, "Governed by: AD-4, AD-5, AD-6, AD-7." But FR-22 is about keybinding-to-action uniqueness and tooltip-label accuracy within each Tkinter adapter — none of AD-4 (shared maze repo), AD-5 (cell encoding), AD-6 (settings scoping), or AD-7 (migration) touch keyboard shortcuts at all. The row groups FR-22 with three genuinely storage/data-related FRs (FR-20, FR-21, FR-23) purely because the FR numbers are numerically adjacent, not because the governing ADs actually apply. The FR-22 fix (one canonical keybinding table per app, consistent with its displayed label) is real but architecturally thin enough that it may not need its own AD — but the map entry currently overclaims coverage that isn't there.

## 7. Are all initiative/whole-product structural dimensions decided, deferred, or flagged?

Checked systematically against the standard set of dimensions an architecture spine at this altitude should touch:

| Dimension | Status |
| --- | --- |
| Paradigm/layering | Decided (Hexagonal, AD-1) |
| Language/runtime | Decided (Stack table) |
| Build/dependency tooling | Decided (ratifies pyproject.toml) |
| Domain mutability model | Decided (AD-2) |
| Persistence strategy (maze) | Decided (AD-4, AD-5) |
| Persistence strategy (settings) | Decided but incomplete — see 1a |
| Legacy data migration | Decided (AD-7) |
| UI/adapter boundary | Decided (AD-1, AD-3) |
| Cross-app UI code sharing | **Silent** — see 1b |
| Cross-app launch wiring | Decided (AD-9) |
| Testing/quality gate | Decided (AD-8 + NFR reference) |
| Naming/language convention | Decided (Consistency Conventions, ratifies CLAUDE.md) |
| Deployment/packaging/infra | Explicitly deferred with a stated reason (no PRD NFR requires it) — this is the *good* pattern the checklist asks to distinguish from silent omission, and it's done correctly here |
| CI/CD pipeline | Silent, not even named as deferred — but low-impact: solo project, no PRD NFR asks for CI, "ruff + pytest gate" already exists per NFR §6/CLAUDE.md without requiring a hosted pipeline decision. [LOW] |
| Error/exception signaling convention across the AD-1 boundary | **Silent in substance** — see below |
| Logging | Silent, plausibly out of scope (no PRD NFR), but not stated as such |
| Auth/multi-user | Correctly out of scope per PRD non-goals; doesn't need to appear |

**[LOW] The "State & cross-cutting (mutation, errors, logging, config, auth)" row of the Consistency Conventions table doesn't actually address errors, logging, config, or auth** — its content only restates AD-2 (mutation) and AD-8 (boundary enforcement). Given the row header explicitly promises those four concerns, and there's no PRD-non-goal reason to skip "errors" the way there is for "auth," this reads as an unfulfilled promise in the document's own structure rather than a deliberate, stated scope cut. Not necessarily a divergence risk serious enough to warrant its own AD (a solo developer is unlikely to invent two incompatible exception schemes), but worth either filling in briefly or trimming the row header to match what's actually there.

Deployment/environment/infra — the dimension the checklist calls out for special attention — is handled correctly: it's not silently missing, it's deferred with an explicit, checkable reason (verified against PRD §6, which indeed has no packaging/deployment NFR).

## 8. Leanness — does anything fail the "could two independently-built units diverge incompatibly on this?" test?

The document is appropriately tight: ~140 lines, no padded prose, every AD ties to a named legacy defect or PRD FR/NFR, and the Deferred section actively resists scope creep (explicitly punting FR-24/25 detail, web stack, UX polish). No AD reads as invariant-for-invariant's-sake; all nine pass the divergence test in the sense that a plausible two-track build (Builder epic vs. Game epic, done separately) could actually violate each one if it didn't exist. No bloat found — if anything the doc is slightly under-specified in the two spots flagged above (1a, 1b) rather than over-specified anywhere.

---

## Summary of Findings

| # | Severity | Finding |
| --- | --- | --- |
| 1 | HIGH | AD-6 doesn't mandate a single shared `SettingsRepository` implementation for the `shared` scope (unlike AD-4 for `MazeRepository`); combined with the deferred settings-format decision, this leaves a path to reintroduce a divergence bug in the same class as the one FR-21/AD-6 was written to fix. |
| 2 | MEDIUM | No decision on whether `adapters/tkinter/builder` and `adapters/tkinter/player` share a common widget/settings-panel module, despite `CLAUDE.md` documenting exactly this pattern (`Autres/Outils.py`) as already established in the code being ported. |
| 3 | MEDIUM | AD-8's automated import-scan is scoped to `domain/`+`application/` only; it doesn't guard against `adapters/tkinter` → `adapters/storage` direct imports (undercuts AD-3/AD-4) or `builder` ↔ `player` direct imports (undercuts AD-9), even though both are cheap additions to the same mechanism. |
| 4 | MEDIUM | Capability → Architecture Map lists FR-22 (keyboard shortcuts) as governed by AD-4/AD-5/AD-6/AD-7, none of which actually address keyboard shortcuts — an accuracy issue in the map, not a missing FR. |
| 5 | LOW | Consistency Conventions table's "errors, logging, config, auth" row doesn't substantively address errors/logging/config; only restates AD-2/AD-8. |
| 6 | LOW | Enforcement asymmetry: AD-1 gets an automated test (AD-8); AD-2, AD-4, AD-9 state equally load-bearing rules with no automated backstop. |
| 7 | LOW | CI/CD pipeline dimension is silent rather than explicitly named as out-of-scope/deferred (low impact given solo-project context and no PRD NFR demanding it). |

## What the spine does well (for balance)

- Correctly resists over-abstracting rendering (AD-3) while still fixing the one abstraction that matters for data integrity (persistence ports).
- AD-1/AD-8 pairing (rule + automated enforcement) is a genuinely strong example of a structural, not conventional, boundary — directly answers the PRD's core anti-goal.
- Every AD traces to a specific, named legacy defect or PRD FR — no invented invariants.
- Deferred section reasoning was spot-checked (UX run status, PRD NFRs for packaging, PRD Open Questions 2 and 4) and found accurate in every case checked.
- Stack table exactly matches the already-ratified `pyproject.toml` — no re-litigation of settled tooling.
