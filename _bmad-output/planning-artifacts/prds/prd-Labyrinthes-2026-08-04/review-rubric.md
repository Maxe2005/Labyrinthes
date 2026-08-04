# PRD Quality Review — Labyrinthes — Modular Rewrite

## Overall verdict

This is a well-earned PRD for its stakes: the thesis is specific (parity port + architectural decoupling, not a rewrite-for-its-own-sake), the legacy-code claims in the addendum check out against the actual source (verified by spot-check, see Shape fit), and scope is deferred honestly rather than smoothed over. The main risks are downstream, not conceptual: two FRs (FR-4, FR-10) leave a load-bearing "bounded" undefined with no number anywhere in either document, and roughly half the FRs have no User Journey tracing them, which is defensible for a solo-hobby PRD but will cost the architecture/stories phase some reconstruction work. Nothing here is a blocker; the fixes are additive, not structural.

## Decision-readiness — strong

Trade-offs are named rather than smoothed. §8 Open Question 4 states the migration-approach fork explicitly ("a one-time conversion script, or a compatibility shim that reads both layouts during a transition period — not decided") and FR-23's Notes cross-reference it instead of silently picking one. §5 Non-Goals states real decisions as decisions ("No user accounts, multiplayer, or online features in this milestone," "No monetization considered at this stage") rather than burying them as considerations. The Vision's "Explicit anti-goal" paragraph is a genuine stance (legacy architecture patterns are "learning-era hacking — not to be reproduced or imitated"), not a hedge. §7's counter-metric (SM-C1) is substantive, not decorative — it explicitly disqualifies a shipped-but-untested feature from counting as "ported."

### Findings
- **low** Rubric-style PM callouts not used (whole doc) — the PRD's real tensions (migration approach, porting order, new-mode design) are captured faithfully in §8 Open Questions and per-FR "Notes:" fields, but never with the `[NOTE FOR PM]` bracket convention the rubric looks for. *Fix:* none needed — the substance is present; only worth a note if this PRD is meant to interoperate with other BMad artifacts that scan for that literal tag.

## Substance over theater — strong

No persona theater: §2.1 has exactly one persona (the author, wearing three JTBD hats) appropriate for a solo project, and each JTBD is concrete enough to trace to features (e.g. "without touching three different files or untangling a `big_boss` reference graph" ties directly to the Non-Goals architecture stance). No NFR boilerplate — §6's five NFRs each carry a specific mechanism and rationale ("Logic/UI decoupling... is what makes a future web/mobile interface possible," not "the system must be scalable"). The Vision's core claim (0/1/2/3 cell-encoding scheme) is backed by real mechanism detail in the Glossary (§3: "bit 1 marks a top wall and bit 2 a left wall") and the addendum's code citations — this is earned novelty, not a claimed one.

No findings.

## Strategic coherence — strong

The thesis — port behavior faithfully, decouple logic from UI, defer new modes — is legible in the prioritization itself: §4.5's P2 features are explicitly gated behind "the existing features (§4.1-4.4) are fully ported," which is a scope-logic decision following from the thesis (reach parity before extending), not "what's easy first." SM-1 measures the thesis directly (ported + tested + "no class re-creates the legacy 'big_boss' role") rather than a vanity/activity metric — there's no DAU/MAU-style stand-in here, which is the right call for this MVP-scope kind (a problem-solving/technical-debt rewrite, not an engagement play).

No findings.

## Done-ness clarity — adequate

Where the PRD fixes a known legacy defect, done-ness is sharp: FR-13, FR-14, FR-20, FR-21, and FR-23 all carry explicit "Consequences (testable)" bullets that name the exact observable behavior change. But that rigor doesn't extend evenly across all 25 FRs — about half rely on the FR description alone, which is fine for simple, self-evident toggles (FR-6 theme toggle, FR-18 appearance) but leaves two FRs with a genuinely load-bearing gap.

### Findings
- **medium** Unquantified "bounded" in FR-4 and FR-10 (§4.1, §4.2) — FR-4 says maze dimensions are settable "(columns/rows, bounded)" and FR-10 says random-maze generation is "(bounded, with input validation)," but no number appears anywhere in the PRD or addendum. The addendum (§"Duplicated size bounds") only describes the *legacy* hardcoded values (3–50 cols, 3–35 rows) as debt to eliminate ("no single source of truth") — it never states what the rewrite's canonical bounds should be. An engineer implementing FR-4/FR-10 has no way to know what "done" means for the boundary case. *Fix:* either commit to a number (e.g., "reuse the legacy 3–50/3–35 range, now single-sourced from settings instead of duplicated") or mark it `[ASSUMPTION]`/add to Open Questions so it's visibly unresolved rather than silently vague.
- **low** Several FRs (FR-3, FR-9, FR-12, FR-15, FR-17) have no explicit testable-consequence bullet and lean on the addendum for engineering detail (e.g. FR-12's Level mechanics are fully specified only in the addendum's "Level detail" section). This is a reasonable two-tier documentation choice given the addendum exists precisely for this level of detail, but it means FR-12 in isolation (per the Downstream-usability "pulled out alone" test) is under-specified — someone reading only the PRD wouldn't know Level 2's partition-reveal mechanic exists. *Fix:* a one-line pointer from the FR to the relevant addendum section would close the gap cheaply.

## Scope honesty — strong

