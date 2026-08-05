# Rubric Walk Review — ARCHITECTURE-SPINE.md UPDATE (Labyrinthes, 2026-08-05)

Reviewer role: independent rubric walker, fresh context, reviewing an in-place **amendment** to an already-finalized spine (not a full re-review). Scope per the review brief: AD-3 (`Maze.id: MazeId | None`), AD-6 (additive `MazeId` header line), AD-8 (migration backfill), new AD-12 (`RecordsRepository`), the two new Capability Map rows (Personal Records, First-activation explainers), and the Deferred section edits.

Target: `_bmad-output/planning-artifacts/architecture/architecture-Labyrinthes-2026-08-04/ARCHITECTURE-SPINE.md`
Checked against: `.memlog.md` (full), `prd.md` (specifically FR-27, FR-28, §2.2 UJ-2, §3 Glossary, §8 OQ4/OQ5).

## Verdict

The update's central design calls (single `RecordsRepository`, comparison logic parked in a new `application/RecordsService`, `MazeId` as an additive CSV header keyed identity rather than a path-based or side-mapping key) are sound and correctly resolve the real divergence risk FR-27 introduces. However, the update leaves one direct, unresolved textual contradiction with an unchanged prior AD (AD-4's port count), introduces one new unpinned shared type (`Duration`) that two separate features (FR-16 Timer, FR-27 Records) could each invent independently, and reuses a Deferred bullet whose claims are now stale against the very AD-12 material it was just folded into. None of these require reopening the update's actual trade-offs — all are localized text fixes — but they are exactly the class of gap a rubric walk exists to catch before re-closing.

**Recommend:** fix before re-closing, in priority order below.

---

## 1. [CRITICAL] AD-4's "only two ports" claim now directly contradicts AD-12

AD-4's Rule, unchanged by this update, reads:

> "`MazeRepository` and `SettingsRepository` are the only ports defined in `application/`, implemented under `adapters/storage/`."

AD-12 (new) defines a third port, `RecordsRepository`, also living in `application/`/`adapters/storage/` under the exact same paradigm AD-4 describes ("Only persistence is a port"). AD-4's enumeration was not touched by this update, so as written it now asserts something the spine's own new material contradicts on the same page. An implementer who reads AD-4 in isolation — plausible, since AD-4 is the AD that answers "how many ports am I allowed to define?" — is told only two exist, and would have no textual basis from AD-4 itself to conclude `RecordsRepository` is sanctioned; they'd have to notice AD-12 separately and reconcile the discrepancy themselves. This is precisely the kind of drift the spine format exists to prevent: two ADs asserting different structural facts about the same system.

This is not a deep design problem — AD-4's underlying principle ("only persistence is a port, rendering isn't") still holds fine with three persistence ports instead of two — but the literal enumeration is now false.

**Recommendation:** amend AD-4's Rule to read "`MazeRepository`, `SettingsRepository`, and `RecordsRepository` are the only ports..." (or more durably, drop the closed enumeration and say "the only ports defined in `application/` are persistence ports implementing this pattern — currently `MazeRepository`, `SettingsRepository`, `RecordsRepository`"). Also add AD-4 to the Personal Records Capability Map row's "Governed by" list, since it's the AD that authorizes RecordsRepository's existence as a port in the first place (currently lists AD-1, AD-3, AD-6, AD-8, AD-9, AD-12, but not AD-4).

## 2. [HIGH] The "exact interfaces" Deferred bullet now contradicts AD-12 (and, pre-existing, AD-7) — and its taxonomy claim is stale against AD-3

The memlog records that this update "folded `RecordsRepository` into the existing 'exact interface'/'exact on-disk format' deferred bullets." The result:

> "**`MazeRepository`/`SettingsRepository`/`RecordsRepository` exact interfaces (method signatures).** AD-5/AD-7/AD-12 fix singularity and access pattern; the precise method signatures and the classic/sketch/saved-random taxonomy are left to Epics/Stories..."

Two separate problems, both now live inside the exact bullet this update edited:

- **Method signatures aren't actually undecided for `RecordsRepository`.** AD-12's Rule already pins them concretely: `get_best(maze_id, level, difficulty) -> Record | None`, `list_all() -> list[Record]`, `set_best(record)`, plus `RecordsService.record_completion(maze, level, difficulty, time)`. (The same is true, pre-existing, of `SettingsRepository` — AD-7 already pins `get(scope, key)`/`set(scope, key, value)` — so this bullet's premise was already shaky before this update touched it, and folding `RecordsRepository` in doubles down on the same problem rather than fixing it.) A reader who trusts the Deferred bullet's literal claim ("left to Epics/Stories") over AD-12's literal Rule could reasonably conclude the port shape is still open for a future story to decide — including adding methods AD-12 explicitly rules out (e.g., a "record a completion and decide if it's a new best" method on the port itself, which AD-12's Prevents clause exists specifically to block).
- **The taxonomy claim is stale.** "the classic/sketch/saved-random taxonomy are left to Epics/Stories" — but AD-3 already pins this exhaustively, including a fourth value this bullet doesn't even list: `kind tag (classic | sketch | saved-random | generated, per FR-5/FR-9/FR-11)`. This clause predates the Personal Records update (AD-3's kind tag was already finalized in the prior Update pass), but since this update explicitly re-touched this same bullet, it's now inside the update's scope and should have been caught by the same edit pass that added `RecordsRepository`.

