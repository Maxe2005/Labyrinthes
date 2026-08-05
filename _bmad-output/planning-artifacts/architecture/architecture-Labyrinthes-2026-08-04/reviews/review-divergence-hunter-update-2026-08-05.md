# Adversarial Divergence-Hunter Review — Spine Update (Personal Records / FR-27, First-activation explainers / FR-28)

**Reviewed:** `ARCHITECTURE-SPINE.md`, updated 2026-08-05
**Scope of attack:** AD-3 (`MazeId`), AD-6 (amended header line), AD-8 (amended migration backfill), AD-12 (new — `RecordsRepository`/`RecordsService`), and their new Capability Map rows / Deferred edits, plus interaction with AD-1–AD-11.
**Method:** for each AD pairing, construct two units one level down that each satisfy their governing AD's text to the letter, and show they still build incompatibly.

## Verdict

The new material is well-pinned on *shape* (Record's fields, port method names, layer placement) but leaves the *lifecycle* of `MazeId` — who mints it, when, and for which legacy population — under-specified across three separate ADs (AD-3, AD-6, AD-8) that each only tell part of the story; two teams following their own AD to the letter can produce a store where `MazeId` is missing, duplicated, or inconsistently formatted, and `RecordsService`/`RecordsRepository` (AD-12) has no defensive contract for any of those states.

## Findings

### 1. CRITICAL — AD-8's backfill scope (classic only) contradicts AD-3/AD-6's eligibility scope (classic *or* saved-random)

**AD-3:** "`MazeId`... present only for `classic`/`saved-random` mazes (`None` for `sketch`/`generated`...)"
**AD-6:** "a new `MazeId` header line... present only when the maze is saved as `classic` or `saved-random`."
**AD-8:** "The same one-time script also mints and writes AD-6's `MazeId` header line for every **legacy classic maze** it converts... so migrated mazes are Personal-Records-eligible from day one."

AD-8's backfill sentence names only *classic* mazes. But per CLAUDE.md's documented data layout, legacy `saved-random` mazes exist on disk too, under `Labyrinthes_aléatoires_enregistrés/`, and both AD-3 and AD-6 put `saved-random` on equal footing with `classic` for `MazeId` eligibility.

**Two compliant-but-incompatible units:**
- **Unit A — migration script (AD-8 literalist):** reads AD-8's sentence exactly as written, iterates only the classic-maze folder, backfills `MazeId` there, and never touches the saved-random legacy folder. Fully compliant with AD-8's text.
- **Unit B — `RecordsService`/Player win-handler (AD-3/AD-12 literalist):** reads AD-3's "present only for classic/saved-random" as a *guarantee* that any post-migration `Maze` of kind `saved-random` carries a `MazeId`, and therefore calls `RecordsRepository.get_best(maze.id, ...)` unconditionally once `maze.kind` passes AD-12's `classic or saved-random` check, with no null guard.

Result: every legacy saved-random maze a player wins on has `maze.id is None`, and it silently reaches the repository as a `None` key — either crashing, or (worse, if the storage adapter doesn't validate) creating a record bucket keyed on `None` that collides across every unmigrated saved-random maze.

**Fix direction:** AD-8's backfill sentence should say "every legacy classic **and saved-random** maze it converts," matching AD-3/AD-6's scope — or, if saved-random legacy mazes are deliberately excluded (e.g., product decision that only classic mazes get records at launch), AD-3/AD-6/AD-12 need to say so explicitly instead of stating parallel `classic`/`saved-random` eligibility throughout.

### 2. CRITICAL — nothing pins "preserve existing MazeId on re-save"; a generic save path can re-mint on every edit

AD-3 says `MazeId` is "minted once, at the same save operation that assigns `classic` or `saved-random` (AD-6), and carried unchanged thereafter." This describes the *transition* moment (e.g., `generated` → `saved-random` on first save, or new classic maze creation) but the save *operation* itself is also invoked on every subsequent re-save — e.g. via AD-10's **Edit in Builder** transition, where a `classic`/`saved-random` `Maze` is reopened in Builder, edited, and saved again through the same `MazeRepository`/`BuilderService` write path.

**Two compliant-but-incompatible units:**
- **Unit A — implementer of the "mint MazeId on first save" flow** (e.g. Player's "save this generated maze" / Builder's "save new classic maze" story): correctly mints a fresh `MazeId` only when transitioning from `None`.
- **Unit B — implementer of the generic `MazeRepository.save(maze)` / Builder re-save flow** (Edit-in-Builder → edit → Save): reads AD-3's phrase "minted... at the same save operation that assigns classic or saved-random" as describing *every* save call that results in a `classic`/`saved-random` maze on disk (which a re-save trivially is, since the kind doesn't change) — and, absent an explicit "if `maze.id` is already set, keep it" rule, re-mints a new id each time `save()` runs, since nothing in AD-3/AD-6 puts that guard *on the save operation* rather than merely asserting it as an outcome.

Result: every time a user edits and re-saves a classic/saved-random maze via Edit-in-Builder, its `MazeId` silently changes, orphaning every Personal Record tied to the old id — precisely the failure mode AD-12's own "Prevents" clause calls out for *renames*, but reachable here via *re-save*, which AD-3/AD-6/AD-12 don't mention at all.

**Fix direction:** state explicitly, as a rule (not just descriptive prose) on either AD-3 or AD-6: "the save operation must preserve a non-null `MazeId` already present on the `Maze` value being saved; a new `MazeId` is minted only when the incoming value's `id` is `None`." This turns an implicit inference into an enforceable, testable contract (and is a natural companion assertion for AD-9's boundary test or a dedicated unit test).

### 3. HIGH — no null-safety contract between AD-12's kind-check and AD-3's "present only for classic/saved-random" (which is not the same as "always present for classic/saved-random")

AD-12: "`RecordsService.record_completion(maze, level, difficulty, time)`... itself checks `maze.kind` is `classic` or `saved-random` (AD-3) before touching the repository."

This check is necessary but, per findings #1 and #2, not sufficient — there are two legitimate compliant paths (unmigrated legacy saved-random mazes; a save operation that races with/precedes a completed migration; a partially-failed migration run) that produce a `classic`/`saved-random` `Maze` with `id: None`. AD-12's stated guard only inspects `kind`, never `id`.

**Two compliant-but-incompatible units:** a story implementing `RecordsService.record_completion` exactly as AD-12 describes it (kind-check only) vs. a story implementing `MazeRepository`/migration that (correctly, per AD-3's literal text, which never says "always non-null for these kinds," only "present only for" i.e. describing where it's *never* present) allows `id: None` to coexist with `kind: classic`. Neither violates its AD; together they crash or corrupt records.

**Fix direction:** AD-12's rule should read "...checks `maze.kind` is `classic`/`saved-random` **and `maze.id` is not `None`**..." — closing the gap explicitly rather than relying on an unstated invariant.

### 4. HIGH — `MazeId` generation scheme is deferred, but nothing requires the migration script and the live save path to share one minting implementation

The Deferred section explicitly leaves "`MazeId`'s exact generation scheme, e.g. UUID4 vs. another scheme" open. AD-8 requires the migration script and the repositories to share *path/naming constants* ("declared once... imported by both the migration script and the repositories"), but that sentence is scoped to "the new layout's path/naming scheme" — it does not extend to the `MazeId`-minting function itself.

**Two compliant-but-incompatible units:** a story implementing live `MazeId` minting inside `MazeRepository.save()` (e.g., `uuid4()`) and a separately-scheduled story implementing AD-8's migration script (e.g., a zero-padded incrementing counter, written independently since the spine never says "reuse the live minting function") — both satisfy their AD to the letter. Result: the on-disk store ends up with two different `MazeId` formats depending on whether a maze was freshly saved or migrated, which is harmless for `RecordsRepository`'s purely-opaque-key usage (AD-12 never assumes a format) but breaks the moment any future story assumes uniform id shape (validation, display truncation, sort-by-id, dedup logic) — exactly the kind of "two independent implementers inventing incompatible shapes" AD-3 exists to prevent, resurfacing one layer down at the *generation-scheme* level that AD-3 declines to pin.

**Fix direction:** even without picking the concrete scheme now, add one sentence requiring both call sites to invoke a single shared "mint a new `MazeId`" function (living beside AD-8's shared path/naming constants), so the scheme can stay deferred while its *singularity* is not.

### 5. MEDIUM — header-line position not pinned to an index, and AD-8's "shared constants" don't cover serialization order

AD-6: "positioned alongside the existing header lines before the grid rows" — no line index relative to entry/exit is given. AD-8 only requires the migration script and repositories to share *naming* constants, not a shared *writer*/serializer.

**Two compliant-but-incompatible units:** the live `MazeRepository.save()` writer places `MazeId` as, say, the third header line (after entry, exit); the migration script — built independently, per AD-8's letter, which never says "call `MazeRepository`'s own write method to rewrite the file" — inserts it as the *first* header line ahead of entry/exit, or appends it last. Both satisfy AD-6's "alongside... before the grid rows" wording. Any reader that assumes a fixed header order (rather than parsing header lines by tag/prefix) will misparse one or the other population.

**Fix direction:** either (a) require AD-8's migration script to call the same `MazeRepository` write path used for live saves (not just import the same path constants) so there is structurally one writer, or (b) make AD-6 explicit about the exact line order/position, or (c) require the header format to be tagged (self-describing lines) rather than positional, so insertion order can't matter.

### 6. MEDIUM — `Record`'s shape has no maze-display-name field, and `MazeRepository`'s (still-Deferred) interface isn't required to support id-based lookup

AD-12 pins `Record` to `maze_id, level, difficulty, time, set_at` — deliberately mechanical, no maze name. The Capability Map assigns Home's Personal-Records *display* to `RecordsService` + `adapters/tkinter/home`. But Home needs to turn a bare `maze_id` into something a user recognizes (maze name/thumbnail), which requires `MazeRepository` to support an id-keyed lookup — a method the Deferred section explicitly leaves unspecified ("`MazeRepository`/... exact interfaces... left to Epics/Stories").

**Two compliant-but-incompatible units:** the story that defines `MazeRepository`'s port (sequenced first per the Deferred note) models it around the legacy CSV-index/path-listing access pattern only (`list_classic()`, `load(path)`, etc., mirroring `#_Doc_index.csv`) with no id-based accessor, since neither AD-5 nor AD-12 requires one; the story that builds Home's Personal-Records display assumes `MazeRepository.get_by_id(maze_id)` exists (a reasonable but unstated assumption, since AD-12 keys everything on `MazeId`). Neither violates its governing AD; the display feature is unbuildable without a follow-up interface change.

**Fix direction:** add a line to AD-12 or the Deferred `MazeRepository`-interface note requiring the eventual `MazeRepository` port to support an id-based lookup, since AD-12 already made `MazeId` the load-bearing cross-reference key.

### 7. LOW — `list_all()` ordering ("most-recently-set-or-broken first") is not assigned to either side of the port boundary

FR-27's ordering requirement is cited as the reason `Record` carries `set_at`, but AD-12 doesn't say whether `RecordsRepository.list_all()` returns pre-sorted results or whether `RecordsService`/Home is responsible for sorting by `set_at`. A storage-adapter story could return arbitrary order (relying on the caller to sort) while a Home-display story could assume the port already guarantees order — both compliant, differing only in where a `sorted(..., key=lambda r: r.set_at, reverse=True)` call lives (or whether it exists at all).

**Fix direction:** state which side owns the ordering — cheapest fix is a one-clause addition to AD-12: "`list_all()` returns records pre-sorted by `set_at` descending."

### 8. LOW (flagged, out of primary scope) — FR-28's seen-tier flags are scoped only to `game`, but the explainer widget lives in `common/`

The Capability Map's FR-28 row scopes seen-tier flags to the `game` `SettingsRepository` scope only, while the explainer dialog itself is placed in `adapters/tkinter/common/` (per AD-11's widening, usable from any screen). If Builder also needs first-activation explainers, there is no declared scope for its seen-flags under AD-7's three-scope model as currently written in this row — a Builder-side explainer story and this capability row would diverge on which scope to persist into. Noted for completeness since it borders the reviewed material, though it wasn't the primary target of this pass.

## Summary Table

| # | Severity | Pairing | One-line divergence |
| --- | --- | --- | --- |
| 1 | Critical | AD-8 vs AD-3/AD-6/AD-12 | Migration backfill text says "classic" only; eligibility rules say classic-or-saved-random |
| 2 | Critical | AD-3/AD-6 vs any re-save path (AD-10 Edit-in-Builder) | No explicit "preserve existing id on save" guard — re-mint-on-resave orphans records |
| 3 | High | AD-12 vs AD-3 | `record_completion`'s kind-only check doesn't guard against `id: None` on classic/saved-random |
| 4 | High | AD-8 vs AD-3/AD-6 (via Deferred) | No shared minting function required between migration script and live save path |
| 5 | Medium | AD-6 vs AD-8 | Header-line position unpinned; migration and live save path could each write different order |
| 6 | Medium | AD-12 vs AD-5/Deferred | `Record` has no display name; `MazeRepository`'s undefined interface may lack id-lookup Home needs |
| 7 | Low | AD-12 vs FR-27 ordering | `list_all()` sort ownership (repository vs. service) unassigned |
| 8 | Low | AD-7 vs AD-11 (adjacent) | FR-28 seen-flags scoped to `game` only despite `common/`-hosted, multi-screen explainer |
