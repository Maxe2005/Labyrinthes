# Web-Verification Review — Update Pass (2026-08-05)

**Scope:** material added to `ARCHITECTURE-SPINE.md` to extend the spine for Personal Records (FR-27) and First-activation explainers (FR-28): AD-3's `id: MazeId | None` addition, the AD-6 amendment (additive `MazeId` header line), the AD-8 amendment (migration backfill), the new AD-12 (`RecordsRepository`), the two new Capability Map rows, and the Deferred section edits. Stack table and AD-1/2/4/5/7/9/10/11 were out of scope per the prior full review pass and were not re-verified here unless the new material touched them (it doesn't).

**Lens:** does the new material name any technology/library/ID-generation scheme that should be checked against current reality, assert a Python/pytest/tkinter capability fact without having checked it, or otherwise read as asserted-from-training-data rather than reality-checked?

---

## Verdict

The new material is almost entirely internal architectural design (repository shape, value-object composition, CSV format extension, capability-map wiring) with no new libraries, frameworks, or version claims introduced — so there is very little surface for this lens to bite on. There is exactly one spot that names a concrete external technology as an example without checking it against current reality: the Deferred section's `MazeId`-generation-scheme note ("e.g. UUID4 vs. another scheme"). It's appropriately left as an open example rather than committed, but the example itself is now measurably stale relative to what Python's stdlib offers.

## Findings

### 1. MEDIUM — Deferred section's UUID4 example is stale next to Python's own current `uuid` module, and wasn't checked

**Location:** Deferred bullet: *"Exact settings, maze-repository, and records on-disk file formats (JSON/TOML/CSV per scope; `MazeId`'s exact generation scheme, e.g. UUID4 vs. another scheme)."* — this bullet is new/expanded material in this update (confirmed via `git diff`: it merges and extends what was previously a `MazeRepository`/`SettingsRepository`-only bullet, adding the `MazeId`/UUID4 clause).

**What I checked:** Web search confirms Python's stdlib `uuid` module gained native `uuid6()`, `uuid7()`, and `uuid8()` in **Python 3.14** (RFC 9562, which itself obsoleted RFC 4122 in 2024). `uuid7()` in particular is a time-ordered, monotonic-within-millisecond ID designed as a drop-in replacement for exactly this "database key" use case — better locality/sortability than `uuid4()`'s pure randomness, at no extra dependency cost if the runtime is 3.14+. (Sources: [docs.python.org/3/library/uuid.html](https://docs.python.org/3/library/uuid.html), [github.com/python/cpython/issues/102461](https://github.com/python/cpython/issues/102461).)

**Why it matters:** `pyproject.toml` pins `requires-python = ">=3.12"` with no upper bound, so `uuid7()` isn't guaranteed to be available depending on which interpreter is actually used to run the project — this is exactly the kind of "is the fact still true, and does it apply to *this* project's pinned floor" question the web-verification lens exists to force. `UUID4` is cited as *the* illustrative example, which reads as pulled from training-data familiarity rather than a check of what's current. This is low-stakes today because the bullet is explicitly Deferred/non-committal ("left to Epics/Stories," "below this spine's altitude") — nothing is actually adopted here, so it isn't a factual error in a stated decision. But if it survives verbatim into an Epic/Story as a starting assumption, whoever picks `MazeId`'s real scheme should verify at that time (a) which Python version is actually running, (b) whether `uuid7()` (native 3.14+) or a backport package (e.g. `uuid6`, `uuid-utils` on PyPI) fits better than `uuid4()` for a value that's stored as a CSV header field and used as a stable, humanly-inspectable record key.

**Suggested fix:** either drop the "e.g. UUID4" example entirely (the bullet already says the scheme is undecided and below this spine's altitude — no example is needed to make that point), or replace it with a neutral phrase like "e.g. a UUID variant or another scheme" that doesn't anchor the eventual implementer to a specific, unverified choice.

### 2. INFORMATIONAL — No other new-material claims need web verification

Swept AD-3's `MazeId`/`Position`-mirroring language, the AD-6 additive-header-line rule, AD-8's backfill rule, and AD-12's `RecordsRepository`/`RecordsService`/`Record` value-object design for named technologies, versions, or capability claims. None found:

- `Record`'s fields (`maze_id`, `level`, `difficulty`, `time: Duration`, `set_at`) are project-invented domain/application types (mirroring the already-established `Position`/`MazeId` pattern from AD-3, itself verified in the prior full pass) — not references to a specific stdlib or third-party type (e.g. `Duration` is not asserted to be `datetime.timedelta` or any named library class), so there's no version/existence claim to check.
- AD-12's "immutable value object" framing reuses AD-2's already-verified frozen-dataclass convention rather than introducing a new immutability mechanism.
- The two new Capability Map rows (Personal Records, First-activation explainers) only wire FR-27/FR-28 to existing directories and AD numbers — no new tool, library, or dependency is named.
- The First-activation explainer's "`Toplevel` dialog" mechanism is AD-11's pre-existing, already-verified pattern — not new tech in this update.

No fact about Python/pytest/tkinter capabilities is newly asserted by this update's material; the update is architecture-shape work built on primitives the spine already established and verified.

## Not Re-Checked (per scope)

Stack table (Python ≥3.12, ruff ≥0.6, pytest ≥8.0, hatchling, Tkinter) and AD-1/2/4/5/7/9/10/11 were confirmed in the prior full review pass and are untouched by this update — not re-verified here.
