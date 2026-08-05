# Adversarial Review — Update Pass (AD-10 single-shell amendment)

**Target:** `ARCHITECTURE-SPINE.md` (Labyrinthes, `architecture-Labyrinthes-2026-08-04`), scoped to the update triggered by the finalized UX (memlog entries 29–32): AD-10's amendment, AD-9's widened scan, the directory tree, and the Capability Map's new Home row.
**Method:** for each amended rule, construct two hypothetical future implementers who each follow the letter of the amended text, and ask whether their outputs would interoperate.
**Reviewer stance:** adversarial / independent. Not a rewrite — a list of seams introduced or left open by this specific update.

---

## Verdict

The amendment does what it set out to do at the macro level: it correctly retires the two-composition-root/cross-launch model in favor of one shell, and in doing so it **closes** the prior full review's Finding 2 (the "second `Tk()` instance vs. subprocess" ambiguity) — with only one composition root left, that class of divergence structurally can't occur anymore. Good, credit where due.

But the amendment buys that simplification by introducing a new, thinner joint — the `mount(parent) -> Frame` "common screen interface" — and pins it only loosely (an "e.g." example, not a contract). That joint is now the single place where a router-builder and three screen-builders must agree, and the amendment doesn't give them enough to agree by construction. There's also a real, PRD-grounded gap in AD-3's Maze kind tag for gating `Edit in Builder` correctly, and two documentation-consistency gaps (Settings' status relative to the router; AD-11/Capability Map disagreement about whether Home is a `common/` consumer) that would send two careful readers of the same spine to different conclusions. None of these are as severe as the pre-amendment Critical findings, but the highest one (the screen interface) is close.

---

## Findings summary

