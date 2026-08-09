---
title: 'Story 1.10: Accessibility floor & keyboard shortcut consistency'
type: 'feature'
created: '2026-08-09'
status: 'done'
review_loop_iteration: 0
followup_review_recommended: false
context: ['_bmad-output/implementation-artifacts/epic-1-context.md']
warnings: [oversized]
baseline_revision: '41d14ed767a2553b27bad36996344cbb9435e097'
final_revision: 'ae80b7fcbc13a0b665f08961b393e7310d6d40ee'
---

<intent-contract>

## Intent

**Problem:** Every clickable `common/` widget (`IconButton`, `ToolButton`, `PillButton`, `Breadcrumb`'s clickable segment) is mouse-only -- no `takefocus`, no `<Return>`/`<space>` binding, no visible focus ring (already flagged in `deferred-work.md` from Stories 1.6/1.8/1.9) -- and no canonical keybinding table exists yet, so `kbd_tag.py` prints shortcut text with nothing behind it (its own docstring: "registers no key binding -- Story 1.10's job").

**Approach:** Give every focusable `common/` primitive real Tab-reachability, Enter/Space activation, and a `colors.accent` focus ring (AA-passing, ≥4.5:1, in both themes); add one canonical `Keybinding` table (`adapters/tkinter/common/keybindings.py`) that every printed `kbd-tag` and real binding derives from, plus an automated collision test; wire it into Home's two `PillButton`s (currently the only shortcut-bearing controls that exist).

## Boundaries & Constraints

**Always:** `IconButton`/`ToolButton`/`PillButton`/`Breadcrumb`'s clickable `Label` gain `takefocus=True`, `<Return>`/`<space>` bound to the same handler as `<Button-1>`, and explicit `<FocusIn>`/`<FocusOut>` handlers that toggle `highlightthickness` between `RESTING_RING_THICKNESS` (1, unchanged) and `FOCUS_RING_THICKNESS` (2, new -- both added to `tokens.py`) with `highlightbackground`/`highlightcolor` both set to `colors.accent` while focused. Explicit thickness toggling (not Tk's automatic highlightcolor/highlightbackground-only swap) is required because `ToolButton`'s existing *active* state already borders in `colors.accent` at thickness 1 -- an active-but-unfocused button must stay visually distinct from an active-and-focused one. `keybindings.py` exposes `Keybinding(action_id, label, key)` with `.display` (`key.upper()`, the printed `kbd-tag` text) and `.event` (`f"<KeyPress-{key}>"`, the Tk sequence) both derived from the one `key` field so they cannot drift apart; `KEYBINDINGS: tuple[Keybinding, ...]` currently holds exactly `("open_builder", "Open Builder", "b")` and `("open_player", "Open Player", "p")`; `keybinding(action_id)` looks one up (raises `KeyError` on a typo'd id); `bind_shortcut(widget, keybinding, callback)` calls `widget.bind_all(keybinding.event, ...)` and unregisters it on the widget's own `<Destroy>`. Home's two `PillButton`s source `shortcut=keybinding("open_builder").display` / `.../"open_player").display` and call `bind_shortcut(frame, ..., go_to_builder)` / `go_to_player` (the same callables passed as each `PillButton`'s `command=`). Fix `PillButton`'s primary-variant text color: it currently resolves `colors.window` against the widget's *own* theme (white, `#ffffff`, in light mode; near-black, `#12161d`, in dark mode), landing dark-mode primary text on the `accent_strong_dark` fill (`#1e40af`) at ~2.1:1 -- far under AA and contradicting `DESIGN.md`'s own rationale for that fill (white text measures ~8.7:1 there). Resolve it as `colors_for(Theme.LIGHT).window` unconditionally instead (same already-declared literal, reused rather than inventing a new hex).

**Block If:** None identified -- every decision here (focus-ring mechanics, which controls get a real shortcut, the primary-`PillButton` text bugfix) is mechanical or has one unambiguous correct answer backed by `DESIGN.md`'s own contrast math.

**Never:** Do not add a printed `kbd-tag` or real key binding to `IconButton` (Settings, theme-toggle) or `Breadcrumb`'s Home segment -- neither has a `kbd-tag` surface in the locked mockups (bare `title`-only `.icon-btn` markup; no `kbd-tag` slot on a breadcrumb segment), so Tab + Enter/Space is their complete keyboard path per AC2's own "or"; a hidden, unprinted accelerator key would contradict the "always visible, never hover/hidden-only" `kbd-tag` philosophy. Do not add a "Shortcuts" category to `SettingsWindow` -- no AC requires it; `settings_window.py`'s docstring hints at one, but building real category-switching UI is unrequested scope (flag it in `deferred-work.md` for whichever story next touches `SettingsWindow`'s content). Do not touch the dark-mode active-`ToolButton` text color (`colors.accent` on `colors.accent_bg` dark, ~4.25:1, marginally under AA) -- `DESIGN.md` explicitly locks this pairing as deliberate ("the dark-mode equivalent pairing was not flagged"), a locked planning artifact this story has no standing to override unilaterally; record it in `deferred-work.md` instead. Do not change `Router`, `ScreenMountFn`'s contract, or any screen's `mount()` signature.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| A focusable widget gains focus | `_on_focus_in()` invoked directly (real Tab traversal isn't reliably synthesizable under this suite's withdrawn-`tk_root` convention) | `highlightthickness == FOCUS_RING_THICKNESS`; `highlightbackground == highlightcolor == colors.accent` | No error expected |
| Focus leaves the widget | `_on_focus_out()` invoked | Ring reverts to `RESTING_RING_THICKNESS` and its resting color | No error expected |
| Enter or Space pressed on a focused control | `<Return>`/`<space>` bound handler invoked (or `_on_click()` directly) | Same effect as a mouse click | No error expected |
| An already-*active* `ToolButton` gains focus | `set_active(True)` then `_on_focus_in()` | Ring thickness becomes 2 (still visibly distinct from its active-but-unfocused 1px accent border) | No error expected |
| "B" shortcut fires while Home is mounted | `bind_shortcut`'s registered handler invoked | Navigates to Builder -- identical outcome to clicking "Open Builder" | No error expected |
| Two `Keybinding`s share a `key` | A modified `KEYBINDINGS` tuple | `test_keybindings.py`'s uniqueness test fails | Caught by an automated test, never at runtime |
| Dark-mode primary `PillButton` | `PillButton(primary=True, theme=Theme.DARK)` | label `foreground == colors_for(Theme.LIGHT).window` (`#ffffff`), ~8.7:1 against `accent_strong_dark` | No error expected |
| A screen's frame is destroyed | `frame.destroy()` after `bind_shortcut(frame, kb, ...)` | `<Destroy>` cleanup calls `unbind_all(kb.event)` -- no stale binding survives the screen | No error expected |

