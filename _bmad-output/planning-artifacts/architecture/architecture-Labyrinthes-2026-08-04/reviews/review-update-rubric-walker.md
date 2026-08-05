# Rubric Walk Review — ARCHITECTURE-SPINE.md UPDATE (Labyrinthes)

Reviewer role: independent rubric walker, fresh context, reviewing an in-place **amendment** to an already-finalized spine (not a full re-review). Scope is the UX-driven update described in `.memlog.md` entries 22–25: AD-10's single-shell rewrite, AD-9's scan widening, the directory tree / mermaid diagram / Capability Map changes, AD-5/AD-7 wording changes, and the new Personal Records Deferred bullet.

Target: `_bmad-output/planning-artifacts/architecture/architecture-Labyrinthes-2026-08-04/ARCHITECTURE-SPINE.md`
Checked against: `.memlog.md` (full), `prd.md`, `EXPERIENCE.md`, `DESIGN.md`.

## Verdict

The update correctly executes its stated intent — single composition root, Home-routed navigation, widened AD-9 scan, Home added to the directory tree/mermaid/Capability Map — and I found no leftover stale reference to the old two-composition-root model anywhere in the document. However, the rewritten AD-10 paragraph has one genuine internal contradiction about whether Game→Builder navigation carries state, and it drops a UX nuance the review brief specifically asked me to check for (Edit-in-Builder's conditional availability). There's also one real cross-reference inconsistency introduced by this very update: the new Capability Map "Home" row cites AD-11 as a governing AD, but AD-11 itself was not widened to bind/cover `adapters/tkinter/home`. Both are fixable with small, localized edits — nothing here requires re-opening the update's actual decisions.

**Recommend:** fix before re-closing (not critical-blocking, but both bear directly on the two things this update exists to get right — AD-10's accuracy and AD-9/AD-11's completeness).

---

## 1. AD-10 accuracy against EXPERIENCE.md's Information Architecture / Navigation model

### 1a. [HIGH] AD-10's Rule text contradicts itself on whether Game→Builder navigation carries state

The rewritten Rule reads (emphasis mine):

> "...the Builder's `Test in Player` action passes the in-progress `Maze` straight to the Player screen; the Player's `Edit in Builder` action **does the mirror** without needing to hand anything back. This preserves the FR-8/FR-19 asymmetry already noted (Builder→Game carries state; **standalone Game→Builder does not need to**)."

"Does the mirror" of "passes the Maze straight to the Player screen" can only mean Edit-in-Builder passes the Maze straight to the Builder screen — i.e., it *does* carry state, matching EXPERIENCE.md UJ-B step 7 ("jump straight back to his exact editing session — no re-navigation through Home, **no re-opening the file**"), which only makes sense if the Maze/file reference travels with the navigation. The very next sentence then asserts the opposite for the same direction: "standalone Game→Builder does not need to [carry state]." Read together, the paragraph both affirms and denies that Game→Builder carries state, in two adjacent sentences about what looks like the same transition.

The likely intended reconciliation — "standalone" (FR-19, no maze in context, e.g. a bare top-bar/Home-routed nav to Builder) is a *different* transition from the maze-scoped "Edit in Builder" contextual action, and only the former is state-free — is plausible, but the text never draws that distinction explicitly. As written, an implementer cannot tell from AD-10 alone whether `Edit in Builder` needs a state-carrying code path or not, which is exactly the kind of ambiguity AD-10 exists to close off (per its own "hands live in-memory domain state directly, no serialization hop" framing).

**Recommendation:** split the asymmetry sentence to name both Game→Builder cases separately, e.g.: "...FR-8 always carries state (Test-in-Player); FR-19's bare/standalone Builder launch does not; the Edit-in-Builder contextual action is a third case that *does* carry state, mirroring Test-in-Player." Or simplify by dropping the now-misleading "does not need to" clause and letting the Edit-in-Builder example stand on its own.

### 1b. [HIGH] AD-10 omits the "traces back to a Builder-editable source" caveat — Edit-in-Builder's conditional availability

EXPERIENCE.md's Navigation model is explicit that `Edit in Builder` is **not universally available**: it "exists from a maze context in the Player wherever a maze traces back to a Builder-editable source (classics and saved randoms — not procedurally-generated-and-unsaved mazes, which have no Builder file to open)."

AD-10's Rule presents `Edit in Builder` unconditionally — "the Player's `Edit in Builder` action does the mirror without needing to hand anything back" — with no mention that the action is only offered for some maze kinds. This is architecturally material, not just a UI-copy detail: it means the Player screen (or the router) needs a way to know, from the domain state alone, whether the currently-loaded `Maze` has a Builder-editable backing file before it can decide whether to expose the action at all. That determination plausibly hangs off AD-3's `Maze` kind tag (`classic | sketch | saved-random`) — but AD-3's enum has no explicit slot for "freshly generated, not yet saved" (the exact case EXPERIENCE.md calls out as *not* eligible), so it's not obvious from the spine alone how a screen would compute that flag today. AD-3 is out of this update's scope and I'm not asking it be reopened here, but AD-10 should at minimum name the constraint so a story doesn't build an unconditional `Edit in Builder` action against it.

**Recommendation:** add a clause to AD-10's Rule (or Prevents) naming the conditional availability, e.g.: "`Edit in Builder` is only offered when the current `Maze`'s kind indicates a Builder-editable on-disk source (`classic`/`saved-random`); an unsaved procedurally-generated maze has none and the action is not offered." Flag as a Deferred/Epics-level follow-up that AD-3's kind tag (or an adjacent flag) needs to be able to answer this.

### 1c. [LOW] "Deliberate exception" framing not restated

EXPERIENCE.md frames Test-in-Player/Edit-in-Builder explicitly as a *deliberate exception* to Home-only routing, and DESIGN.md's Do's/Don'ts table encodes the same pair as one locked rule ("Route Builder ↔ Player through Home, except the explicit Test-in-Player / Edit-in-Builder contextual actions"). AD-10's Prevents clause states the Home-router rule but doesn't explicitly flag that Test-in-Player/Edit-in-Builder are a *named, bounded* exception to it (as opposed to, say, an oversight in the Rule that a future reviewer might "fix" by routing them through Home too). Not a coherence bug — the Rule text does describe the mechanism accurately — but a one-clause addition ("these are the sole exceptions to Home-only routing") would remove any ambiguity for a future reader. Polish only.

## 2. Is AD-9's enforcement-scan update sufficient?

AD-9's Rule now explicitly covers `adapters/tkinter/home` alongside `builder`/`player` for the lateral-import ban, and its Binds line lists `domain/`, `application/`, `adapters/tkinter/` (broad enough to include `home`). This matches AD-10's new three-screen model and the memlog's stated intent. I found no other location in the document that still assumes two composition roots — grepped for `builder.py`/`player.py`/`Lab_builder`/`Parcoureur_labs`/"two separate"/"independently launchable" and the only hits are AD-10's own (correctly historicized) references to the pattern it supersedes.

### 2a. [MEDIUM] AD-11 was not widened to cover `adapters/tkinter/home`, but the Capability Map now cites AD-11 as governing Home

This is the one place the update's "touch everything that referenced the old two-root model" sweep appears to have missed a spot — not a stale reference to the old model, but a new inconsistency the update itself introduces. The memlog says "Capability Map gained a Home row," and that row now reads:

> `Navigation shell / Home ... | adapters/tkinter/home, app/ | AD-10, AD-11`

But AD-11 itself still reads (Binds and Rule both untouched by this update):

> **Binds:** `adapters/tkinter/builder`, `adapters/tkinter/player`, FR-6, FR-17, FR-18
> **Rule:** generic ... blocks ... live in `adapters/tkinter/common/`, imported by both `builder/` and `player/` — not duplicated per app.

Home is a real screen with its own top-bar (`icon-btn` for Settings/theme, `settings-window`, breadcrumb-Home affordance) per EXPERIENCE.md's Component Patterns table ("Top bar / breadcrumb-Home-button | All screens"; "settings-window | Reached from any top bar"), so it plausibly *should* consume the same `common/` toolkit — but AD-11's Rule as written doesn't say so, and its Binds line doesn't list `adapters/tkinter/home` at all. As it stands, the Capability Map asserts AD-11 "governs" Home's capability while AD-11's own text is silent on Home — a citation that doesn't resolve if you go read the AD it points to.

**Recommendation:** either widen AD-11's Binds/Rule to include `adapters/tkinter/home` (three-way, matching AD-9/AD-10's treatment), or drop AD-11 from the Home row of the Capability Map if the intent is that Home doesn't consume `common/`. Given EXPERIENCE.md's shared top-bar/settings-window pattern across all three screens, widening AD-11 is almost certainly the right fix and is a one-line change.