| # | Finding | Severity | Disposition |
|---|---|---|---|
| 1 | `mount(parent) -> Frame` screen interface underspecified: state type, screen-registration key, and — more seriously — a granularity mismatch against EXPERIENCE.md's breadcrumb model | **High** | Tighten AD-10 |
| 2 | AD-3's `classic \| sketch \| saved-random` kind tag has no slot for a freshly-generated, not-yet-saved random maze, which is exactly the case EXPERIENCE.md's `Edit in Builder` caveat needs to exclude | **High** | Tighten AD-3 (or AD-10's reference to it) |
| 3 | Settings' relationship to the router is never stated in AD-10, and the Capability Map's "routes to ... Settings" wording reads as router-navigation when AD-11 + EXPERIENCE.md both actually place it elsewhere (a `common/`-hosted dialog, not a router screen) | **Medium** | Tighten AD-10 or the Capability Map wording |
| 4 | AD-11 not amended to add `adapters/tkinter/home` as a `common/` consumer, yet the Capability Map's Home row cites AD-11 as governing it — the two disagree | **Medium** | Tighten AD-11 |
| 5 | Capability Map's Home row lists no `application/`/`domain/` dependency and names no Home-side service, leaving "does Home ever need `application/`" unanswered for whoever eventually wires a "resume last session"-style affordance | **Low-Medium** | Accept — note for Epics/Stories, revisit if Personal Records lands |
| 6 | Removing the old "Toplevel/window-swap, never a second `Tk()`, never a subprocess" language | **Info / cleared** | No loss — see analysis |
| 7 | AD-9's lateral-import matrix still doesn't include `adapters/tkinter/common` as a party, so a backward `common/` → `home/builder/player` import would go uncaught | **Low** | Accept — note alongside any future AD-9 edit |

---

## 1. The `mount(parent) -> Frame` screen interface is the new thin joint — HIGH

**The text.** AD-10: *"Each screen implements a common interface (e.g. `mount(parent) -> Frame`, given an optional initial domain state) so the router can swap them uniformly."*

This is the mechanism the whole amendment rests on — it's what lets "Home, Builder, and Player are screens registered with that router" be true in practice. But it's introduced with "e.g.", i.e. as an illustrative example, not a pinned contract. Three concrete sub-gaps:

**(a) The state parameter's type is left to inference.** "An optional initial domain state" is never typed. In practice it needs to double as at least two different things depending on which screen receives it: for Builder, "the `Maze` to open, or `None` for a blank New Maze flow"; for Player, "`None` → land on the maze-selection screen, or a `Maze` → skip straight to gameplay on it (this is literally how `Test in Player` has to work)." AD-3 already defines `Maze` — a one-line note ("typically a `Maze`, per AD-3") would remove the ambiguity for near-zero cost. As written, whoever builds the router and whoever builds Player's `mount()` could each independently assume the parameter means something narrower (e.g. the Player-side implementer builds `mount(parent, maze: Maze | None)` while the Home-side router-caller, having never been told the type, passes a bare dict of "navigation intent" instead) and only discover the mismatch at integration.

**(b) The screen-registration mechanism is unnamed.** "Registered with that router" doesn't say whether a screen is identified by a string key, an enum member, or the class/factory object itself. Two people — whoever writes Home's "go to Builder" button handler and whoever writes `app/`'s router dispatch table — need to agree on this key namespace independently, since Home (per AD-10 itself) never imports `adapters/tkinter/builder` directly to reference it. A string-literal-vs-enum mismatch here is exactly the kind of thing that fails at runtime with a typo, not at review time.

**(c) Granularity mismatch against EXPERIENCE.md's own navigation model — the sharper problem.** AD-10 treats "Player" as a single registered screen. But EXPERIENCE.md's Information Architecture table lists **two separate Player surfaces** — "Player — maze-selection screen" (reached from Home) and "Player — gameplay screen" (reached from the selection screen, or directly via `Test in Player`) — and its breadcrumb row gives a worked example: *"Breadcrumb reflects the actual navigation depth (e.g. `Home / Player / Classic Maze 4`)"* (EXPERIENCE.md line 58). That's **three** breadcrumb segments for what AD-10 models as **one** router-level screen. Nothing in the `mount(parent) -> Frame` interface gives a screen a channel to report a dynamic third-level label (`"Classic Maze 4"`) back up to whatever renders the breadcrumb (per AD-11, presumably a `common/` widget). Two implementers — one who assumes the router only ever needs to track its own 3-item screen stack and lets Player render its own internal sub-navigation invisibly, and one who assumes (correctly, per EXPERIENCE.md) that the breadcrumb needs to reach *into* whichever screen is mounted for a live label — will build incompatible breadcrumb wiring, and nothing in AD-10 or AD-11 tells either of them which is right.

A secondary, weaker point in the same neighborhood: the interface has no teardown/guard hook (`unmount()`, `can_leave()`). FR-17's confirmation-prompt list ("switching mazes, restarting, Level change, invalid input") is plausibly all *intra*-screen, so this may not be load-bearing — flagging it as a lower-confidence watch-item, not a hard finding, since Builder's Save-dialog flow (EXPERIENCE.md) at least raises the question of what happens to an unsaved edit if the user clicks the Home breadcrumb mid-session.

**Recommendation.** Tighten AD-10 with: the state parameter's type (or an explicit "no fixed type; each screen negotiates independently" if that's really the intent — but that's a materially different, weaker guarantee than a reader would assume from the current "e.g."); the registration-key mechanism; and — the one with real teeth — reconcile the router's screen granularity with EXPERIENCE.md's breadcrumb example, either by (i) stating Player owns two internally-navigable sub-states and defining how it feeds a label back to the shell's breadcrumb, or (ii) registering "Player — selection" and "Player — gameplay" as two separate router screens instead of one. This doesn't need full type signatures at spine altitude, but it needs more than an "e.g." given that this interface is the entire mechanism the amendment introduces to prevent "Home, Builder, and Player each inventing their own navigation mechanism."

---

## 2. AD-3's Maze kind tag can't represent "generated but not yet saved" — HIGH

**The collision.** EXPERIENCE.md's navigation model states the `Edit in Builder` exception is available *"from a maze context in the Player wherever a maze traces back to a Builder-editable source (classics and saved randoms — not procedurally-generated-and-unsaved mazes, which have no Builder file to open)."* This is a three-way distinction the UX explicitly cares about: classic, saved-random, and **freshly-generated-not-yet-saved-random** — three states, one of which must disable the `Edit in Builder` action.

AD-3 pins `Maze`'s kind tag as exactly `classic | sketch | saved-random` — three values, but not the same three. There is no tag value for "randomly generated this session, not yet written to disk" (FR-10/FR-11's own distinction: FR-10 generates, FR-11 is the separate save action, with the addendum explicitly noting the legacy bug where a saved random maze was never read back — i.e. "generated" and "saved-random" are already known, PRD-level, to be different moments in the same object's life, not synonyms).

**Concrete adversarial pair.** Whoever implements FR-10 (random generation in `domain/`/`application/`) and whoever implements the Player's `Edit in Builder` gating logic (FR-19/AD-10) both read AD-3 literally. Implementer A tags a freshly-generated `Maze` as `saved-random` immediately at generation time — defensible, since AD-3 offers no fourth value and `saved-random` is the closest fit for "this came from the random generator." Implementer B writes the `Edit in Builder` visibility check as `maze.kind in {classic, saved-random}` — also a direct, literal reading of AD-3 plus EXPERIENCE.md's "classics and saved randoms" phrase. The result: an unsaved, freshly-generated maze that the user never clicked "save" on now shows an enabled `Edit in Builder` button that, per EXPERIENCE.md, is explicitly supposed to be absent — because there's no file for Builder to open. Alternatively, if Implementer A instead withholds the `saved-random` tag until the actual save action (equally defensible under AD-3's wording, arguably more consistent with the name "saved-random"), the tag itself becomes state that changes out from under an in-memory `Maze` object mid-session — which AD-2's "domain state is immutable" rule doesn't obviously accommodate (does saving return a *new* `Maze` with the tag flipped, or mutate an existing reference?). Either resolution is plausible from the text; the two are incompatible, and the spine doesn't say which is correct.

