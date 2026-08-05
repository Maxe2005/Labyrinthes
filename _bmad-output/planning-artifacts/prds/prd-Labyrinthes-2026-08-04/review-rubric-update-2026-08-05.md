# PRD Quality Review (Update Pass) — Labyrinthes — Modular Rewrite

**Scope note:** this is an update review of the 2026-08-05 amendment only — §4.2 (FR-26, FR-27), FR-28 (§4.3), the new Accessibility NFR (§6), the Home/Personal Record Glossary entries (§3), amended UJ-1/UJ-2 (§2.2), and the downstream renumbering (§4.3→§4.6). Material that didn't change is not re-litigated; see `review-rubric.md` for the prior full-pass review, whose verdicts on unchanged sections still stand.

## Overall verdict

The amendment is mechanically excellent — every one of the ~10 section/FR renumbering touch-points was updated in lockstep (verified by grep: `§4.1-4.5` ranges in §4.6 and SM-1, and the `§4.2, §4.3` cross-refs in §9, all correctly shifted) and the new Glossary/Non-Goals/UJ integration is careful and consistent. But the amendment's substance falls short of the one job the record shows it was supposed to do: the architecture `.memlog.md` states Architecture explicitly stopped and deferred building Personal Records "until this PRD update landed," and this update still leaves the central product question — whether a Personal Record is scoped per-maze or per-maze-per-Level/Difficulty — completely unaddressed, inherited unresolved from the UX spec rather than closed here. Two smaller but real integration gaps ride along: the new Accessibility NFR's scope text never mentions Home, the surface this very update introduces, and FR-28 sends a mixed signal about whether HARD mode is in or out of its own scope.

## Decision-readiness — adequate

FR-26's router-exception carve-out is a real, well-drawn decision (§4.2: "Two contextual exceptions bypass Home... gated to mazes with a Builder-editable source... Every other transition between the Builder and the Game passes back through Home"), and the Accessibility NFR states real bounds rather than hedging. But the one decision this update exists to make — per the update note's own framing and the architecture memlog's explicit deferral — is not made. FR-27 says the system "records the player's fastest completion time for that maze" without saying whether "that maze" is scoped by the Level/Difficulty the run was played at. This is not a minor omission: Levels/Difficulty change how much of the grid is visible during a solve (§4.3, FR-12/FR-13), so a "fastest time" that mixes a Level-1 run with a Level-4 run is not a coherent leaderboard entry. Neither the PRD nor the UX `EXPERIENCE.md` it's reconciling with states a position either way, and this PRD update doesn't add one, flag it as an Open Question, or tag it `[ASSUMPTION]` — it's simply absent, and a decision-maker reading only this PRD would not know it's unresolved.

### Findings
- **high** Personal Record scope vs. Level/Difficulty left undecided (§4.2 FR-27) — FR-27's testable consequence ("A new completion time replaces the stored record for that maze only if it is faster than the existing one") presumes a single record per maze, but doesn't say whether Level/Difficulty is part of the maze's "identity" for this purpose. This is exactly the point Architecture flagged as blocking (`architecture-Labyrinthes-2026-08-04/.memlog.md`: "Personal Records... Max's call: update the PRD first... before this spine is extended for it") and it is the reason this update pass exists, per the PRD's own §0 update note — yet it isn't resolved. *Fix:* state the scoping rule explicitly (e.g. "one record per maze, independent of Level/Difficulty" or "one record per maze × Level × Difficulty combination"), or if genuinely undecided, add it to §8 Open Questions and/or tag it `[ASSUMPTION]` in §4.2 rather than leaving it implicit.

## Substance over theater — strong

The new Accessibility NFR (§6) is not boilerplate — it carries concrete, checkable bounds ("WCAG AA," "shape as well as color, never color alone," explicit scope exclusion for screen readers with a stated reason). FR-26/27/28 each name a specific mechanism rather than a generic capability statement. No findings.

## Strategic coherence — adequate

FR-26/27/28's integration with the existing thesis is well-argued: the §0 update note explicitly ties them to the UX phase surfacing a gap, and Non-Goals (§5) was correctly extended ("Personal Records (FR-27) stay local-only; any future community maze library or shared leaderboards are out of scope beyond that") rather than left stale. The Accessibility NFR, however, arrives with no stated rationale connecting it to this update's narrative — the §0 update note frames the whole amendment as reconciling the Home/Personal-Records gap ("FR-26 through FR-28 were added after the UX phase... fixed Home as the app's sole router and introduced Personal Records"), but never mentions the NFR at all, so a reader is left to guess why an accessibility requirement rides along with a navigation-hub feature addition.

### Findings
- **low** Accessibility NFR's origin is unstated (§0 vs. §6) — the update note enumerates what changed ("FR-26 through FR-28... Home screen... Personal Records") but omits the new NFR, the Glossary entries, and the UJ edits entirely, even though the task-level amendment includes all of them. *Fix:* extend the §0 update note to name the NFR (even one clause — e.g., "and a keyboard/contrast accessibility floor was added at the same time") so the change record is complete, not just the FR additions.

