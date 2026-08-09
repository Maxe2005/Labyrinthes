---
title: 'Story 1.6: Design token system & shared Tkinter widget primitives'
type: 'feature'
created: '2026-08-06'
status: 'done'
review_loop_iteration: 0
followup_review_recommended: false
context: ['_bmad-output/implementation-artifacts/epic-1-context.md']
warnings: [oversized]
baseline_revision: 'e94d8c1a28666e8e1cf5f59562ee54a2f9486872'
final_revision: '7fc7c613d3e8a0dc4e433a512f8e493e545a1611'
---

<intent-contract>

## Intent

**Problem:** No Tkinter code exists yet (`adapters/tkinter/` is unbuilt), so there is nowhere for Home/Builder/Player (Stories 1.7-1.10, Epics 2/3/5) to get the locked Blueprint colors, typography, spacing, radii, or the five core widget primitives (`tool-btn`, `hud-chip`, `icon-btn`, `pill-btn`, `kbd-tag`+tooltip) from without each screen inventing its own.

**Approach:** Add `adapters/tkinter/common/` with one `tokens.py` module mirroring `DESIGN.md`'s `colors`/`typography`/`spacing`/`rounded` blocks as plain data, plus one small widget module per primitive, each a thin `tkinter` subclass styled from `tokens.py` and construction-time `theme` parameter.

## Boundaries & Constraints

**Always:** `tokens.py` mirrors `DESIGN.md`'s four token blocks field-for-field, values copied verbatim (no invented hex/px). `Theme` is an enum (`LIGHT = "light"`, `DARK = "dark"`) so its `.value` round-trips as a plain string for Story 1.9's future settings persistence. `colors_for(theme: Theme) -> ColorTokens` resolves every paired color to that theme's locked value, including `accent_on_tint`/`accent_strong_dark` (single, theme-independent constants per `DESIGN.md` — see Design Notes for how consumers apply them). `SPACING`/`RADII` are module-level dicts keyed by `DESIGN.md`'s exact token strings (`SPACING["2xl"]`, `SPACING["section-gap"]`, `RADII["full"]`, …) since several keys aren't valid Python identifiers. `TYPOGRAPHY` is a dataclass of `FontSpec` entries (`heading`, `heading_sm`, `body`, `body_secondary`, `label`, `hud_stat`, `kbd`), each convertible to a real `tkinter.font.Font` via `FontSpec.to_tk_font()`. Every widget primitive (`ToolButton`+`ToolButtonGroup`, `HudChip`, `IconButton`, `PillButton`, `KbdTag`, `Tooltip`) takes `theme: Theme` at construction and styles itself once from `tokens.py` — no hardcoded hex/px inside a widget module. `ToolButtonGroup` guarantees exactly one member shows active styling at a time. `KbdTag`'s shortcut text is always rendered on the control (never hover-only); `Tooltip` is a separate, generic hover-attach helper reused by every primitive that needs one. `adapters/tkinter/common/` imports only stdlib/`tkinter` (no `domain`/`application` need exists yet for pure styling) — never `adapters/storage/`, never `home/`/`builder/`/`player/` (already enforced by `tests/test_architecture_boundaries.py`).

**Block If:** None identified — `DESIGN.md`/`EXPERIENCE.md` fully pin every color/typography/spacing/radius value and each widget's visual and behavioral rules; nothing here requires a human decision.