**Recommendation.** This is squarely the kind of gap AD-3 exists to prevent (its own stated purpose: stopping "two independent implementers... inventing incompatible in-memory shapes for the same concept"). Either widen the kind tag to a fourth value (e.g. `classic | sketch | saved-random | generated`) with an explicit note that `generated → saved-random` is a one-way transition performed by FR-11's save action (returning a new `Maze` per AD-2, not mutating in place), or state explicitly that "generated-and-unsaved" mazes carry no kind tag / a `None` kind until saved, and that `Edit in Builder` gating is `kind in {classic, saved-random}` exactly. Either fix is cheap and removes a real behavioral inconsistency risk that a UX reviewer, not a code reviewer, would be the one to catch late.

---

## 3. Settings' relationship to the router is unstated, and the Capability Map's wording points the wrong way — MEDIUM

**The evidence trail.** Three sources bear on where Settings lives, and they don't all say the same thing:

- AD-10's rule text enumerates exactly three router-registered screens: *"Home, Builder, and Player are screens registered with that router."* Settings is conspicuously not a fourth name in that list.
- AD-11 already answers *where Settings' code lives*: *"generic, app-agnostic Tkinter building blocks (button/tooltip factories, **the settings-panel widget**, theme toggling, confirmation-prompt dialogs) live in `adapters/tkinter/common/`."* — i.e. Settings is a `common/` widget, not a fourth screen module.
- EXPERIENCE.md is explicit that Settings is *not* a router-swap destination: *"Opens as its own window, not an inline panel — so Builder/Player state stays visible/paused behind it rather than being replaced."* (line 62) — a `Toplevel`-style overlay, definitionally incompatible with "the router can swap [screens] uniformly" (a swap, per AD-10's own verb, replaces what's currently mounted).

Taken together, AD-11 + EXPERIENCE.md already settle this: Settings is a `common/`-hosted dialog invoked directly by whichever screen's Settings icon is clicked, not something that goes through `app/`'s screen router at all. But the Capability Map's new Home row says: *"Navigation shell / Home (IA — routes to Builder, Player, Settings...)"* — using "routes to" for Settings in the same breath as Builder and Player, which *are* router destinations. A reader who checks only AD-10 + the Capability Map (without independently cross-referencing AD-11's `common/` placement, three sections away) would reasonably conclude Settings is a fourth router screen and build it with a `mount(parent) -> Frame`, at which point Builder/Player's underlying state would need to be preserved-but-hidden behind a "swap" — directly contradicting EXPERIENCE.md's "state stays visible... behind it."