**Recommendation:** narrow the bullet to what's genuinely still open — e.g., "exact error-handling conventions (does `get`/`get_best` return `None` or raise on a miss?), additional convenience/query methods beyond the minimal set AD-7/AD-12 already pin, and the on-disk serialization of each" — and drop the "classic/sketch/saved-random taxonomy... left to Epics/Stories" clause entirely, since AD-3 already settles it.

## 3. [HIGH] `Record.time: Duration` introduces a new shared type that nothing pins — a live divergence risk against FR-16's Timer

AD-12 declares `Record` as `maze_id: MazeId, level: Level, difficulty: Difficulty, time: Duration, set_at`. `MazeId`, `Level`, and `Difficulty` are all types AD-3 (or this update, for `MazeId`) explicitly pins — layer, shape, ordering. `Duration` is not pinned anywhere in the document: not in AD-3 (which is exactly the AD whose stated purpose is "pin domain object shapes... prevent two independent implementers inventing incompatible shapes for the same concept"), not in AD-12 itself beyond the bare type name, and not anywhere else in the spine. Grepping the whole document, `Duration` appears exactly once, in this one line.

This matters concretely: FR-16 (Timer) is a separate, not-yet-built feature that will need its own time/duration representation for tracking elapsed solve time and an optional time limit — and AD-12's `RecordsService.record_completion(maze, level, difficulty, time)` is called *from* the Player screen at the moment a run completes, meaning the Timer feature's output value is exactly what gets threaded into `Record.time`. If the Timer feature is built first and picks, say, a raw `float` of seconds or `datetime.timedelta`, and `RecordsService`/`Record` independently assume a different `Duration` type (or vice versa), the two features literally cannot compose without an ad hoc conversion nobody decided on. This is the same divergence class AD-3 exists to prevent for `Position`/`Level`/`Difficulty` — it just wasn't extended to cover the new type this update introduces.

**Recommendation:** either (a) add `Duration` to AD-3's pinned-shapes list (layer, e.g. domain/, and shape, e.g. a thin wrapper over seconds) alongside `Position`/`MazeId`/`Level`, since it's now load-bearing for both FR-16 and FR-27, or (b) explicitly note in AD-12 that `Duration`'s shape is deliberately deferred and name where that decision must land before both FR-16 and FR-27 stories start (mirroring the Deferred section's existing "sequence a 'define the port interfaces' story before consumers" pattern).

## 4. [MEDIUM-HIGH] AD-8's migration backfill doesn't mandate reusing the same serialization path as `MazeRepository`'s writer for the new `MazeId` header line

AD-8's Rule states the migration script "mints and writes AD-6's `MazeId` header line for every legacy classic maze it converts." AD-8's Prevents clause is explicit that its whole purpose is to stop "the migration script and the repositories independently inventing mismatched new folder/file names" — and its Rule already applies a fix for that specific risk (path/naming constants "declared once... imported by both the migration script and the repositories"). But that single-source-of-truth treatment is not extended to the `MazeId` header line's actual on-disk serialization (exact position, delimiter, format) — the migration script is described as writing that line itself, with no stated requirement that it call through the same `MazeRepository` write path (or a shared serializer) that produces the header line for freshly-saved classic/saved-random mazes.

Since the migration script is explicitly "standalone" and "retired" after running once (AD-8's own framing), if it hand-writes the `MazeId` line slightly differently from how `MazeRepository`'s own writer would (see also finding 5, since the line's position isn't itself pinned), the mismatch becomes permanent and silent — baked into every migrated classic maze file, discovered only when `MazeRepository`'s reader chokes on migration output. This is exactly the divergence-between-independent-writers class AD-8 exists to prevent, just not fully closed for this specific new field.

**Recommendation:** add a clause to AD-8's Rule requiring the migration script to construct the `MazeId` header line via the same write/serialization function `MazeRepository` uses (not a hand-rolled equivalent), the same way path/naming constants are already required to be shared.

## 5. [MEDIUM] AD-6's `MazeId` header line position is under-specified for two independent writers

AD-6's amended Rule places the new line "alongside the existing header lines before the grid rows" — this doesn't state whether it comes before or after the entry/exit header lines, nor how a reader disambiguates a 2-header-line file (`sketch`/`generated`, no `MazeId`) from a 3-header-line file (`classic`/`saved-random`, has `MazeId`) when parsing. AD-6's own Rule text asserts "existing fields keep their exact meaning and position" — which, read carefully, implies the only non-breaking placement is *appended* after the existing header lines (inserting before would shift the entry/exit lines' positions, which the same sentence forbids) — but this is an inference a reader has to make, not a stated fact. Given AD-6 exists specifically to prevent Builder/Game divergence on this exact format, and now a third writer (the migration script, per finding 4) also has to conform to it, this is worth pinning explicitly rather than left to careful reading.