§5 Non-Goals does real work (architecture reproduction, stack finality, accounts/multiplayer, monetization all explicitly excluded from this milestone). De-scoping is honest, not silent: FR-24/FR-25 are explicitly labeled P2 with a stated reason ("to be tackled after the existing features are fully ported"), and FR-5 carries an inline "Out of Scope" callout pointing to FR-23 rather than leaving the migration-tooling boundary implicit. Open-items density (4 Open Questions, 2 Assumptions) is proportionate to a hobby-stakes PRD — not padded, not suspiciously thin for a document that will drive real Sprint Planning decisions.

### Findings
- **low** Assumptions Index roundtrip is broken (§9 vs. §0, §4.5) — see Mechanical notes.

## Downstream usability — adequate

The PRD explicitly positions itself as chain-top ("It is the reference for downstream phases (architecture, epics/stories, incremental development)," §0), so traceability matters more than it would for a standalone doc. The Glossary (§3) is used consistently — "Sketch," "Classic maze," "Random maze," "Level," "Difficulty" all appear with stable capitalization and meaning across Features, NFRs, and the addendum. FR IDs are globally contiguous 1–25 with no gaps or duplicates, and every cross-reference resolves (FR-23→§8, SM-1→FR-1..23, UJ-1..3→their FR lists all point at real IDs).

### Findings
- **low** Roughly half the FRs are not traced to any User Journey — UJ-1 covers FR-1..5, UJ-2 covers FR-9, FR-10, FR-12, FR-13, FR-15, and UJ-3 (deferred) covers FR-24. That leaves FR-6, 7, 8, 11, 14, 16, 17, 18, 19, 20, 21, 22, 23 (13 of 25) with no journey context — notably FR-14 (HARD mode) and FR-16 (Timer), which are meaningfully interaction-shaped, not just plumbing. §2.2 flags itself as "Lightweight journeys — solo project," so this is a deliberate choice rather than an oversight, and it's defensible under Shape fit — but architecture/UX work drawing on UJs for interaction context will need to reconstruct that context for over half the feature set from the FR text alone. *Fix:* not required at this stakes level; if UJs are extended later, prioritize covering FR-14/16/17 since they're the ones with real interaction nuance.
- **low** FR ID ordering is non-monotonic against document order — see Mechanical notes.

## Shape fit — strong

Correctly scoped for hobby/solo stakes: three UJs, one persona, no stakeholder sign-off apparatus, SM-1/SM-C1 kept to two metrics — no over-formalization. Brownfield accuracy (the dimension the rubric flags as non-negotiable here) checks out under spot-checking: I verified the addendum's code-level claims directly against `Creer_labyrinthes.py`/`Labyrinthes_copy.py` on disk —
- `aller_a_coord` is indeed dead/broken (commented-out call at line 99, undocumented `tk.simpledialog` use at line 114) — matches addendum verbatim.
- `conbinaisons = ["1", "3", "0", "2"]` lookup table exists exactly as quoted (line 856).
- The `r`-shortcut collision is real: `<KeyRelease-r>` is bound to `self.big_boss.reglages` (line 315) and separately to `self.big_boss.recomencer_lab` (line 413), while the Réglages tooltip at line 314 still claims `"(raccourci : 'r')"`.
- `Chrono` is a complete, working class (line 1479) whose instantiation is commented out (`#self.chrono = Chrono(self)`, line 373) — confirms "100% disabled in shipped code."
- The hardcoded HARD-mode color bug is real: line 1041 calls `change_voyant_mode_hard, "ready", "blue"` with `"blue"` literal, exactly as described.
- `Autres/Parametres_defaut.csv`'s header and `parcoureur`/`builder` tagging match the addendum's description exactly.

This level of citation accuracy is exactly what the rubric asks brownfield PRDs to earn, and this one does.

No findings.

## Mechanical notes

- **Assumptions Index roundtrip is broken.** §9 lists two `[ASSUMPTION]` entries (tied to §0 and §4.5), but neither `[ASSUMPTION]` tag appears inline at those locations in the body — §0 and §4.5 read as plain prose with no inline marker. A reader scanning the body for assumptions to confirm with the author would miss both. *Fix:* add the inline `[ASSUMPTION: …]` tag at the point of assertion in §0 and §4.5, or note in §9 that inline tagging was skipped by convention.
- **No `[NOTE FOR PM]` or `[NON-GOAL for MVP]` inline tags anywhere in the document** (confirmed via full-text search) — the PRD instead uses a dedicated §5 Non-Goals section and per-FR "Notes:" fields, which functionally cover the same ground. Not a defect, just a convention deviation worth flagging if this PRD needs to interoperate with tooling that scans for the literal brackets.
- **FR ID ordering is non-monotonic within document order.** §4.2 runs FR-9, 10, 11, 12, 13, then jumps to FR-16, FR-17 (skipping FR-14, FR-15); §4.3 then opens with FR-14, FR-15 before continuing FR-18, FR-19. All 25 IDs (FR-1 through FR-25) are present exactly once globally — no gaps, no duplicates, no broken cross-references — so this is a readability/ordering quirk, not a structural defect.
- Glossary terms (Grid, Cell, Sketch, Level, Difficulty, Classic maze, Random maze, HARD mode) are used with consistent capitalization and meaning everywhere they recur in Features, NFRs, and the addendum — no drift observed.
- UJ protagonists: all three UJs name their protagonist inline ("The author," "The player," "The player") — no floating UJs.