**Recommendation.** One sentence closes this: either amend AD-10 to state explicitly "Settings is not a router-registered screen — it is invoked directly, as a `common/`-hosted dialog, by whichever screen's Settings icon triggered it," or reword the Capability Map's Home row so "routes to" isn't used identically for Builder/Player (real router destinations) and Settings (a `common/` overlay). Low cost, removes a genuine two-reading-of-the-same-document risk.

---

## 4. AD-11 doesn't list Home as a `common/` consumer, but the Capability Map says AD-11 governs Home — MEDIUM

**The text.** AD-11's `Binds` line: *"`adapters/tkinter/builder`, `adapters/tkinter/player`, FR-6, FR-17, FR-18"* — no `home`. Its rule text: *"imported by both `builder/` and `player/` — not duplicated per app"* — again, no `home`. This is leftover phrasing from before this update (when `home/` didn't exist as an adapter at all — memlog confirms AD-11 was written in the original AD-1..AD-9 draft, pre-dating the Home screen).

Yet the Capability Map's new Home row (added by this very update) says: *"Navigation shell / Home ... | `adapters/tkinter/home`, `app/` | AD-10, **AD-11**"* — explicitly citing AD-11 as governing Home.

**Concrete adversarial pair.** Whoever builds the Home screen's top bar, Settings icon, and navigation cards reads AD-11's own `Binds`/rule text (not the Capability Map) and reasonably concludes Home is out of scope for the shared-toolkit obligation — since AD-11 names only `builder/` and `player/` as the two apps required to import from `common/` "not duplicated per app." Nothing stops that implementer from hand-rolling Home's buttons/tooltips/theme-toggle inline instead, which is exactly the duplication AD-11 exists to prevent — just with Home as the un-named third offender instead of Builder or Player. A second implementer who instead reads the Capability Map first assumes Home is already covered and never checks AD-11's actual `Binds` line. Both are literal, defensible readings of two different parts of the same finalized document that now disagree with each other.

**Recommendation.** Add `adapters/tkinter/home` to AD-11's `Binds` line and reword its rule text to "imported by `home/`, `builder/`, and `player/` — not duplicated per app," matching what the Capability Map already (correctly, in spirit) assumes. Mechanical, no new trade-off — this is the same class of leftover-renumbering slip the memlog's own triage pass (entry 26) already caught once for other ADs during the original Reviewer Gate; this one slipped through the UX-triggered update instead.

---

## 5. Home's `application/`/`domain/` dependency is unaddressed in the Capability Map — LOW-MEDIUM

**The gap.** The Capability Map's Home row lists `Lives in: adapters/tkinter/home, app/` — no `application/`, no `domain/` — unlike every other row (Construction, Game selection, Game modes), which all list `application/, domain/` alongside their adapter. Combined with the row's own parenthetical, *"not tied to a single FR,"* a reader could conclude Home is architecturally a pure-presentation router with zero business-logic needs, ever.