**Recommendation:** state directly in AD-6 (or accept it explicitly as one of the Deferred "exact on-disk format" items, and say so) that the `MazeId` line is appended after the existing entry/exit headers, immediately before the grid rows, so its presence/absence is detectable purely from line count relative to the known grid dimensions.

## 6. [MEDIUM] Consistency Conventions' "Data & formats" row is silent on this update's format change

The table row (untouched by this update) still reads: "Maze CSV = entry/exit header + grid rows (FR-20, AD-6)." It doesn't mention the new `MazeId` header line AD-6 now describes, nor anything about how Records are keyed/stored. This isn't false, just incomplete — a reader skimming the summary table (the doc's fast-reference layer, by design) for "what does the maze file look like" gets a stale picture that AD-6 itself has already moved past.

**Recommendation:** append a clause, e.g. "... plus an additive `MazeId` header line for `classic`/`saved-random` mazes (AD-6)."

## 7. [LOW] AD-3's mint-vs-preserve rule for `MazeId` on re-save is inferable, not explicit

AD-3 says `MazeId` is "minted once, at the same save operation that assigns `classic` or `saved-random`... and carried unchanged thereafter." This correctly implies (a maze already carrying an id must keep it on every subsequent save, e.g. via `Edit in Builder` → re-save), but never states the operational rule a `MazeRepository.save()` implementer actually needs: *if the `Maze` value already has a non-`None` id, write it unchanged; only mint a fresh one when the incoming `Maze.id` is `None` and the kind is becoming `classic`/`saved-random`.* Low risk since it's a short, fairly unambiguous inference, but worth a one-clause spell-out given `MazeRepository` is exactly the kind of code AD-3 is meant to keep two independent builders from diverging on.

---

## Standard good-spine checks

- **Every new/amended AD's Rule enforceable and closes its stated divergence:** AD-12's core shape (single repository, comparison logic in `application/`, minimal mechanical port) is enforceable and correctly closes the "Home/Player invent different comparison logic" risk it names. AD-3/AD-6/AD-8's `MazeId` scheme correctly resolves the identity-key fork noted in the memlog (path-based vs. side-mapping vs. additive header) — Max's chosen third option is coherently threaded through all three ADs. The gaps found above are refinements/omissions, not rejections of the core calls.
- **Nothing under Deferred lets two units diverge on something that should be pinned:** mostly fine (the display-grouping bullet is a legitimate, correctly-scoped UX-layer deferral) — except the "exact interfaces" bullet (finding 2), which actively *creates* divergence risk by contradicting already-pinned material rather than neutrally deferring something genuinely open.
- **Does the amendment weaken or contradict any prior AD:** yes — AD-4 (finding 1), and the pre-existing-but-now-doubly-relevant tension with AD-7/AD-3 inside the Deferred bullet (finding 2). No other prior AD (AD-1, AD-2, AD-5, AD-7, AD-9, AD-10, AD-11) is weakened; AD-1's "adapters carry no business logic" and AD-9's boundary enforcement are, if anything, reinforced by AD-12's explicit RecordsService/RecordsRepository split.
- **Anything left silent that the altitude should own:** the `Duration` type (finding 3) is the clearest case — a shared value type two features now depend on, with no home. The MazeId line's exact position (finding 5) is a borderline case between "spine should pin" and "legitimately below-altitude detail already covered by the Deferred 'exact on-disk format' bucket" — flagged as medium rather than high for that reason.
- **Document stays lean:** yes — one new AD, two Capability Map rows, and proportionate Deferred edits; no duplication, no new section sprawl.

## Summary of Findings

| # | Severity | Finding |
|---|---|---|
| 1 | CRITICAL | AD-4's Rule still says `MazeRepository`/`SettingsRepository` are "the only ports" — directly contradicted by AD-12's new `RecordsRepository` port, unamended by this update |
| 2 | HIGH | Deferred "exact interfaces" bullet claims `RecordsRepository`'s method signatures (and the classic/sketch/saved-random taxonomy) are still open, when AD-12 already pins the former and AD-3 already pins the latter (including a 4th `generated` value the bullet omits) |
| 3 | HIGH | `Record.time: Duration` introduces a new shared type pinned nowhere — real divergence risk between the not-yet-built FR-16 Timer feature and FR-27's RecordsService, which must agree on its shape to compose |
| 4 | MEDIUM-HIGH | AD-8 doesn't require the migration script's `MazeId`-header backfill to reuse `MazeRepository`'s own write path, risking a silent, permanent format mismatch between migrated and freshly-written files — exactly the divergence class AD-8's Prevents clause targets |
| 5 | MEDIUM | AD-6's `MazeId` header line position ("alongside the existing header lines before the grid rows") isn't pinned precisely enough for two independent writers (repository, migration script) to agree without inference |
| 6 | MEDIUM | Consistency Conventions "Data & formats" row wasn't updated to mention the new `MazeId` header line or Records' storage shape |
| 7 | LOW | AD-3's "mint once, carry unchanged" rule for `MazeId` doesn't explicitly spell out the operational mint-vs-preserve check a `MazeRepository.save()` implementer needs on re-save |