## Done-ness clarity — thin

This is where the amendment's substance gaps concentrate. Beyond the Personal-Record scoping gap already covered under Decision-readiness (which is as much a done-ness problem as a decision one — an engineer building FR-27 cannot write the record-comparison logic without it), two more new-material specifics are underspecified:

### Findings
- **medium** FR-28's own scope is internally inconsistent on HARD mode (§4.3) — the FR's title and body scope it to "Level or Difficulty tier[s]" only ("The first time the user activates a given Level or Difficulty tier..."), but its own consequence bullet says "Every tier gets this treatment, not just HARD mode" — implying HARD mode is also in scope for this explainer, which contradicts the title's Level/Difficulty-only framing and the Glossary (§3), which defines HARD mode as a distinct concept from Level and Difficulty. This phrasing is inherited verbatim from the UX spec (`EXPERIENCE.md` line 63: "every tier, not just HARD") but the PRD doesn't reconcile it with its own Glossary's category boundaries. FR-14 (HARD mode, §4.4) has no explainer-related consequence at all, so if HARD mode really is in scope, that FR has no cross-reference to FR-28. *Fix:* either broaden FR-28's title/scope to explicitly include HARD mode and add a one-line cross-reference from FR-14, or drop "not just HARD mode" from the consequence bullet if HARD mode genuinely isn't covered.
- **medium** FR-27's Personal Records ordering criterion is ambiguous (§4.2) — "displays these records, most relevant/recent first" gives two different possible sort keys ("relevant" vs. "recent") joined by a slash with no tie-breaking rule or definition of "relevant." This is inherited from `EXPERIENCE.md` ("most relevant/recent first," line 73) but the PRD update was the opportunity to resolve it and didn't. *Fix:* commit to one ordering rule (most likely: most-recently-set-or-broken record first) or state both criteria and the precedence between them.

## Scope honesty — adequate

Non-Goals (§5) integration is honest and specific for what it does cover (local-only records, no leaderboard, no accounts). But the Level/Difficulty scoping gap above is exactly the kind of omission §5's own convention exists to surface, and it wasn't — nothing in §5, §8 Open Questions, or §9 Assumptions Index flags it, so the silence reads as settled rather than open. The two Done-ness findings above are equally Scope-honesty findings (an unflagged gap is unflagged regardless of which dimension catches it first); not re-listed here to avoid double-counting.

## Downstream usability — adequate

Mechanically, the amendment is careful: FR IDs (26, 27, 28) are unique and contiguous with the existing 1–25 range, every `§4.x` cross-reference was correctly re-pointed after the section insertion (checked via full-text grep — §9's "FR-26 through FR-28 (§0, §4.2, §4.3)" correctly matches FR-26/27's actual location in §4.2 and FR-28's in §4.3), and the new Glossary entries (Home, Personal Record) are used with consistent capitalization and singular/plural distinction everywhere they recur (Home; Personal Record singular for one maze's record vs. Personal Records plural for the feature/zone name). One tracing gap:

### Findings
- **low** FR-28 not traced by any UJ despite direct relevance (§2.2, §4.3) — UJ-2 was carefully extended to reference the other two new FRs ("Realizes FR-9, FR-10, FR-12, FR-13, FR-15, FR-26, FR-27") and its prose already walks through "selects a Level and a Difficulty" — the exact moment FR-28's first-activation explainer fires — but FR-28 itself isn't listed. Since FR-26/FR-27 got UJ tracing as part of this same pass, the omission reads as inconsistent completeness rather than a deliberate lightweight-journey choice. *Fix:* add FR-28 to UJ-2's Realizes list.

## Shape fit — strong

The new material stays at the same lightweight-hobby formalization level as the rest of the PRD — no new UJs manufactured, no stakeholder apparatus added, three short FRs and one NFR sized appropriately to the change. No findings.

## Mechanical notes

- Renumbering integrity is fully verified: `§4.1-4.5` appears in both §4.6's description and SM-1 (§7) and correctly reflects the post-insertion range (old §4.1-4.4 → new §4.1-4.5, since Navigation—Home was inserted as the new §4.2, shifting Cross-cutting from §4.4 to §4.5). §9's `(§0, §4.2, §4.3)` cross-reference for FR-26/27/28 also resolves correctly. No stale section numbers found anywhere in the document.
- The Accessibility NFR's scope clause ("no mouse-only affordance anywhere in the Builder or the Game") names only the Builder and the Game, not Home — even though Home is newly established by this same amendment as a third top-level, independently-navigable app surface (Glossary §3: "the app's entry screen and sole general router... also hosts Settings access and the Personal Records zone"). Read literally, Home's own navigation cards, Settings icon, and Personal Records zone fall outside the accessibility floor's stated scope. This is worth surfacing even though it's not flagged as a full finding above (it's a scope-wording gap rather than a decision left open): *Fix:* add "and Home" (or "and every screen") to the NFR's scope clause in §6.
- UJ protagonist naming and Glossary term consistency both continue to hold under the amendment — no new drift introduced by the update.