</intent-contract>

## Code Map

- `src/labyrinthes/adapters/tkinter/common/tokens.py` -- add `FOCUS_RING_THICKNESS`/`RESTING_RING_THICKNESS`
- `src/labyrinthes/adapters/tkinter/common/keybindings.py` -- new; `Keybinding`, `KEYBINDINGS`, `keybinding()`, `bind_shortcut()`
- `src/labyrinthes/adapters/tkinter/common/icon_btn.py` -- takefocus, Enter/Space, focus ring
- `src/labyrinthes/adapters/tkinter/common/tool_btn.py` -- takefocus, Enter/Space, focus ring integrated with active-state styling
- `src/labyrinthes/adapters/tkinter/common/pill_btn.py` -- takefocus, Enter/Space, focus ring; primary-text-color AA bugfix
- `src/labyrinthes/adapters/tkinter/common/breadcrumb.py` -- clickable segment gains takefocus, Enter/Space, focus ring (reusing existing hover recolor closures)
- `src/labyrinthes/adapters/tkinter/common/__init__.py` -- re-export the new names
- `src/labyrinthes/adapters/tkinter/home/screen.py` -- wire `shortcut=`/`bind_shortcut()` for Open Builder ("B") / Open Player ("P")
- `tests/adapters/tkinter/common/test_tokens.py` -- cover the two new constants
- `tests/adapters/tkinter/common/test_keybindings.py` -- new
- `tests/adapters/tkinter/common/test_icon_btn.py` -- focus-ring + Enter/Space cases
- `tests/adapters/tkinter/common/test_tool_btn.py` -- focus-ring + Enter/Space cases, incl. active+focused vs active+unfocused
- `tests/adapters/tkinter/common/test_pill_btn.py` -- focus-ring + Enter/Space cases; dark-mode primary text-contrast bugfix case
- `tests/adapters/tkinter/common/test_breadcrumb.py` -- focus-ring + Enter/Space cases
- `tests/adapters/tkinter/home/test_home_screen.py` -- kbd-tag matches canonical table; shortcut registered on mount
- `_bmad-output/implementation-artifacts/deferred-work.md` -- append the "Shortcuts" settings category and dark-mode `ToolButton` text-contrast entries

