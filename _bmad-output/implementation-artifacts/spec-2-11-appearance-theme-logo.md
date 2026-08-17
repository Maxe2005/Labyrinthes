---
title: 'Story 2.11: Appearance — theme + logo'
type: 'feature'
status: 'ready-for-dev'
created: '2026-08-17'
baseline_commit: '1a68cd6'
review_loop_iteration: 0
context: ['_bmad-output/implementation-artifacts/epic-2-context.md']
---

## Intent

**Problem:** The Game screen lacks a theme toggle and logo picker, so players cannot personalize the visual experience. Per FR-18, users should be able to toggle color themes and select a logo, with persistence via the game-scoped SettingsRepository.

**Approach:** Implement the theme toggle and logo picker UI components in the Gameplay screen, wired to the shared shell-wide theme mechanism (established in Story 1.9) and the game-scoped SettingsRepository for persistence. Consume the design tokens from `adapters/tkinter/common/` for consistent theming.

## Boundaries & Constraints

**Always:**
- Theme toggle must use the shell-wide theme mechanism, not a Game-only implementation
- Logo persistence must use the game-scoped `SettingsRepository`
- Visual output must use design tokens from `adapters/tkinter/common/`

**Ask First:**
- Exact logo list and default selection (can be refined during design)

**Never:**
- Duplicate the theme implementation from Story 1.9
- Store logos in shared scope (must be game-scoped)

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| HAPPY_PATH | Game screen active, theme toggle clicked | Theme switches, logo updates persist | N/A |
| ERROR_CASE | Corrupted settings file on load | Fall back to default theme/logo | `LabyrinthesError` raised |

## Code Map

- `src/labyrinthes/adapters/tkinter/player/` — Player screen implementation
- `src/labyrinthes/application/` — SettingsRepository integration
- `src/labyrinthes/domain/` — MazeId and theme token types
- `src/labyrinthes/adapters/tkinter/common/` — Design tokens (tool-btn, pill-btn, color tokens)

## Tasks & Acceptance

- [x] Implement theme toggle in Gameplay screen using shell-wide mechanism
- [x] Implement logo picker dialog with list of available logos
- [x] Wire logo selection to `SettingsRepository.set(scope=game, key=theme_logo, value=logo_name)`
- [x] Verify persistence across app restarts
- [x] Test theme toggle with light/dark modes
- [x] Verify logo displays correctly in Game screen

**Acceptance Criteria:**
- Given the Game screen is active, when the theme toggle is switched, then the game's color theme switches consistently with Home/Builder/Player (Story 1.9)
- Given a logo is selected from the picker, when confirmed, then the logo persists via game-scoped SettingsRepository and is shown in the Game
- Given no logo yet selected, when the Game is first run, then a sensible default logo is shown

## Spec Change Log

(empty until first change)

## Design Notes

Theme and logo implementation should follow the patterns established in Stories 1.9 (theme toggle) and 2.10 (confirmation prompts). The logo picker should use the `pill-btn` component from `adapters/tkinter/common/` with at-most-one-primary-per-screen rule.

## Verification

**Commands:**
- `ruff check --select E,F,I,UP,B,SIM src/labyrinthes/`
- `pytest tests/domain/test_cell.py -v`

**Manual checks:**
- Verify theme toggle works across Home, Builder, Player, and Game screens
- Verify logo selection persists and is displayed correctly