## 3. Directory tree / mermaid / Capability Map / AD-5 / AD-7 consistency

All internally consistent and mutually reinforcing:

- Mermaid diagram and directory-tree prose both describe `app/` as "one composition root ... owns the single Tk() root and the screen router" — matches AD-10's Rule verbatim in spirit.
- Directory tree's `adapters/tkinter/` block lists `common/`, `home/`, `builder/`, `player/` in that order, matching AD-11's `common/` framing and AD-10's three-screen model.
- AD-5's Rule ("used by every screen that needs it (Home, Builder, Player) through the shell's single composition root") and AD-7's Rule ("used by every screen that needs it ... mirroring AD-5's rule") are both updated away from "both composition roots," consistent with each other. [LOW polish] AD-7's phrasing is slightly less explicit than AD-5's — it says "every screen that needs it" but doesn't repeat "through the shell's single composition root" — a minor asymmetry in phrasing, not a substantive gap (AD-7 already cross-references AD-5 in the same sentence, so the reader isn't left guessing).
- No leftover `app/builder.py` / `app/player.py` mentions found anywhere (grepped the full document).
- Capability Map's other rows (Construction/Builder, Game selection & progression, Game modes & presentation) were not touched by this update and remain internally consistent with the AD numbering as amended — no renumbering occurred so no cross-reference broke.

The one exception is the AD-11/Home citation covered in finding 2a above.

## 4. Personal Records Deferred bullet — scope accuracy

Accurate and appropriately hedged. The bullet:

- Correctly attributes the concept's origin to `EXPERIENCE.md`'s Home surface, not the PRD.
- Correctly states it is not in FR-1–FR-25 and frames it as "a genuine scope addition, not yet architected."
- Records Max's actual call (update the PRD first via `bmad-prd`, don't extend the architecture yet) without silently deciding it here.
- The "likely shape" sentence (a `RecordsRepository` port, mirroring AD-5/AD-7) is phrased with hedging language ("Likely shape once it is," "probably") and lives entirely inside the Deferred section, not as a new AD or Rule — so it doesn't accidentally create a binding architecture decision. This is exactly the right way to park a scope addition: informative for whoever picks it up later, but nothing here is enforceable or referenced by any AD/Capability Map row today.
- It correctly replaces the now-stale "UX run stalled at draft" Deferred bullet (confirmed: that bullet no longer appears anywhere in the current Deferred section).