## Tasks & Acceptance

**Execution:**
- [x] `src/labyrinthes/adapters/tkinter/common/tokens.py` -- add `FOCUS_RING_THICKNESS = 2` / `RESTING_RING_THICKNESS = 1` -- the shared sizing every focusable primitive uses
- [x] `src/labyrinthes/adapters/tkinter/common/keybindings.py` -- add `Keybinding`/`KEYBINDINGS`/`keybinding()`/`bind_shortcut()` -- the canonical table (FR-22)
- [x] `src/labyrinthes/adapters/tkinter/common/icon_btn.py` -- takefocus + Enter/Space + focus ring -- closes the Story 1.8 deferred-work gap for `IconButton`
- [x] `src/labyrinthes/adapters/tkinter/common/tool_btn.py` -- takefocus + Enter/Space + focus ring -- same gap for `ToolButton`, kept distinct from its active-state border
- [x] `src/labyrinthes/adapters/tkinter/common/pill_btn.py` -- takefocus + Enter/Space + focus ring + primary-text AA bugfix -- closes the gap and a real ~2.1:1 contrast failure
- [x] `src/labyrinthes/adapters/tkinter/common/breadcrumb.py` -- takefocus + Enter/Space + focus ring on the clickable segment -- closes the Story 1.8 deferred-work gap
- [x] `src/labyrinthes/adapters/tkinter/common/__init__.py` -- re-export `Keybinding`/`KEYBINDINGS`/`keybinding`/`bind_shortcut`/`FOCUS_RING_THICKNESS`/`RESTING_RING_THICKNESS`
- [x] `src/labyrinthes/adapters/tkinter/home/screen.py` -- wire the two real shortcuts -- gives AC5's consistency test something real to check
- [x] `tests/adapters/tkinter/common/test_tokens.py` -- cover the two new constants
- [x] `tests/adapters/tkinter/common/test_keybindings.py` -- uniqueness, display/event derivation, lookup, `bind_shortcut` registration/callback/cleanup
- [x] `tests/adapters/tkinter/common/{test_icon_btn,test_tool_btn,test_pill_btn,test_breadcrumb}.py` -- focus-ring + keyboard-activation cases per widget
- [x] `tests/adapters/tkinter/home/test_home_screen.py` -- kbd-tag-matches-table + shortcut-registered-on-mount cases
- [x] `_bmad-output/implementation-artifacts/deferred-work.md` -- append the two out-of-scope findings (Shortcuts settings category, dark-mode `ToolButton` text contrast)