**Never:** Do not build `maze-frame`, `wall-bar`, `marker`, `ghost-marker`, `ball`, the top bar, breadcrumb, `settings-window`, explainer popup, inline-message, win banner, `record-group`, status-light, or fog-overlay — all out of this story's five-primitive scope (later stories/epics). Do not wire live theme switching, persistence, or a theme-toggle control (Story 1.9's job) or the canonical keybinding table (Story 1.10's job) — a `shortcut` string only feeds `KbdTag`'s printed label here, it registers no key binding. Do not attempt pixel-perfect rounded corners via `Canvas` — Tk's native `Button`/`Frame`/`Label` have no border-radius; primitives render square-cornered, and `RADII` values are recorded for later canvas-drawn components (`maze-frame`, `marker`, `ball`) to consume, not applied here. Do not implement the settings-window, confirmation dialogs, or breadcrumb widget that AD-11 also assigns to `common/` — those belong to Stories 1.8/1.9 and Story 2.10.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Paired color resolves per theme | `colors_for(Theme.LIGHT).accent` vs `colors_for(Theme.DARK).accent` | `"#2563eb"` (light) vs `"#3b82f6"` (dark) -- every other paired field likewise matches its `DESIGN.md` hex | No error |
| AA-fix tokens present regardless of theme | `colors_for(Theme.LIGHT).accent_on_tint`, `colors_for(Theme.DARK).accent_strong_dark` | `"#1d4ed8"` and `"#1e40af"` respectively -- same value from either theme's `ColorTokens` (see Design Notes) | No error |
| Wall/corridor never mechanically inverted | `colors_for(Theme.DARK).wall`/`.corridor` | `"#3a4656"`/`"#05070a"` (the locked dark values, not a computed inversion of the light hex) | No error |
| `ToolButtonGroup` mutual exclusivity | 3 `ToolButton`s in one group; `activate(b1)` then `activate(b2)` | Only `b2.active is True`; `b1.active`/`b3.active` are `False` | No error |
| `KbdTag` always visible | `KbdTag(parent, "W", theme=Theme.LIGHT)` constructed, no hover simulated | Widget's displayed text already reads `"W"` | No error |
| `Tooltip` hover lifecycle | `Tooltip(widget, "Removes the wall...")`; simulate the bound `<Enter>` then `<Leave>` handlers | A popup appears after `<Enter>`, is destroyed after `<Leave>` | No error |

</intent-contract>

## Code Map

- `src/labyrinthes/adapters/tkinter/__init__.py` -- new; package marker + docstring naming the future `common/`/`home/`/`builder/`/`player/` layout (AD-11), currently housing only `common/`
- `src/labyrinthes/adapters/tkinter/common/__init__.py` -- new; re-exports all public names via `__all__`, mirroring `adapters/storage/__init__.py`'s convention
- `src/labyrinthes/adapters/tkinter/common/tokens.py` -- new; `Theme`, `ColorTokens`, `colors_for(theme)`, `FontSpec`, `TypographyTokens`/`TYPOGRAPHY`, `SPACING`, `RADII`
- `src/labyrinthes/adapters/tkinter/common/tooltip.py` -- new; `Tooltip` -- hover-triggered `Toplevel` popup, binds `<Enter>`/`<Leave>` on the target widget
- `src/labyrinthes/adapters/tkinter/common/kbd_tag.py` -- new; `KbdTag(parent, shortcut, *, theme) -> tk.Label` -- always-visible shortcut pill
- `src/labyrinthes/adapters/tkinter/common/tool_btn.py` -- new; `ToolButton`, `ToolButtonGroup`
- `src/labyrinthes/adapters/tkinter/common/hud_chip.py` -- new; `HudChip(parent, label, value, *, theme, live=False)` with `set_value(value)`
- `src/labyrinthes/adapters/tkinter/common/icon_btn.py` -- new; `IconButton(parent, *, glyph, theme, tooltip=None, command=None)`
- `src/labyrinthes/adapters/tkinter/common/pill_btn.py` -- new; `PillButton(parent, text, *, theme, primary=False, shortcut=None, command=None)`
- `_bmad-output/planning-artifacts/ux-designs/ux-Labyrinthes-2026-08-04/DESIGN.md` -- existing; read-only, the source-of-truth token values and component visual specs
- `_bmad-output/planning-artifacts/ux-designs/ux-Labyrinthes-2026-08-04/EXPERIENCE.md` -- existing; read-only, the source-of-truth component behavioral rules
- `tests/test_architecture_boundaries.py` -- existing; read-only, `test_common_does_not_import_screens`/`test_tkinter_does_not_import_storage_adapters` already scan `adapters/tkinter/common/` and must keep passing unchanged
- `tests/adapters/tkinter/common/test_tokens.py` -- new; covers the I/O matrix's color/AA-fix/wall-corridor rows plus `SPACING`/`RADII`/`TYPOGRAPHY` shape
- `tests/adapters/tkinter/common/test_tooltip.py` -- new; covers the hover-lifecycle row
- `tests/adapters/tkinter/common/test_kbd_tag.py` -- new; covers the always-visible row
- `tests/adapters/tkinter/common/test_tool_btn.py` -- new; covers the mutual-exclusivity row
- `tests/adapters/tkinter/common/test_hud_chip.py` -- new; construction + `set_value` update
- `tests/adapters/tkinter/common/test_icon_btn.py` -- new; construction + fixed 30x30 footprint
- `tests/adapters/tkinter/common/test_pill_btn.py` -- new; default vs `primary` styling per theme

## Tasks & Acceptance

**Execution:**
- [x] `src/labyrinthes/adapters/tkinter/__init__.py` -- add package docstring, no imports -- establishes the package before any submodule needs it
- [x] `src/labyrinthes/adapters/tkinter/common/tokens.py` -- add `Theme`, `ColorTokens`, `colors_for()`, `FontSpec`, `TYPOGRAPHY`, `SPACING`, `RADII` copied field-for-field from `DESIGN.md` -- the single source every primitive styles from
- [x] `src/labyrinthes/adapters/tkinter/common/tooltip.py` -- add `Tooltip` -- the generic hover-popup every primitive with a tooltip reuses
- [x] `src/labyrinthes/adapters/tkinter/common/kbd_tag.py` -- add `KbdTag()` -- the always-visible shortcut pill `tool-btn`/`pill-btn` embed
- [x] `src/labyrinthes/adapters/tkinter/common/tool_btn.py` -- add `ToolButton` + `ToolButtonGroup` -- delivers the mutual-exclusivity AC
- [x] `src/labyrinthes/adapters/tkinter/common/hud_chip.py` -- add `HudChip` -- read-only stat display, live/accent variant
- [x] `src/labyrinthes/adapters/tkinter/common/icon_btn.py` -- add `IconButton` -- 30x30 utility-action button
- [x] `src/labyrinthes/adapters/tkinter/common/pill_btn.py` -- add `PillButton` -- default + primary variants
- [x] `src/labyrinthes/adapters/tkinter/common/__init__.py` -- re-export all public names via `__all__`
- [x] `tests/adapters/tkinter/common/test_tokens.py` -- cover the I/O matrix's color/AA-fix/wall-corridor rows, plus `SPACING`/`RADII` key presence and `FontSpec.to_tk_font()`
- [x] `tests/adapters/tkinter/common/test_tooltip.py` -- cover the hover-lifecycle row
- [x] `tests/adapters/tkinter/common/test_kbd_tag.py` -- cover the always-visible row
- [x] `tests/adapters/tkinter/common/test_tool_btn.py` -- cover the mutual-exclusivity row
- [x] `tests/adapters/tkinter/common/test_hud_chip.py` -- cover construction (label/value/live variant) and `set_value`
- [x] `tests/adapters/tkinter/common/test_icon_btn.py` -- cover construction and fixed footprint
- [x] `tests/adapters/tkinter/common/test_pill_btn.py` -- cover default vs `primary` styling per theme

**Acceptance Criteria:**
- Given the token module, when light/dark values are requested via `colors_for(Theme.LIGHT)`/`colors_for(Theme.DARK)`, then every paired token (including `accent_on_tint`, `accent_strong_dark`) resolves to its exact `DESIGN.md` value for that theme, and `wall`/`corridor` are the locked per-theme hexes, never a mechanical inversion of one another
- Given `tool-btn`, when one member of a `ToolButtonGroup` is activated, then only that member's `active` is `True` and every other member's `active` is `False`
- Given `kbd-tag`, when rendered on a control, then the shortcut is already visible with no hover required, and a separately-attached `Tooltip` only appears on hover and never restates the shortcut text
- Given `adapters/tkinter/common/`, when `tests/test_architecture_boundaries.py`'s `test_common_does_not_import_screens` and `test_tkinter_does_not_import_storage_adapters` run against this story's new files, then both still pass unchanged

## Spec Change Log

## Review Triage Log

### 2026-08-06 — Review pass
- intent_gap: 0
- bad_spec: 0
- patch: 2 (medium 1, low 1)
- defer: 6 (medium 1, low 5)
- reject: 2 (low 2)
- addressed_findings:
  - `[low]` `[patch]` `Tooltip.__init__`'s `theme` parameter had a `= Theme.LIGHT` default, inconsistent with every sibling primitive (`ToolButton`/`HudChip`/`IconButton`/`PillButton` all require `theme` with no default) and a latent mis-themed-popup risk for a future direct `Tooltip(...)` call that omits it -- dropped the default so `theme` is mandatory, matching its siblings; all existing call sites/tests already passed it explicitly, so nothing else changed
  - `[medium]` `[patch]` `ToolButton.set_active(True)` called directly (bypassing `ToolButtonGroup.activate()`) let two grouped buttons both show active styling simultaneously, contradicting the group's documented mutual-exclusivity guarantee -- `set_active()` now routes an activation through `self._group.activate(self)` when the button is grouped, with a new private `_set_active_direct()` used internally by `ToolButtonGroup.activate()` to avoid the two methods recursing into each other; added `test_calling_set_active_directly_still_respects_group_exclusivity` as a regression test

Findings routed to `deferred-work.md` (real but out of this story's declared minimal scope, none blocking any stated AC): `FontSpec.to_tk_font()`'s `int(self.weight)` crashes on a non-numeric `weight` string instead of degrading to `"normal"` (unreachable today -- all 7 `TYPOGRAPHY` entries use numeric-string weights); `SPACING`/`RADII` are plain mutable dicts with no `MappingProxyType` guard against a consumer accidentally mutating the shared token source; `ToolButtonGroup.activate()` called with a button never registered in that group silently deactivates every member with no membership check/error (only reachable via manual group/button wiring that bypasses `ToolButton`'s own constructor auto-`add`); a grouped `ToolButton` that is `.destroy()`ed while still registered (no `remove()`/unregister API exists) raises `TclError` out of the next `activate()` call, breaking every subsequent selection in that group -- not reachable today since no consuming screen exists yet to ever call `.destroy()` on one; `Tooltip` has no `<Destroy>` handling, so an anchor widget destroyed while its popup is shown (without a preceding `<Leave>`) can leave the popup `Toplevel` referenced with no owning widget; `HudChip(value=None)`/`set_value(None)` renders the literal text `"None"` instead of a placeholder, reachable only if a future caller passes an unset stat straight through.

Findings rejected as noise: `colors_for(theme)`'s `_LIGHT if theme is Theme.LIGHT else _DARK` (and the identical `is Theme.LIGHT else <dark>` pattern in `tool_btn.py`/`pill_btn.py`) has no runtime check that `theme` is actually a `Theme` member, so a raw string would silently fall through to dark colors -- mirrors Story 1.3/1.4/1.5's own repeatedly-rejected finding class ("no runtime type/union validation" -- the project has no static type-checker configured and relies on type hints as documentation, not runtime enforcement; already-established precedent, not a new judgment call here); `KbdTag` being a plain factory function rather than a class, unlike its sibling primitives, is a style-only observation that matches the spec's own documented `KbdTag(parent, shortcut, *, theme) -> tk.Label` signature literally -- not a defect.

## Design Notes

- **`accent_on_tint`/`accent_strong_dark` are single constants, not theme-paired:** `DESIGN.md` lists them outside the `{name}`/`{name}-dark` pairing convention -- each is one hex used in exactly one theme's *component* state (`tool-btn.active-text` in light mode; `pill-btn.primary-background-dark` in dark mode). `ColorTokens` therefore carries the same literal value under both `colors_for(Theme.LIGHT)` and `colors_for(Theme.DARK)`; it is the *widget* code (`ToolButton`, `PillButton`), not `tokens.py`, that decides which theme actually applies the field, exactly mirroring how `DESIGN.md`'s component blocks reference them.
- **No rounded corners on these five primitives:** Tk's native `Button`/`Frame`/`Label` cannot render `border-radius`; going through `Canvas` to fake it would balloon this story's scope for a mostly-invisible visual delta at these small control sizes. `RADII` is still fully populated as data so a later canvas-drawn component (`maze-frame`, `marker`, `ball`) has one source to read from.
- **Tk font size is negative-for-pixels:** `FontSpec.to_tk_font()` passes `size=-value` to `tkinter.font.Font`, since Tk treats a positive size as points (DPI-variable) and a negative size as pixels -- `DESIGN.md`'s sizes are already px, so this is the only way to render them as specified rather than approximate them.
- **No CSS-style font-stack fallback in Tk:** `FontSpec.family` keeps the full `DESIGN.md` fallback tuple as data, but `to_tk_font()` only ever passes the first entry -- Tk has no multi-family substitution, and relies on its own default-font fallback if that literal face isn't installed. `letter-spacing`/`line-height` are recorded in `DESIGN.md` but dropped from `FontSpec` entirely (not silently mis-applied) since `tkinter.font.Font` has no such concept.
- **`typography.label`'s uppercase transform lives in the widget, not the token:** `DESIGN.md` says so explicitly ("apply `text-transform: uppercase` at the component level"); `HudChip` upper-cases its caption text itself.

## Verification

**Commands:**
- `pytest -q` -- expected: full suite passes, including the new `tests/adapters/tkinter/common/` tests
- `ruff check .` -- expected: no findings
- `ruff format --check .` -- expected: no findings

## Auto Run Result

**Summary:** Added `adapters/tkinter/common/`, the shared Blueprint design-token module (`tokens.py`: `Theme`, `ColorTokens`/`colors_for()`, `FontSpec`/`TYPOGRAPHY`, `SPACING`, `RADII` -- mirroring `DESIGN.md`'s `colors`/`typography`/`spacing`/`rounded` blocks field-for-field) plus the five widget primitives the story scopes: `ToolButton`+`ToolButtonGroup` (mutual-exclusivity guarantee), `HudChip`, `IconButton`, `PillButton`, and `KbdTag`+`Tooltip`. This unblocks every later Tkinter screen (Stories 1.7-1.10, Epics 2/3/5) from styling itself off one shared source instead of hardcoding hex/px per widget.

**Files changed:**
- `src/labyrinthes/adapters/tkinter/__init__.py` -- new; package marker for the future `common/`/`home/`/`builder/`/`player/` layout
- `src/labyrinthes/adapters/tkinter/common/tokens.py` -- new; all four token categories as plain data
- `src/labyrinthes/adapters/tkinter/common/tooltip.py` -- new; `Tooltip`, the generic hover-popup helper (review-patched: `theme` is now a required keyword, no default)
- `src/labyrinthes/adapters/tkinter/common/kbd_tag.py` -- new; `KbdTag()` always-visible shortcut pill
- `src/labyrinthes/adapters/tkinter/common/tool_btn.py` -- new; `ToolButton`+`ToolButtonGroup` (review-patched: `set_active(True)` now routes through the group so direct calls can't break mutual exclusivity)
- `src/labyrinthes/adapters/tkinter/common/hud_chip.py` -- new; `HudChip`
- `src/labyrinthes/adapters/tkinter/common/icon_btn.py` -- new; `IconButton`
- `src/labyrinthes/adapters/tkinter/common/pill_btn.py` -- new; `PillButton`
- `src/labyrinthes/adapters/tkinter/common/__init__.py` -- new; re-exports all public names via `__all__`
- `tests/adapters/tkinter/common/conftest.py`, `test_tokens.py`, `test_tooltip.py`, `test_kbd_tag.py`, `test_tool_btn.py`, `test_hud_chip.py`, `test_icon_btn.py`, `test_pill_btn.py` -- new; full coverage of the I/O matrix plus a review-patched regression test for direct `set_active()` group-exclusivity
- `_bmad-output/implementation-artifacts/deferred-work.md` -- appended 6 review-deferred findings

**Review findings breakdown:** 2 patches applied (medium 1: `ToolButton.set_active(True)` called directly could break `ToolButtonGroup`'s mutual-exclusivity guarantee -- now routes through the group; low 1: `Tooltip`'s `theme` parameter had an inconsistent default vs. its sibling primitives -- now required). 6 findings deferred (medium 1: a destroyed-but-still-registered `ToolButton` raises `TclError` out of `activate()`; low 5: `FontSpec.to_tk_font()`'s unvalidated numeric-weight parsing, `SPACING`/`RADII`'s unguarded mutability, `ToolButtonGroup.activate()` with an unregistered button, `Tooltip`'s missing `<Destroy>` handling, `HudChip`'s `None` rendering as literal text) -- all real but unreachable today since no consuming screen exists yet (Stories 1.7+), logged to `deferred-work.md`. 2 findings rejected as noise: no runtime `Theme`-membership validation on `colors_for()` (mirrors Story 1.3/1.4/1.5's repeatedly-rejected "no static type-checker configured" precedent); `KbdTag` being a factory function rather than a class (matches the spec's own documented signature literally, not a defect). No `intent_gap` or `bad_spec` findings -- the spec needed no amendment.

**Verification performed:** `pytest -q` -- 174 passed (173 from initial implementation + 1 new regression test from the review-patch pass), including all 4 `tests/test_architecture_boundaries.py` tests confirming `adapters/tkinter/common/` imports nothing from `adapters/storage/` or the (not-yet-existing) `home/`/`builder/`/`player/` screen packages. `ruff check .` -- all checks passed. `ruff format --check src tests` -- all 65 project source/test files formatted clean (the one pre-existing unformatted file in the repo, `_bmad-output/implementation-artifacts/1-1-domain-model-foundation.md`, predates this story and was left untouched, consistent with Stories 1.4/1.5's identical precedent). All 4 acceptance criteria and all 15 execution tasks verified satisfied by direct inspection, cross-checking every `tokens.py` literal against `DESIGN.md`, and exercising the widget APIs directly (not just file existence). Two independent review passes (adversarial + edge-case) ran in parallel against the full diff; every finding was triaged, with 2 patched, 6 deferred, and 2 rejected as either out-of-scope-by-design or already-established precedent.

**Residual risks:** Low. The six deferred findings are all real but unreachable in today's tree since no Tkinter screen consumes these primitives yet -- every one of them (destroyed-widget handling, unregistered-group-member handling, `None`-value display, unvalidated `FontSpec` weight, mutable token dicts, tooltip `<Destroy>` handling) becomes relevant only once Stories 1.7+ actually mount `ToolButton`/`HudChip`/`Tooltip` instances into a live, tearing-down screen -- a natural point to revisit them, rather than speculatively hardening code with no current caller. The two patches applied are both localized and now covered by regression tests. No rounded corners, live theme switching, or keybinding registration were implemented, exactly as the spec's "Never" section scopes out -- those remain Story 1.9/1.10's work.
</content>
