# Epic 1 Context: Foundation & Navigation Shell

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Establish the structural foundation every later epic builds on: a single composition root and screen router; a functional, themable Home hub with breadcrumb navigation and top-bar Settings access; the immutable domain engine (Grid, Cell, Position, Maze, Level, Difficulty, Duration); the single shared `MazeRepository` and `SettingsRepository` implementations; the shared Tkinter `common/` widget toolkit and design token system; and an automated test that structurally enforces the domain/UI boundary. This epic replaces the legacy two-separate-apps, `big_boss`-cross-reference pattern with one shell that Home, Builder, and Player register into as screens, and it must land before any storage-consuming or screen-specific feature work (Epics 2-5) starts, since those all depend on the port interfaces, repositories, router, and toolkit defined here.

## Stories

- Story 1.1: Domain model foundation (Grid/Cell/Position/Level/Difficulty/Duration/Maze/MazeId, immutable)
- Story 1.2: Automated domain/UI boundary test
- Story 1.3: Persistence port interfaces — MazeRepository & SettingsRepository
- Story 1.4: Concrete MazeRepository — single shared CSV read/write implementation
- Story 1.5: Concrete SettingsRepository — scoped persistence
- Story 1.6: Design token system & shared Tkinter widget primitives
- Story 1.7: Single composition root & screen router
- Story 1.8: Home — breadcrumb navigation & Settings access
- Story 1.9: Light/dark theme toggle, wired end-to-end
- Story 1.10: Accessibility floor & keyboard shortcut consistency

## Requirements & Constraints

- The system reads/writes mazes in the existing CSV format (entry/exit lines, optional `MazeId` header, then the 0/1/2/3 grid); Builder and Game must share exactly one read/write implementation, with no format divergence and no re-encoding of existing data.
- Each application (Builder, Game) persists its own default settings between sessions; running both at once and changing a setting in one must never silently overwrite the other's settings on close.
- Every keyboard shortcut maps to exactly one action, and the printed label/tooltip always matches the real binding — no collisions, no stale labels.
- The app opens to a Home screen that is the sole general router between Builder and Player (aside from two later contextual exceptions owned by Epic 3); every screen carries a persistent, clickable breadcrumb back to Home; Settings is reachable from a top-bar icon on every screen, not routed through Home.
- The maze engine and gameplay rules must depend on no UI library — this is what keeps a future web/mobile interface possible, not just good practice.
- The 0/1/2/3 cell encoding and maze CSV format are a stable public contract; the only additive exception this milestone is the `MazeId` header line, and that is not itself precedent for further changes.
- Every ported feature needs automated test coverage (pytest) and must pass lint (ruff) — already configured in `pyproject.toml`, nothing to re-establish.
- Every action must be keyboard-reachable, every focusable control needs a visible AA-contrast focus indicator, text/background contrast must meet WCAG AA, and entry/exit/wall states must be distinguished by shape as well as color. Screen-reader support is out of scope (known Tkinter limitation).
- Git history should read as an incremental, feature-by-feature port with understandable commits/PRs.
- Code, identifiers, comments, UI strings, on-disk data, and docs are English-only from this branch onward.

## Technical Decisions

