# Adversarial Review — Divergence Hunter

**Target:** `ARCHITECTURE-SPINE.md` (Labyrinthes, `architecture-Labyrinthes-2026-08-04`)
**Method:** for each Invariant/Convention, construct two hypothetical implementers who each follow the letter of every AD, and ask whether their outputs would actually interoperate.
**Reviewer stance:** adversarial / independent. Not a rewrite of the spine — a list of seams.

---

## Verdict

The spine correctly nails the *big* structural risks it was explicitly written to prevent (the `big_boss` boundary erosion, whole-file settings clobbering, format re-encoding, direct adapter-to-adapter cross-imports). But it fixes the **on-disk/wire contract** (AD-5's `"0"`–`"3"` strings, the CSV shape, the scoped settings API) far more precisely than the **in-memory contract** between the two future implementers who will each write code against `domain/`/`application/`. That gap is where two people who each satisfy every AD to the letter can still hand each other objects that don't fit. The highest-value fix is cheap: pin the domain value-object shapes (§1 below) and tighten AD-9's cross-launch contract (§2) before epics/stories starts generating parallel work. The rest are real but narrower, and several are fine to leave to stories as noted.

---

## Findings summary

| # | Finding | Severity | Disposition |
|---|---|---|---|
| 1 | Domain value-object shapes (`Grid`/`Cell`/`Maze`/`Position`/`Level`/`Difficulty`) are unpinned in-memory | **Critical** | Tighten AD-2 / add a companion AD |
| 2 | AD-9 cross-launch contract underspecifies process model, entry-point signature, and state hand-off | **Critical** | Tighten AD-9 |
| 3 | Lateral `adapters/tkinter/` → `adapters/storage/` import not prohibited, and AD-8's test doesn't catch it | **High** | Tighten AD-1 + widen AD-8's scan |
| 4 | AD-6 "shared" vs "private" scope classification has no rule beyond one example; no single owner of shared-key writes | **Medium-High** | Tighten AD-6 |
| 5 | `MazeRepository` port interface (method signatures, maze-category taxonomy) unspecified beyond "one shared impl" | **Medium** | Accept — sequencing note for Epics/Stories |
| 6 | Migration script (AD-7) output paths vs repository input paths not required to share one source of truth | **Medium** | Accept — note for Epics/Stories |
| 7 | Bounds-validation logic (FR-4/FR-10) not assigned to a layer, risking inconsistent error behavior across apps | **Low-Medium** | Accept — note for Epics/Stories |
| 8 | Settings read-caching semantics (live vs cached-per-session) unspecified | **Low** | Accept — FR-21 doesn't require live cross-app sync |
| 9 | "Re-render after every call" (AD-2) redraw strategy — checked, not actually a cross-adapter risk | **Low / cleared** | No action |

---

## 1. Domain value-object shapes are unpinned — CRITICAL

**The gap.** AD-2 says `Grid`/`Cell`/`Maze` "and other domain value objects are immutable" and that operations "take a state and return a new state." AD-5 pins the **on-disk** encoding (`"0"`–`"3"` strings, bit 1 = top wall, bit 2 = left wall) and the CSV shape. Nothing in the spine pins the **in-memory Python shape** of these objects: field names, container type, coordinate convention, or how `Level`/`Difficulty` (1–4 + the non-numeric "Max" sentinel; 1–3) are represented.

**Concrete adversarial pair.** Take "whoever implements `domain/generation` (FR-10, random maze generation, DFS/backtracking)" and "whoever implements `adapters/tkinter/player` rendering + `Laby_balle`-equivalent movement logic (FR-15)." Both read the spine, both obey AD-1/AD-2/AD-5 to the letter. Nothing stops:

- One choosing `Grid = list[list[Cell]]` addressed `grid[row][col]`, the other assuming `grid[x][y]` (legacy code's `lab_xx`/`lab_yy` naming doesn't disambiguate this either — worth checking against the legacy source before assuming everyone will guess the same convention).
- One representing `Cell` as the raw `str` ("0".."3") straight through the domain layer (arguably compliant with AD-5's "cell encoding stays digits"), the other unpacking it into a `Cell(top: bool, left: bool)` dataclass at the domain boundary and only serializing back to digits at `adapters/storage`. Both are defensible readings of AD-5 ("cell encoding is a preserved *public contract*" — doesn't say public contract stops at the storage boundary vs. extends into the domain API).
- One representing `Entry`/`Exit` as a `(row, col)` tuple, the other as an index into a flattened grid array, a third as a `Cell` reference.
- One representing `Level` as `int | Literal["max"]`, another as an `IntEnum` with `MAX = 5`, a third as a dataclass. The PRD's own addendum shows the *legacy* asymmetry this could reintroduce: Level 2 and Level 4 already used two different reveal-threshold formulas for "a similar concept" (FR-13 exists specifically to fix that) — an unpinned `Level` type invites the same kind of drift to resurface in the rewrite's domain layer instead of the UI layer.

**Why this matters more than it looks.** AD-4 mandates *exactly one* `MazeRepository` implementation shared by both composition roots. That repository has to load/save *some* fixed in-memory `Maze` type — but the spine never says what that type is, only what it serializes to/from on disk. If the Builder-side and Game-side application services end up expecting different in-memory shapes from the same repository (because nobody pinned it and each was written first against their own app's needs), AD-4's "one shared implementation" becomes either unimplementable without one side adapting, or implemented with an implicit, undocumented shape that the next person (e.g. a future web adapter author, exactly the persona AD-1/AD-3 are written to protect) has to reverse-engineer from usage.

This is also why the "conflicting mutable state wrapper" worry (AD-2) is mostly *not* a separate risk: each adapter is expected to own its own mutable "current state" wrapper (Builder's cursor/mode/undo history vs. Game's ball position/level/difficulty/timer), and that's fine — those wrappers are legitimately app-specific and don't need to interoperate. The real interoperability requirement is one layer down: the *immutable domain value* the wrapper holds a reference to (`Maze`/`Grid`/`Cell`) must be the same shape everywhere, because it's what flows through the shared `MazeRepository` and (per FR-8) potentially across a Builder→Game cross-launch hand-off.

**Recommendation.** Tighten AD-2 (or add a short companion AD, e.g. AD-2b "Domain object shapes") to pin, at minimum:
- `Grid` indexing convention (row/col vs x/y, 0-origin, which corner is origin) and container type.
- `Cell`'s in-domain representation (raw digit string end-to-end, vs. a decoded wall-boolean value object with the digit form generated only at the storage boundary) — pick one, don't leave it implicit in AD-5's wording.
- `Maze` = `Grid` + `Position` (entry) + `Position` (exit), with `Position` itself fixed as a single shared type.
- `Level`/`Difficulty` as fixed types, explicitly resolving how "Max" compares/orders against 1–4 given FR-13's "unlockable from Level 2 onward" gating needs an ordinal comparison.

This doesn't need full dataclass definitions at spine altitude — even one worked example per type (a two-line signature) is enough to remove the ambiguity two independent implementers would otherwise resolve differently.

---

## 2. AD-9 cross-launch contract is underspecified — CRITICAL

**The gap.** AD-9 fixes *where* cross-launch wiring lives (composition-root level, no direct `adapters/tkinter/builder` ↔ `adapters/tkinter/player` imports) but not *how* the launch actually happens. Concretely, unaddressed:

- **Process model.** Same Python process (import the other composition root's entry function and call it) vs. a new subprocess (`subprocess.Popen([sys.executable, "-m", "labyrinthes.app.player"])`)? Tkinter's `Tk()` root is a de-facto singleton per process/thread — a second `Tk()` instantiated in the same process while the first's mainloop is running is a well-known footgun (event loop conflicts, `Tcl` interpreter cross-talk). One implementer building `app/builder.py`'s launch-the-game path as an in-process `Toplevel`-parented child window, and the other building `app/player.py`'s launch-the-builder path as a subprocess spawn, would both satisfy AD-9's literal text ("wired at the composition-root level... never import each other directly") while producing two fundamentally incompatible launch behaviors — one that shares process memory and one that doesn't.
- **Entry-point signature.** Nothing states that `app/builder.py` and `app/player.py` must expose a common callable shape (e.g. `def launch(parent: tk.Misc | None = None, initial_maze: Maze | None = None) -> None`). Without that, "app/builder.py can start app/player.py's composition root" is a sentence both implementers can honor with completely different function names, parameter counts, and return types — which is fine in isolation but means whoever wires the *second* direction has to reverse-engineer the first person's ad hoc convention instead of following a documented one.
- **State hand-off, and an asymmetry the spine papers over.** FR-8 says the user can "open the Game from the Builder **without leaving their editing session**" — a reasonably strong implication that the in-progress maze being edited should carry over so it can be tried immediately. FR-19 only requires that standalone-launched Game can open the Builder at all — no stated requirement to hand anything back. AD-9's "and vice versa" phrasing implies a *symmetric* contract, but the FRs it binds (FR-8, FR-19) are not symmetric in their state requirements. A Builder-launch implementer who reads only AD-9 could reasonably build a stateless "just start the other app fresh" launcher (satisfying AD-9's text) while missing FR-8's actual "without leaving their editing session" requirement — and a reviewer checking against AD-9 alone wouldn't catch the miss, because AD-9 doesn't mention state.

**Concrete adversarial pair.** "Whoever implements `app/builder.py`'s launch-the-player call" vs. "whoever implements `app/player.py`'s launch-the-builder call": both avoid direct `adapters/tkinter/*` cross-imports (satisfying AD-9's literal rule), yet one passes a live `Maze` object into a shared-process `Toplevel`, the other spawns a subprocess with no way to receive one — genuinely incompatible if either side's code is ever exercised against the other's harness (e.g. an integration test that launches Builder, edits a maze, triggers FR-8, and asserts the Game sees the same maze — passes for one implementation, fails for the other, and AD-9 as written doesn't tell you which one is "correct").

**Recommendation.** Tighten AD-9 to state explicitly:
- Single-process model (same interpreter, same `Tk()` root reused via `Toplevel`/window-swap — not a second `Tk()` instance, not a subprocess), since that's the only model compatible with FR-8's "without leaving their editing session."
- A standard composition-root entry-point signature both `app/builder.py` and `app/player.py` must expose (parent window handle + optional initial domain state).
- Explicitly note the FR-8/FR-19 state-hand-off asymmetry (Builder→Game carries the in-progress maze; Game→Builder does not need to) so it isn't silently smoothed over by "and vice versa."

---

## 3. Lateral `adapters/tkinter` → `adapters/storage` import path — HIGH

**The gap.** AD-1's dependency direction is stated as `app/ → adapters/ → application/ → domain/`, and AD-3 says UI adapters call "`application/` services (commands/queries)." Read together, the *intent* is clearly that `adapters/tkinter/` should never reach sideways into `adapters/storage/` directly — it should always go through an `application/` service. But no AD states this as a rule, and AD-8's enforcement test is scoped only to `domain/` and `application/` ("scans `domain/` and `application/` source for forbidden imports (`tkinter`, `adapters`)") — it does not scan `adapters/tkinter/` for imports of `adapters/storage/`.

**Concrete adversarial pair.** "Whoever builds the Builder's maze-selector list (FR-9-adjacent, needs to enumerate saved sketches)" vs. "whoever builds the Game's classic-maze selector (FR-9)." One strictly routes every maze read through a `BuilderService`/`PlayerService` method in `application/` (as AD-3 intends); the other, wanting a quick read-only listing, imports `MazeRepository` from `adapters/storage/` directly into `adapters/tkinter/player/` — nothing forbids it, nothing catches it in CI (AD-8's test is silent on this path), and it still satisfies AD-1's literal text since `adapters/tkinter` → `adapters/storage` is technically still "adapters/ → adapters/" not a violation of the stated `app → adapters → application → domain` chain read narrowly. Once one adapter does this, it bypasses any validation/business rules `application/` services were meant to centralize (e.g. FR-4's shared bounds check), and the two apps' storage-access patterns silently diverge from what AD-3 assumed.

**Recommendation.** Tighten AD-1 (or AD-3) with an explicit sentence: "`adapters/tkinter/` may depend only on `application/`, never directly on `adapters/storage/`." Extend AD-8's import-scan test to also flag `adapters/storage` imports inside `adapters/tkinter/`, closing the exact enforcement gap this finding describes.

---

## 4. AD-6 shared/private classification has no general rule — MEDIUM-HIGH

**The gap.** AD-6 fixes the *access pattern* well (`get(scope, key)`/`set(scope, key, value)`, written immediately, no full-file dump — this genuinely closes the legacy clobbering bug at the mechanism level). It gives exactly one worked example of what's `shared` (the FR-4/FR-10 size bounds) and asserts `builder`/`game` are "private," but gives no general rule for classifying any *other* setting, and — more importantly — no rule for **who is allowed to write a `shared`-scope key**.

**Concrete adversarial pair.** "Whoever builds the Builder's general-settings panel" vs. "whoever builds the Game's general-settings panel." The addendum flags that in the legacy app, "Alert on invalid input" (conceptually a Game/random-maze-generation concern, FR-10) leaks into the Builder's settings panel "inherited from the shared `Reglages` component" — precisely the kind of scope-classification mistake AD-6 exists to prevent, yet AD-6 doesn't give either implementer a rule to check a *new* setting against. Two people independently deciding where a given key belongs (e.g., should "confirm before switching mazes," FR-17, be `game`-private, or `shared` since the Builder also has a comparable "confirm before redefining entry/exit," FR-3, prompt?) can reasonably disagree per-key with no spine text to arbitrate. Separately: AD-6 doesn't say whether both apps may write to a `shared` key, or only one is the source of truth for it (e.g., is the FR-4/FR-10 size bound editable from *both* the Builder's and the Game's settings UI, and if so, is last-write-wins acceptable, or does one app own it and the other only reads?). Since AD-6's granular-write mechanism sidesteps the *whole-file* clobber bug, a shared key written from both sides won't silently destroy unrelated settings the way the legacy bug did — but a genuine "shared key edited concurrently from two running instances" race is still structurally possible and unaddressed.

**Recommendation.** Tighten AD-6 with: (a) an explicit, even if short, decision rule for scope classification (e.g., "a setting is `shared` only if both apps must observe the identical value in the same session — everything else defaults to private"), and (b) a structural single-source-of-truth requirement for the *set of shared keys themselves* — e.g., "the shared-key names are declared once, in one module both composition roots import" (mirrors the fix recommended for Finding 3) — so the classification question is settled by code layout, not by two people's independent judgment calls.

---

## 5. `MazeRepository` port interface is unspecified beyond "one shared implementation" — MEDIUM

**The gap.** AD-4 is strong on *singularity* ("exactly one `MazeRepository` implementation... used by both composition roots — no per-app duplicate parsing") but the port's actual interface — method names, how a caller distinguishes classic vs. sketch vs. saved-random mazes (a real distinction: FR-9 lists classics, FR-11 requires saved-random mazes to reappear "in the selector alongside classic mazes" after restart, FR-5 needs sketches kept separate and re-openable) — isn't given, not even a sketch signature, unlike `SettingsRepository` which AD-6 does spell out (`get`/`set`).

**Why this is lower severity than Findings 1–4.** AD-4's singularity requirement substantially self-corrects this: if there is truly only one implementation, whoever writes it necessarily settles the interface for both consumers at once, and both composition roots are forced to code against whatever that one person/PR produced. The residual risk is purely a *sequencing* one: if Epics/Stories splits "define the `MazeRepository` port" and "consume it from the Builder" and "consume it from the Game" into three independently-schedulable stories without an explicit ordering dependency, the two consumer stories could start from divergent assumptions about the interface before the port is actually fixed, producing rework rather than an unenforceable production bug.

**Recommendation.** Accept as out-of-scope for the spine's altitude, but flag explicitly for Epics/Stories: sequence a "define `MazeRepository`/`SettingsRepository` port interfaces" story (or fold it into whichever of Builder/Game storage work lands first) strictly before the *other* app's storage-consuming stories are started in parallel, and make the maze-category taxonomy (classic / sketch / saved-random) an explicit part of that story's acceptance criteria given FR-11's specific requirement that saved-random mazes must show up in the same selector as classics.

---

## 6. Migration script (AD-7) paths vs. repository paths — MEDIUM

**The gap.** AD-7 fixes the *approach* (one-time script, no permanent dual-format shim) and the Deferred section correctly punts "exact migration script design" to stories. What isn't stated anywhere — in the spine or explicitly in the Deferred section — is that the migration script's **output** folder/file naming and the `MazeRepository`/`SettingsRepository`'s **input** folder/file naming must be the same source of truth. This is almost certainly the *intent* behind AD-4's "one shared... implementation, no per-app duplicate parsing," but AD-4 is scoped to Builder-vs-Game duplication, not migration-script-vs-repository duplication.

**Concrete adversarial pair.** "Whoever writes the one-time migration script (AD-7)" vs. "whoever writes `adapters/storage/`'s `MazeRepository`/`SettingsRepository`." If these are different stories/people and each independently invents the new English folder names (e.g. migration script emits `mazes/classic/`, repository reads from `classic_mazes/`), both satisfy AD-7's and AD-4's literal text while producing a broken pipeline — data migrated correctly per FR-23's content-preservation requirement, but unreachable by the app that's supposed to read it.

**Recommendation.** Accept as story-level detail (the spine already correctly defers "exact migration script design"), but add one sentence to that Deferred bullet (or to AD-7) requiring that the new path/naming scheme be declared once (e.g. as constants in `adapters/storage/`) and imported by both the migration script and the repositories, rather than each independently choosing names that happen to need to match.

---

## 7. Bounds-validation logic isn't assigned to a layer — LOW-MEDIUM

**The gap.** AD-6 guarantees the FR-4/FR-10 size bounds (3–50 cols, 3–35 rows) are defined once and read identically by both apps — good, this directly fixes the named legacy defect. But *validating user input against those bounds* (what happens on out-of-range input, what error type/message, whether validation happens in the domain, in `application/`, or ad hoc in each Tkinter form) isn't assigned to a layer by any AD. Two implementers could each read the same shared bound correctly (AD-6 satisfied) yet build divergent validation behavior — e.g., the Builder's `Fen_chose_new_lab`-equivalent silently clamping to the bound, the Game's random-maze dialog raising a domain-level exception with a specific message the Builder never learns to catch or display the same way.

**Recommendation.** Accept — reasonable to leave to Epics/Stories, but worth a story-writer's note: validation against the shared bound should be a single pure function (domain or application layer) both adapters call, not reimplemented per-adapter, so the *behavior* is shared as tightly as the *value* already is under AD-6.

---

## 8. Settings read-caching semantics — LOW

**The gap.** AD-6 guarantees writes are immediate and granular (no clobbering on close). It doesn't say whether an adapter must call `get()` fresh every time it needs a value, or may cache a value in memory for the session. If Builder and Game run simultaneously and one changes a `shared` value, the other might not see it until its next `get()` call (or restart) depending on whether its implementer cached it.

**Why this is low severity.** FR-21's actual testable consequence is scoped to "does not silently overwrite... on close" — it does not require live visibility of changes between two simultaneously-running instances. Both a caching and a non-caching implementer satisfy every stated FR/AD; the observable difference (does the other app's change show up immediately, or only after restart) is a UX nuance, not a data-loss bug, and is consistent with the existing pattern elsewhere in the PRD (FR-11: a saved random maze only needs to "appear in the selection list after the application restarts," not live).

**Recommendation.** Accept as-is; no spine change needed. Optionally note for stories that restart-to-see-shared-changes is an acceptable, precedented UX (matches FR-11), so nobody over-engineers live cross-process sync.

---

## 9. "Re-render after every call" — checked, cleared

Considered whether AD-2's "each adapter... re-renders after every call" leaves room for two adapters to diverge in a way that breaks interoperability (e.g. one doing full redraws, one doing incremental diffs). This is real implementation latitude, but it's **intra-adapter**, not cross-adapter: Builder's renderer and Player's renderer never need to interoperate with each other's redraw strategy, only with their own service layer's return values (covered by Finding 1). No action needed.

---

## Overall recommendation

Before Epics/Stories starts generating parallel work, prioritize:
1. Pin domain value-object shapes (Finding 1) — this is the one gap that would silently break AD-4's "one shared repository" promise if left open.
2. Tighten AD-9's cross-launch contract (Finding 2) — concrete enough today to cause a real FR-8 regression (losing "without leaving their editing session") if the two launch directions are built independently.
3. Close the AD-8 enforcement gap for lateral adapter imports (Finding 3) — cheap, mechanical fix (extend an existing test) with disproportionate payoff.
4. Tighten AD-6's shared/private classification rule (Finding 4) — currently one example standing in for a general principle.

Findings 5–8 are legitimate seams but are reasonable to leave for Epics/Stories to pin down, provided the sequencing notes above are actually carried forward into the relevant stories rather than silently dropped.
