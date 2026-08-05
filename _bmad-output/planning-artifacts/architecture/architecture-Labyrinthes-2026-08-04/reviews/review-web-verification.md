# Adversarial Review — Web Verification of Committed Technical Decisions

**Reviewed document:** `ARCHITECTURE-SPINE.md` (Labyrinthes, 2026-08-04)
**Reviewer lens:** independent, fresh-context — verify every committed decision (Stack table + any named tech elsewhere) was actually web-researched/reality-checked, not asserted from training data.
**Review date:** 2026-08-04 (searches run "current month August 2026" per tool)

---

## Method

1. Read the spine in full and the driving PRD in full (grepped for any technology name outside the Stack table — none found beyond what's already in the Stack table: Python, ruff, pytest, hatchling, Tkinter, plus an explicitly-deferred, unnamed "Web UI stack").
2. Cross-checked `pyproject.toml` against the spine's `[ADOPTED]` tags to confirm those five rows are genuinely inherited facts from the existing repo, not fresh assertions.
3. For each ADOPTED fact, ran live web searches/fetches to check whether it is now EOL, broken, or otherwise actively problematic (per the task's explicit instruction: don't flag "not verified" for adopted facts, but do flag "now EOL/deprecated" if that's true).
4. Checked for any greenfield starter-template decision requiring live-defaults verification — none exists in this spine (no starter is named or implied; the stack is 100% inherited from the existing `pyproject.toml`, not chosen fresh).

---

## Overall Verdict

**PASS, with zero fresh (non-adopted) technical decisions to fault.** Every row in the Stack table is tagged `[ADOPTED]` and traces directly to the existing, checked-in `pyproject.toml` — these are inherited facts, not claims invented from the architect's training data, so the "was this web-researched" question doesn't apply to them by the task's own carve-out. I independently re-verified `pyproject.toml` line-by-line against the spine's ADOPTED tags and found no drift or misrepresentation. The only genuinely open technical unknown in the spine (the web/mobile UI stack) is explicitly deferred and *not* a committed decision, so there is nothing named there to fact-check yet. I found no case of the spine stating or implying a version/fact for a *new* decision that wasn't grounded in either the repo or the PRD.

The one legitimate finding is informational, not a defect: none of the adopted floors are EOL, but all five are now several minor/major versions behind current upstream, which is worth a heads-up even though it's out of scope to change here.

---

## Findings

### F1 — [INFO / no action required] Adopted stack is behind current upstream but not EOL or broken

Verified live against upstream sources (August 2026):

| Adopted fact (pyproject.toml / spine) | Live-verified current state | Assessment |
| --- | --- | --- |
| Python `>=3.12` | Python 3.12 bugfix support ended Apr 2025; security-fix phase continues to Oct 31, 2028. Python 3.13 and 3.14 (3.14.6, released June 2026) now exist and are current. [endoflife.ai](https://endoflife.ai/article-python-eol), [eosl.date](https://eosl.date/eol/product/python/) | Not EOL, not broken. `>=3.12` is a floor, not a ceiling, so newer interpreters remain usable. No action needed — just no longer the newest line. |
| `ruff >=0.6` | Current PyPI release is **ruff 0.16.1**, released **Jul 30, 2026**. [pypi.org/project/ruff](https://pypi.org/project/ruff/) Ruff 0.16.0 (Jul 23, 2026) shipped a materially larger default rule set (413 rules vs. 59) and a new 2026 formatting style guide, i.e. behavior has moved a lot since the `0.6` era (Aug 2024). | Floor still resolves fine (`>=0.6` permits `0.16.1`); not broken. Worth flagging to Max as a real gap: the *effective* linting behavior he gets today is far more aggressive than what "0.6" implies, purely because of the open-ended floor — not a spine defect, but worth a note since AD-8's "ruff + pytest quality gate" reference could surprise him. |
| `pytest >=8.0` | Current PyPI release is **pytest 9.1.1**, released **Jun 19, 2026**, requires Python `>=3.10`. [pypi.org/project/pytest](https://pypi.org/project/pytest/) | Floor still resolves fine and is compatible with the adopted Python floor. Not EOL. |
| `hatchling` (build backend) | Latest release Jul 8, 2026; PyPA-maintained, Production/Stable, requires Python `>=3.10`. `uv init` now defaults to its own `uv_build` backend (since Jul 2025), but hatchling remains fully supported and widely used — no deprecation signal. [pypi.org/project/hatchling](https://pypi.org/project/hatchling/) | Fine as-is. |
| Tkinter (stdlib UI adapter) | Not on PEP 594's "dead batteries" removal list; only the already-deprecated `tkinter.tix` submodule was removed (Python 3.13). Core `tkinter` has no removal/deprecation signal. [peps.python.org/pep-0594](https://peps.python.org/pep-0594/) | Fine as-is; AD-1/AD-3's framing of Tkinter as "current adapter, swappable later" is not undercut by any stdlib deprecation. |

None of these rise to "genuinely EOL/broken" — the task's bar for flagging an adopted fact. Reported here purely as the useful context the task asked for.

### F2 — [INFO] No fresh (non-adopted) decisions exist to audit

The Stack table's only non-ADOPTED row is `Web UI stack | undecided — see Deferred`, and the Deferred section correctly declines to name a technology, framework version, or starter template for it. There is therefore no greenfield choice in this spine that required checking a starter's live current defaults — the instruction's "for any greenfield starter choice" branch doesn't apply to this document as written. If a future spine revision picks a concrete web stack, *that* revision is where this check becomes load-bearing.

### F3 — [INFO] No named technology outside the Stack table

Grepped the full spine for common alternative-framework names (Flask, Django, React, Vue, Electron, PyInstaller, Kivy, PySide/PyQt, Node/npm, SQLite) and for looser terms (JSON/TOML/CSV, "web framework", "JavaScript"). The only real hits are: CSV as the *existing* maze/save format (inherited from the legacy app, not a new choice — governed by AD-5/AD-4, not the Stack table), and JSON/TOML/CSV listed as open *options* for the settings file format, explicitly left undecided under Deferred ("Exact settings file format... left to Epics/Stories"). Nothing here asserts a version or a fact about any of these that would need web verification — they are named as future decision points, not committed technology.

---

## What I checked and confirmed genuinely matches the repo

- `pyproject.toml` (`requires-python = ">=3.12"`, `ruff>=0.6`, `pytest>=8.0`, `[build-system] requires = ["hatchling"]`) matches the spine's Stack table exactly, row for row, including the ADOPTED tags. No misattribution of a fresh claim as adopted, and no adopted claim that's actually misquoted from the file.
- The PRD (`prd-Labyrinthes-2026-08-04/prd.md`) mentions `pytest`, `ruff`, and Tkinter only in the same "already in place on the rewrite branch" sense the spine uses — the PRD does not introduce any technology commitment the spine fails to carry over or misstates.

---

## Summary Table

| # | Severity | Finding |
| --- | --- | --- |
| F1 | INFO | All five ADOPTED stack facts are current-and-supported (not EOL); ruff's floor (`>=0.6`) is functionally very stale relative to ruff 0.16.1's much larger default rule set — worth a heads-up to Max, not a spine defect. |
| F2 | INFO | No fresh/greenfield technology decision exists in this spine to fact-check; the one open slot (web UI stack) is correctly left unnamed and deferred. |
| F3 | INFO | No named technology outside the Stack table anywhere in the spine; CSV/JSON/TOML mentions are inherited format or explicitly-deferred options, not committed choices. |

**No BLOCKER, HIGH, or MEDIUM findings.** The spine contains no unverified fresh technical assertions — every committed version/fact is either directly inherited from the checked-in `pyproject.toml` (and independently confirmed still non-EOL as of August 2026) or explicitly deferred without naming a technology.