No issue found here.

## 5. Standard good-spine checks

- **Every AD's Rule still enforceable:** yes, with the one caveat noted in 2a (AD-11's Rule is enforceable as literally written, just incomplete relative to what the Capability Map now claims it governs). AD-9's scan (the update's core enforcement mechanism) is mechanically sound and correctly widened.
- **Nothing new in Deferred lets two units diverge:** confirmed — the only new Deferred bullet (Personal Records) explicitly blocks further architecture work behind a PRD update, so there's no half-specified surface for two stories to build against differently.
- **Document stays lean:** yes. The update is additive but proportionate — AD-10's Rule paragraph did grow, and per finding 1a it grew in a way that introduced ambiguity rather than length for its own sake, but no new AD was added, no section was duplicated, and the Deferred-bullet swap (Personal Records for the stale UX-draft note) was a net-neutral edit, not bloat.
- **Sources frontmatter:** correctly updated to include `DESIGN.md`/`EXPERIENCE.md` alongside the PRD docs, matching what this update actually drew on.
- **Status field:** frontmatter still reads `status: final` while the memlog's own last entry says a Reviewer Gate pass (this one) is pending before re-closing. Not a defect — this is normal in-flight amendment sequencing — but worth Max re-confirming `final` is re-affirmed (not silently left over) once this gate closes.

## Summary of Findings

| # | Severity | Finding |
|---|---|---|
| 1a | HIGH | AD-10's Rule paragraph contains two adjacent, contradictory claims about whether Game→Builder navigation carries state (Edit-in-Builder "does the mirror" vs. "standalone Game→Builder does not need to [carry state]") |
| 1b | HIGH | AD-10 omits EXPERIENCE.md's "traces back to a Builder-editable source" caveat — presents `Edit in Builder` as unconditionally available when it isn't, and doesn't flag that AD-3's `Maze` kind tag has no slot for the "unsaved generated maze" case the caveat depends on |
| 2a | MEDIUM | Capability Map's new Home row cites AD-11 as governing, but AD-11's Binds/Rule were not widened to mention `adapters/tkinter/home` — a self-inconsistent cross-reference introduced by this update |
| 1c | LOW | AD-10 doesn't explicitly label Test-in-Player/Edit-in-Builder as the *sole, bounded* exception to Home-only routing (implied but not stated) |
| §3 | LOW | AD-7's Rule phrasing is slightly less explicit than AD-5's parallel wording ("through the shell's single composition root") — cosmetic asymmetry only |
| §5 | INFO | `status: final` in frontmatter predates this Reviewer Gate pass closing — expected in-flight state, flag for Max to re-confirm at close |