- Package layout is fixed: `src/labyrinthes/{domain/, application/, adapters/tkinter/{common/,home/,builder/,player/}, adapters/storage/, app/}`. Dependency direction is one-way: `app/` → `adapters/` → `application/` → `domain/`; `domain/` depends on nothing else in-project.
- `domain/` and `application/` import nothing from `adapters/` or any UI framework. `adapters/tkinter/` never imports `adapters/storage/` directly — storage access always goes through an `application/` service, so validation/business rules stay centralized.
- Domain value objects (`Grid`, `Cell`, `Maze`, `Position`, `Level`, `Difficulty`, `Duration`, `MazeId`) are immutable (frozen dataclasses or equivalent); engine operations are pure functions returning a new state. Each adapter owns its own mutable "current state" reference and re-renders after each call.
- Pinned shapes: `Grid` is `[row][col]`, 0-origin. `Cell` exposes wall booleans as computed properties over its `"0"`-`"3"` digit, never a separately stored decode. `Position` is one shared `(row, col)` type for entry/exit/ball/cursor alike. `Maze` = `Grid` + entry/exit `Position` + kind tag (`classic`/`sketch`/`saved-random`/`generated`) + `id: MazeId | None` (non-`None` only for `classic`/`saved-random`, minted once via a single shared minting function, carried forward unchanged on re-save). `Level` covers `1`-`4` plus a `MAX` sentinel ordered above `4`. `Duration` is one shared type (e.g. whole milliseconds) reused later by the Timer and by Personal Records.
- A pytest test scans `domain/` and `application/` for forbidden imports (`tkinter`, `adapters`), and flags `adapters/tkinter/` importing `adapters/storage/` directly, the three screen packages importing each other, and `adapters/tkinter/common/` importing any of them. It must pass before feature code exists, establishing the gate ahead of what it guards.
- Only persistence is a port; rendering is not. `MazeRepository` and `SettingsRepository` (plus `RecordsRepository`, added in Epic 6) are the sole ports in `application/`, each with exactly one implementation under `adapters/storage/`, used by every screen through the shell's single composition root.
- `MazeRepository` exposes saving/loading a `Maze` and looking one up by `MazeId` (not only by path). `SettingsRepository` exposes `get(scope, key)`/`set(scope, key, value)` for `builder`/`game`/`shared` scopes, written immediately — never a load-everything/dump-everything cycle. The `shared`-scope key names (e.g. FR-4's size bounds) are declared once in one module the shell imports. This port-definition story must land before any story that implements or consumes a concrete repository.
- Cell encoding stays `"0"`-`"3"` (bit 1 = top wall, bit 2 = left wall). Save format = entry/exit header lines, then (classic/saved-random only) a `MazeId` line, then grid rows — a fixed position, written through one shared routine reused later by the migration script.
- Design tokens (paired light/dark colors, two typography stacks, spacing scale, radii scale) and core widget primitives (`tool-btn`, `hud-chip`, `icon-btn`, `pill-btn`, `kbd-tag` + tooltip) live once in `adapters/tkinter/common/`, imported by `home/`, `builder/`, `player/` — never duplicated per screen, and `common/` imports nothing from those three.
- Exactly one `Tk()` root and one screen router live under `app/`. Home, Builder, and Player register with it via a shared `mount(parent, state: Maze | None) -> Frame` interface, keyed by a stable enum (not a bare string); none of the three imports another directly — all navigation goes through the router.
- Settings is not a router-tracked screen: it is a `common/`-hosted dialog (its own `Toplevel`) invoked directly from whichever screen's Settings affordance triggered it, with the underlying screen staying mounted behind it.
- The canonical keybinding table is one module; every later epic's actions register into this same table (not scattered per-widget bindings), and an automated test catches shortcut collisions.

## UX & Interaction Patterns

- Locked visual direction is "Blueprint": drafting-table register, monospace HUD for exact values (Level/Difficulty/Time/Pos/dimensions), restrained single blue accent, small radii, minimal shadows. Two dedicated AA-fix tokens exist: `accent-on-tint` (light-mode active-tool-button text) and `accent-strong-dark` (dark-mode primary-button fill) — apply them exactly where specified, not as general replacements.
- Wall/corridor colors deliberately invert between light and dark mode (walls are "the lit structure" in dark mode) — never derive one mode's hex from the other mechanically.
- Top bar (every screen): brand mark + wordmark on the left; a breadcrumb-style Home/back affordance (e.g. "Home / Player / Classic Maze 4") replaces any Builder/Player switcher — the Home segment is always present and clickable, each earlier crumb jumps there directly. `icon-btn` (Settings, theme toggle) and `pill-btn` (primary action, at most one per screen) sit on the right.
- `tool-btn` groups are mutually exclusive within a group (only one shows active styling); `kbd-tag` shortcuts are always printed on the control itself (never hover-only), paired with a separate hover tooltip describing the action's effect in plain language — the tooltip never restates the shortcut.
- `settings-window` is a dedicated window with left-hand/top category navigation (Appearance, Ball, Difficulty, Shortcuts, …), not an inline panel.
- Voice and tone is clear, direct, non-alarmist plain language — no baby-talk, no exclamation-driven copy (e.g. "Columns must be between 3 and 50." not "Error! Invalid input.").
- Accessibility floor: full keyboard operability for every action, a visible AA-contrast focus indicator on every focusable control, WCAG AA text/background contrast per the locked token pairs, and shape-plus-color (never color alone) for state distinctions — this floor is anchored here in Story 1.10 but every later screen-specific story must uphold it too.

## Cross-Story Dependencies

- Story 1.2 (boundary test) should exist before feature code accumulates, so it catches violations from the start rather than retrofitting a gate later.
- Story 1.3 (port interfaces) must land strictly before Story 1.4/1.5 (concrete repositories) and before any Epic 2/3/5 story that consumes a repository — those later stories would otherwise start from divergent assumptions about method signatures.
- Story 1.6 (tokens + widget primitives) is a prerequisite for Story 1.7-1.10 (router, Home, theme toggle, accessibility floor all render using `common/` widgets) and for every screen built in Epics 2, 3, and 5.
- Story 1.7 (composition root & router) must exist before Story 1.8 (breadcrumb navigation) and before Home can route to Builder/Player placeholders.
- Story 1.9's theme mechanism is the one Epic 2 (Story 2.11) and Epic 3 (Story 3.7) reuse rather than reimplementing per screen.
- Story 1.10's canonical keybinding table is the single table every later epic's screen-specific actions register into.
- This entire epic is a prerequisite for Epic 2, Epic 3, and Epic 6, all of which consume `MazeRepository`/`SettingsRepository`, the router, and the `common/` toolkit established here. Epic 5's migration script also reuses this epic's path/naming constants and `MazeRepository`'s `MazeId` writer.