**Acceptance Criteria:**
- Given any focusable `common/` widget (`IconButton`, `ToolButton`, `PillButton`, a clickable `Breadcrumb` segment), when it gains keyboard focus, then it shows a visible `colors.accent` focus ring at `FOCUS_RING_THICKNESS`, meeting the same ≥4.5:1 AA contrast bar as body text against every surface it sits on in both themes
- Given any actionable control, when operated via Tab + Enter/Space (or, for Home's two `PillButton`s, its printed `kbd-tag` key), then it performs the same action as a mouse click
- Given the dark-mode primary `PillButton`, when its text/fill contrast is checked, then it measures ≥4.5:1 (fixing the ~2.1:1 regression), while the `accent-strong-dark` fill itself stays correctly applied
- Given `KEYBINDINGS`, when any two entries are compared, then no two share a `key` -- enforced by an automated test, never discovered at runtime
- Given Home's "Open Builder"/"Open Player" `kbd-tag`s, when compared to `keybinding("open_builder"/"open_player").display`, then they match exactly

## Spec Change Log

## Review Triage Log

### 2026-08-09 — Review pass
- intent_gap: 0
- bad_spec: 0
- patch: 5 (high 2, medium 3, low 0)
- defer: 3 (medium 1, low 2)
- reject: 1 (low 1)
- addressed_findings:
  - `[high]` `[patch]` Re-navigating a screen to *itself* (e.g. Story 1.9's theme toggle while on Home) mounted the new frame's shortcuts before the old frame's `<Destroy>`-triggered `unbind_all()` fired, silently and permanently wiping out the fresh registration since `Router.navigate()` mounts new-before-old — fixed `bind_shortcut()` with a per-interpreter, per-sequence registration-token registry so a `<Destroy>` cleanup only unbinds if it's still the current registration, not whichever one happened to fire last; also structurally closes the related "two different screens share a key" latent risk the spec's own Design Notes had flagged as "not reachable today."
  - `[high]` `[patch]` `Keybinding.event`/`bind_shortcut` only bound the lowercase keysym (`<KeyPress-b>`), so Shift+B or a CapsLock-typed "b" — exactly what the printed uppercase `kbd-tag` visually suggests — never fired, contradicting this story's own AC5 promise — fixed `bind_shortcut()` to bind both the lower- and upper-case keysym for a key.
  - `[medium]` `[patch]` `Breadcrumb`'s new focus handlers and pre-existing hover handlers each unconditionally overwrote the other's recolor with no shared state, so e.g. hovering off a Tab-focused segment reverted it to resting style despite focus still being present, and losing focus while still hovered dropped the hover color too — fixed by replacing the two independent closure factories with one `_segment_interactions()` factory tracking combined hovered/focused state, so text stays accent-colored while either is true and the ring reflects focus alone.
  - `[medium]` `[patch]` A light-mode primary `PillButton`'s focus ring reused `colors.accent` — the exact same hex as its own fill — landing at ~1.00:1 contrast, an AC1 violation for the screen's most important control (the primary CTA) — fixed by reusing the same always-white literal (`colors_for(Theme.LIGHT).window`) already used for the primary-text bugfix as the primary variant's focus-ring color instead (non-primary buttons keep the standard `colors.accent` ring, which has no such collision).
  - `[medium]` `[patch]` The primary-`PillButton` text-color AA bugfix (this story's own Boundaries) was applied to `_label` but not to the trailing `_kbd` (`KbdTag`), which stayed at its default `colors.ink_soft` foreground — ~1.06:1 (light) / ~2.94:1 (dark) against a primary fill, the same failure class one widget over — fixed by extending the same `colors_for(Theme.LIGHT).window` resolution to `_kbd`'s foreground when primary.
- Findings routed to `deferred-work.md` (real but pre-existing patterns, cross-cutting, or not reachable through any current call path — none blocking any stated AC): pressing "B"/"P" while a non-modal `SettingsWindow` is open silently closes it via `Router.navigate()`'s frame-destroy cascade — the identical underlying mechanism already deferred twice before (Story 1.8 breadcrumb-click, Story 1.9 theme-toggle), just reached via a third trigger; `bind_shortcut()` has no guard against hijacking keystrokes from a future focused text input, not reachable since no screen has one yet; `IconButton` snapshots `colors_for(theme)` once at construction instead of recomputing fresh like its three sibling widgets this story also touched, harmless today since screens fully re-mount on every theme toggle.
- Findings rejected as noise: `test_destroying_the_widget_unregisters_the_bind_all_shortcut`'s superfluous `tk_root.update()` call after `frame.destroy()` (the cleanup is synchronous within `.destroy()` itself, no event-loop pump needed) — cosmetic test-clarity nitpick with zero behavioral impact, not worth the churn.

### 2026-08-09 — Review pass (follow-up)
- intent_gap: 0
- bad_spec: 0
- patch: 2 (low 2)
- defer: 5 (low 5)
- reject: 4 (medium 1, low 3)
- addressed_findings:
  - `[low]` `[patch]` `home/screen.py` hardcoded `"Open Builder"`/`"Open Player"` as `PillButton` text literals instead of deriving them from `keybinding(...).label`, contradicting this story's own "single source of truth" premise for the canonical table — fixed by looking up `open_builder_kb`/`open_player_kb` once each and sourcing both the button text and the `shortcut=` display from the same `Keybinding`.
  - `[low]` `[patch]` `bind_shortcut()` re-derived its lowercase bind sequence as `f"<KeyPress-{kb.key.lower()}>"` instead of reusing `kb.event` (which `Keybinding.event`'s own docstring already calls "what gets bound"), so the property's claim wasn't actually backed by the binding code and the two could drift — fixed by binding `kb.event` directly for the lowercase sequence.
- Findings routed to `deferred-work.md` (real but not reachable through any current call path, or requiring a genuine design trade-off rather than a mechanical fix — none blocking any stated AC): toggling `highlightthickness` on focus causes a ~2px layout shift in any focusable `common/` widget without a fixed size (`PillButton`/`ToolButton`/`Breadcrumb`), since only `IconButton`'s fixed footprint absorbs it; `bind_shortcut()`'s registration registry keys on `id(widget.tk)`, a CPython identity shortcut that could theoretically be reused across short-lived `Tk()` instances; `bind_shortcut()`/`Keybinding` silently assume every `key` is a single ASCII letter, which would silently mis-bind a future function-key shortcut; `IconButton`/`ToolButton`/`PillButton` set `takefocus=True` unconditionally even when constructed with `command=None`; the new `<Return>`/`<space>` bindings fire on every `KeyPress`, so OS key-auto-repeat re-invokes the command for as long as the key is held, unlike a mouse click.
- Findings rejected as noise or duplicates: a `Ctrl+B`/Emacs-style-Entry-binding collision from `bind_shortcut()`'s bare `<KeyPress-b>` registration — the same underlying "no guard against hijacking a future text input's keystrokes" risk already deferred in the previous pass, just a more specific manifestation, with no current text-input screen to make it live; pressing "B"/"P" while `SettingsWindow` is open destroys it — an exact re-report of the entry already in `deferred-work.md` from this same story's previous pass; an active-and-focused `ToolButton`'s ring differing from active-unfocused by only 1px of thickness being "hard to perceive" — re-litigates a trade-off the Design Notes already document and a test (`test_active_and_focused_tool_button_renders_a_thicker_ring_than_active_unfocused`) already locks in; `_BY_ACTION_ID` "silently overwriting on a duplicate `action_id`" — already caught by the existing `test_every_action_id_in_the_table_is_unique` test, so the finding doesn't hold.

## Design Notes

- **Why explicit `<FocusIn>`/`<FocusOut>` handlers instead of relying on Tk's automatic highlightcolor/highlightbackground swap:** Tk widgets already auto-select `highlightcolor` (focused) vs `highlightbackground` (not) at a fixed `highlightthickness`, but this test suite's withdrawn `tk_root` never gains real X11 focus (`focus_set()` doesn't take, confirmed empirically), so nothing would be testable without a directly-invokable `_on_focus_in()`/`_on_focus_out()` pair -- the same reason every existing `common/` widget test invokes `_on_click()` directly instead of synthesizing `<Button-1>`.
- **Why thickness changes, not just color:** `ToolButton`'s *active* state already borders in `colors.accent` at the resting thickness. If focus only recolored (already `colors.accent` when active), an active-and-focused button would look identical to active-but-unfocused -- no visible focus indicator in that specific, real case. Toggling thickness (1 → 2) makes focus visible regardless of active state, with no new color to reason about.
- **Why `bind_shortcut` targets `bind_all` scoped by the widget's own `<Destroy>`, not the frame's own `bind()`:** a screen-wide shortcut must fire regardless of which child widget currently holds focus, which plain `widget.bind()` cannot do (it only fires when that exact widget has focus); `bind_all` is global to the Tk interpreter, hence the explicit `<Destroy>`-triggered `unbind_all` so a torn-down screen's shortcut can't outlive it. `Router.navigate()`'s new-before-old teardown order (Story 1.7) means this is only safe today because no two currently-registered shortcuts share a `key` across screens -- Builder/Player register none yet; flagged in `deferred-work.md` as a latent, not-reachable-today ordering risk for whichever future story first reuses a key across two screens.

## Verification

**Commands:**
- `pytest -q` -- expected: full suite passes, including the new `test_keybindings.py` and updated widget/screen tests
- `ruff check .` -- expected: no findings
- `ruff format --check .` -- expected: no findings

## Auto Run Result

Status: done

**Summary:** This invocation was a fresh, follow-up review pass on story 1.10 (previously `done` with `followup_review_recommended: true`), not a new implementation. Blind Hunter and Edge Case Hunter reviewed the story's full merged diff (`41d14ed..HEAD`, `src/`/`tests/` only) in parallel. Two small consistency gaps were patched; five real-but-unreachable edge cases were logged to `deferred-work.md`; four findings were rejected as duplicates of already-logged issues or as re-litigating already-locked design decisions.

**Files changed this pass:**
- `src/labyrinthes/adapters/tkinter/home/screen.py` -- `PillButton` text now sourced from `keybinding(...).label` instead of hardcoded `"Open Builder"`/`"Open Player"` literals
- `src/labyrinthes/adapters/tkinter/common/keybindings.py` -- `bind_shortcut()` now binds `kb.event` directly for the lowercase sequence instead of re-deriving it independently
- `_bmad-output/implementation-artifacts/deferred-work.md` -- five new entries (focus-ring layout jitter, `id(widget.tk)` identity fragility, single-ASCII-letter key assumption, unconditional `takefocus`, no debounce on held Enter/Space)
- `_bmad-output/implementation-artifacts/spec-1-10-accessibility-floor-keyboard-shortcut-consistency.md` -- new Review Triage Log entry, frontmatter updated (`status`, `followup_review_recommended`, `final_revision`)

**Review findings breakdown (this pass):** patch 2 (low 2) -- both applied; defer 5 (low 5) -- logged to `deferred-work.md`, none blocking any AC; reject 4 (medium 1, low 3) -- duplicates of already-logged findings or re-litigated locked decisions.

**Verification performed:** `pytest -q` -- 278 passed. `ruff check .` -- all checks passed (repo-wide). `ruff format --check src/ tests/` -- 95 files already formatted, no findings on any file this story touches (one unrelated legacy markdown doc outside this diff needs reformatting, pre-existing and untouched by this story).

**Follow-up review recommendation:** `false` -- only two small, low-severity, localized consistency fixes were made; not significant enough in volume or consequence to warrant another independent pass.

**Residual risks:** all five newly deferred findings are explicitly not reachable through any current call path (single-Tk-root app lifetime, no text-input screens yet, no commandless widget construction, no non-idempotent shortcut-bound handler yet, no non-letter keybinding yet) -- each is flagged in `deferred-work.md` for whichever future story first makes it live.