That's probably true *today* (Home routes and shows Settings/Personal-Records-later — no FR currently requires it to read maze or settings data). But AD-1's blanket rule ("`adapters/tkinter/` depends only on `application/`") does still structurally cover Home if that ever changes — so this isn't a violation risk today, just an absence of positive guidance. The moment Home grows a "resume where you left off" affordance, or when Personal Records (already named in EXPERIENCE.md, explicitly Deferred pending a PRD update per the spine's own Deferred section) needs local-best-times data on the Home surface, whoever builds that has no named `HomeService`-equivalent to extend (unlike Builder/Player, which at least have `BuilderService`/`PlayerService` implied by the Capability Map's other rows) and no stated rule preventing them from reaching `adapters/storage/` directly out of Home in a moment of "it's just a read, application/ has nothing for this yet" convenience — which AD-1 forbids, but only as a structural rule someone has to remember to apply consistently to a screen the rest of the spine treats as logic-free.

**Recommendation.** Accept as-is for this update (correctly, Personal Records is already flagged Deferred pending a PRD change, and no FR currently requires Home-side application logic). But when Personal Records is architected, this is the moment to also close this gap — name a `HomeService` (or fold Home's needs into existing services) in the Capability Map's `Lives in` column rather than leaving Home's future application-layer boundary implicit.

---

## 6. Removing the "Toplevel/window-swap, never a second `Tk()`, never a subprocess" language — no loss, checked

**The question.** The pre-amendment AD-10 (formerly AD-9, per memlog entry 26) explicitly named the mechanism: single-process, `Tk()` root reused via `Toplevel`/window-swap, never a second `Tk()` instance, never a subprocess. The amended text drops that enumeration and says only *"it owns the single `Tk()` root."*

**Why this is fine.** The old language existed to rule out a specific failure mode of the *two-composition-root* model: two independently-launchable apps, each of which might (if unconstrained) instantiate its own `Tk()` or spawn a subprocess when launching the other. That failure mode is structurally impossible under the new model — there's only ever one composition root, full stop, so there's no second app that could instantiate a second `Tk()` in the first place. The guarantee wasn't dropped; the scenario it was written to prevent was eliminated along with the two-root model. "Owns the single `Tk()` root" is actually the tighter statement for the new model, not a weaker one.

**What's still genuinely unchanged (not a regression from *this* update, but worth restating since the prompt asks specifically about enforceability):** neither the old nor the new phrasing was ever backed by AD-9's automated scan — that test only checks import statements, never actual `tk.Tk()` call sites. A screen module could still call `tk.Tk()` directly (e.g. by mistake, or a copy-pasted test fixture, instead of `tk.Toplevel()`/using the injected `parent`) and nothing in CI would catch it, before or after this amendment. Not a new hole introduced by the update — but since the update is exactly the moment "single `Tk()` root" became the guarantee's canonical phrasing, it's a reasonable point to note for whenever AD-9 is next touched: the scan could grep for `tk.Tk(` / `Tkinter.Tk(` outside `app/` at near-zero cost, turning a currently-conventional guarantee into a structural one, consistent with the whole spine's stated preference (AD-1's opening rationale) for structural over conventional boundaries.

**Disposition:** informational — no fix required by this update, optionally worth folding into a future AD-9 edit.

---

## 7. AD-9's lateral matrix omits `common/` as a party — LOW

**The gap.** AD-9's widened rule: *"any of `adapters/tkinter/home`, `adapters/tkinter/builder`, `adapters/tkinter/player` importing one another"* — three names, not four. `adapters/tkinter/common/` is (correctly, per AD-11) meant to be the base layer everyone imports *from*, never the other way around. But nothing in AD-9 flags a `common/` module that imports `home/`, `builder/`, or `player/` — an inversion that would silently reintroduce a lateral coupling path (e.g. `common/` importing something Builder-specific "just this once," which `home/`/`player/` then transitively inherit through their own `common/` import).

**Recommendation.** Low priority — accept for now, but worth folding into whichever future pass next touches AD-9's scan text: add "`adapters/tkinter/common/` importing any of `home/`, `builder/`, `player/`" as a fourth forbidden direction, alongside the `tk.Tk()` grep suggested in Finding 6. Both are cheap, mechanical extensions to an already-existing test, not new trade-offs.

---

## Overall recommendation

Before this feeds Epics/Stories:

1. **Tighten AD-10's screen interface (Finding 1)** — at minimum, reconcile the router's screen granularity with EXPERIENCE.md's `Home / Player / Classic Maze 4` breadcrumb example. This is the one gap in this update that mirrors the severity class of the original Reviewer Gate's Critical findings: it's the exact mechanism the amendment introduces to keep Home/Builder/Player from inventing their own navigation, and it's currently only sketched.
2. **Tighten AD-3's kind tag (Finding 2)** — add the fourth "generated, unsaved" state or explicitly define it as tagless, and state the `generated → saved-random` transition's shape (new `Maze`, per AD-2). This is directly required to build EXPERIENCE.md's `Edit in Builder` caveat consistently, and the PRD (FR-10/FR-11) already implies the distinction exists — AD-3 just hasn't caught up to it.
3. **Cheap consistency fixes (Findings 3 and 4)** — one sentence each: state Settings is a `common/`-hosted dialog, not a router screen; add `home` to AD-11's `Binds`/rule text so it stops disagreeing with the Capability Map's own citation of AD-11.

Findings 5–7 are legitimate but narrower — reasonable to leave for Epics/Stories (5) or bundle into a future AD-9 touch-up (6, 7) rather than block this update's close.
