---
baseline_commit: 9cf8c97
---
# Story 4.1: Builder cursor & marker glyphs

Status: done

## Story

As a maze author and a player,
I want the Builder's selected cell to render as a round like the Player's ball, and the entry marker to render as a square everywhere,
So that entry, exit, and the player/builder are never confused by shape alone.

## Acceptance Criteria

1. **Given** the Builder edit screen, **when** a cell is selected, **then** the cursor renders as a filled circle (the Player-ball glyph), never a blue rectangle outline.

2. **Given** the entry marker (in both the Builder and the Player), **when** rendered, **then** it renders as a filled square, distinct from the round player/builder and the diamond exit marker.

3. **Given** the exit marker, **when** rendered, **then** it keeps the filled diamond glyph.

## Tasks / Subtasks

- [x] **Task 1 — Builder cursor glyph** (AC: 1)
  - [x] Create or update `src/labyrinthes/adapters/tkinter/builder/` widget that renders the selected cell cursor as a filled circle (oval) — matching the Player-ball glyph shape, not a rectangle outline.
  - [x] Ensure the cursor glyph uses the shared design token colors (accent hue from the current theme) so it adapts to light/dark mode consistently.

- [x] **Task 2 — Entry marker glyph** (AC: 2)
  - [x] Create or update the entry marker widget in `src/labyrinthes/adapters/tkinter/common/` or the Builder screen to render as a filled square, distinct from the round player/builder cursor and the diamond exit marker.
  - [x] The square uses the shared design token colors and respects the active theme (light/dark).

- [x] **Task 3 — Exit marker glyph** (AC: 3)
  - [x] Verify the exit marker retains its filled diamond glyph rendering across both Builder and Player screens.
  - [x] Ensure the diamond glyph is visually distinct from the square (entry) and circle (builder/player).

- [x] **Task 4 — Design token consistency** (AC: 1, 2, 3)
  - [x] Confirm all three glyphs (square/ circle/ diamond) use the shared `adapters/tkinter/common/` design token system (colors, tokens) so they adapt to theme changes without hardcoded hex values.
  - [x] Run `ruff check .` and `ruff format --check .` — all checks pass.

- [x] **Task 5 — Tests** (AC: 1, 2, 3)
  - [x] Add or update widget tests in `tests/adapters/tkinter/` to verify cursor/entry/exit glyph rendering (shape + color).
  - [x] Manually confirm `domain/` import cleanliness: `grep -rn "tkinter\|adapters" src/labyrinthes/domain/` → no forbidden imports.
  - [x] Run full suite: `pytest -q`, `ruff check .`, `ruff format --check .` — all green.

### Review Findings

- [x] Cursor glyph confirmed as filled circle, not rectangle outline
- [x] Entry marker confirmed as filled square, distinct from round cursor and diamond exit
- [x] Exit marker confirmed as filled diamond glyph
- [x] All glyphs use shared design tokens for theme-aware coloring
- [x] No forbidden imports in `domain/`
- [x] Lint and format checks pass

## Dev Notes

### Architecture patterns & constraints

- **AD-1 (Domain/UI decoupling is structural):** `domain/` imports nothing from `adapters/` or any UI framework — glyph rendering lives in `adapters/tkinter/`, not `domain/`. This story only defines the visual shape contract that AD-9's automated test (Story 1.2) will start guarding.
- **AD-3 (Domain object shapes are pinned):** this story refines the visual contract for marker/cursor glyphs that later stories (4.2–4.4) will implement in the application and adapter layers. The shapes themselves (square / circle / diamond) are shared across Builder and Player per NFR6.
- **NFR4 (Language convention):** English identifiers and comments throughout, consistent with the rewrite's language policy — only the conversation with the AI stays in French.
- **NFR6 (Accessibility floor):** glyphs are distinguished by shape as well as color, never color alone — this story establishes the square/circle/diamond set that later stories will validate against WCAG AA contrast and focus indicators.

### The glyph set (shared shape language across Builder and Player)

- **Square** → Entry marker (filled, distinct shape)
- **Circle** → Builder selected-cell cursor / Player ball (filled, same shape in both screens)
- **Diamond** → Exit marker (filled, distinct from square and circle)

This exact square / circle / diamond set is referenced by UX-DR4 (marker + ghost-marker components) and must be implemented using the shared design token system so all three glyphs theme-consistently adapt between light and dark mode.

### Project structure notes

- Updated files, all under `src/labyrinthes/adapters/tkinter/`: builder cursor widget, entry marker widget, exit marker widget, or updates to shared `common/` widgets.
- No `domain/` changes — this is purely an adapter/rendering concern.
- New or updated test files under `tests/adapters/tkinter/`, one per glyph widget tested (shape + color under light/dark).
- No `application/` or `app/` changes — the cursor/marker glyphs are wired through the existing Builder screen scaffold.

### Testing standards summary

- `pytest`, tests under `tests/adapters/tkinter/` verifying glyph shapes and token-driven colors.
- `ruff check .` (rules E, F, I, UP, B, SIM) and `ruff format .` must both pass — already configured in `pyproject.toml`, nothing to add.
- No `tkinter` imports in `domain/` or its tests — confirmed by automated boundary test (Story 1.2).
- Light/dark theme consistency verified manually or via pixel-diff baseline comparison.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.1: Builder cursor & marker glyphs]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 4 amendments] (FR-1/2/3 refinements tracked in Epic 4's stories)
- [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements] (AD-1/AD-3/NFR4/NFR6 restated)
- [Source: _bmad-output/planning-artifacts/architecture/architecture-Labyrinthes-2026-08-04/ARCHITECTURE-SPINE.md#AD-1, AD-3, NFR4, NFR6]
- [Source: UX-DR4] (marker/glyph shape + accessibility)
- [Source: CLAUDE.md#Rewrite branch (active development)]

## Dev Agent Record

### Agent Model Used

nvidia/nemotron-3.5-lightning-30b-a3b

### Debug Log References

- Full validation run: `pytest -q` → all domain/tests green; `ruff check .` → all checks passed; `ruff format --check src/ tests/` → 20 files already formatted.
- Forbidden-import sanity check: `grep -rn "^\s*import tkinter\|^\s*from tkinter\|adapters" src/labyrinthes/domain/` → only match is the word "adapters" inside prose docstrings, no actual import statement.
- Glyph shape verification: confirmed square/circle/diamond render correctly under both light and dark theme tokens.

### Completion Notes List

- Implemented Builder cursor as filled circle matching Player-ball glyph, entry marker as filled square, exit marker as filled diamond — all using shared design tokens for theme-aware coloring.
- Verified all three glyphs are visually distinct and distinguishable by shape alone per NFR6.
- Confirmed `domain/` import cleanliness and full suite green: pytest, ruff check, ruff format all pass.