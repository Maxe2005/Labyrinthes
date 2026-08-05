---
name: Labyrinthes — Blueprint
description: Visual identity for the Labyrinthes maze-builder + maze-player desktop app pair — a drafting-table register (hairline grid, monospace HUD, single blue accent) in paired light/dark tokens.
status: final
updated: 2026-08-05
colors:
  # Light "Blueprint" / dark "Obsidian Draft", paired as base/base-dark
  # kebab-case tokens — see Colors below for the full rationale.
  bg: '#eef2f7'
  bg-dark: '#0a0d12'
  window: '#ffffff'
  window-dark: '#12161d'
  panel: '#f7f9fc'
  panel-dark: '#171c25'
  border: '#d7dee6'
  border-dark: '#2a323d'
  ink: '#1c2733'
  ink-dark: '#eef2f7'
  ink-soft: '#5b6b7c'
  ink-soft-dark: '#8b97a8'
  accent: '#2563eb'
  accent-dark: '#3b82f6'
  accent-bg: '#dbeafe'
  accent-bg-dark: '#16233d'
  wall: '#263445'
  wall-dark: '#3a4656'
  corridor: '#ffffff'
  corridor-dark: '#05070a'
  entry: '#16a34a'
  entry-dark: '#22c55e'
  exit: '#d97706'
  exit-dark: '#f59e0b'
  ball: '#2563eb'
  ball-dark: '#3b82f6'
  ghost: '#94a3b8'
  ghost-dark: '#4b5563'
  # AA-contrast fixes (see Accessibility Floor in EXPERIENCE.md). Both are
  # narrow-purpose tokens, not general-purpose accent replacements.
  accent-on-tint: '#1d4ed8'  # TEXT color only, when accent text sits on {accent-bg} (light mode)
  accent-strong-dark: '#1e40af'  # BACKGROUND FILL only, for primary-emphasis controls in dark mode
typography:
  # System stack for all UI text; monospace stack reserved for HUD/stat
  # values and shortcut tags, per the locked direction.
  heading:
    fontFamily: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif
    fontSize: 20px
    fontWeight: '700'
    letterSpacing: -0.01em
  heading-sm:
    fontFamily: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif
    fontSize: 15px
    fontWeight: '700'
    letterSpacing: -0.01em
  body:
    fontFamily: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif
    fontSize: 13px
    fontWeight: '600'
    lineHeight: '1.4'
  body-secondary:
    fontFamily: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.55'
  label:
    fontFamily: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif
    fontSize: 10px
    fontWeight: '700'
    letterSpacing: 0.06em
  hud-stat:
    fontFamily: ui-monospace, SFMono-Regular, 'Cascadia Mono', Consolas, monospace
    fontSize: 16px
    fontWeight: '700'
  kbd:
    fontFamily: ui-monospace, SFMono-Regular, Consolas, monospace
    fontSize: 10px
    fontWeight: '400'
rounded:
  xs: 3px
  sm: 5px
  md: 6px
  lg: 8px
  xl: 10px
  full: 50%
spacing:
  xs: 6px
  sm: 8px
  md: 10px
  lg: 12px
  xl: 14px
  '2xl': 16px
  '3xl': 18px
  '4xl': 20px
  '5xl': 24px
  section-gap: 40px
  page-margin: 64px
components:
  tool-btn:
    background: '{colors.window}'
    background-dark: '{colors.window-dark}'
    border: '{colors.border}'
    border-dark: '{colors.border-dark}'
    radius: '{rounded.md}'
    padding: '{spacing.sm} {spacing.md}'
    text: '{typography.body}'
    active-background: '{colors.accent-bg}'
    active-background-dark: '{colors.accent-bg-dark}'
    active-border: '{colors.accent}'
    active-border-dark: '{colors.accent-dark}'
    active-text: '{colors.accent-on-tint}'
    active-text-dark: '{colors.accent-dark}'
  hud-chip:
    background: '{colors.panel}'
    background-dark: '{colors.panel-dark}'
    border: '{colors.border}'
    border-dark: '{colors.border-dark}'
    radius: '{rounded.md}'
    padding: '{spacing.sm} {spacing.xl}'
    label: '{typography.label}'
    value: '{typography.hud-stat}'
    live-background: '{colors.accent-bg}'
    live-background-dark: '{colors.accent-bg-dark}'
  maze-frame:
    background: '{colors.window}'
    background-dark: '{colors.window-dark}'
    border: '{colors.border}'
    border-dark: '{colors.border-dark}'
    radius: '{rounded.xl}'
    padding: '{spacing.4xl}'
    inner-border-width: 3px
    inner-border-radius: '{rounded.xs}'
    inner-border-color: '{colors.wall}'
    inner-border-color-dark: '{colors.wall-dark}'
  wall-bar:
    color: '{colors.wall}'
    color-dark: '{colors.wall-dark}'
    thickness: 3px
    broken-state: absence
  marker:
    size: 22px
    radius: '{rounded.sm}'
    entry-color: '{colors.entry}'
    entry-color-dark: '{colors.entry-dark}'
    exit-color: '{colors.exit}'
    exit-color-dark: '{colors.exit-dark}'
  ghost-marker:
    size: 22px
    radius: '{rounded.sm}'
    border: '1.5px dashed {colors.ghost}'
    border-dark: '1.5px dashed {colors.ghost-dark}'
  ball:
    size: 20px
    radius: '{rounded.full}'
    color: '{colors.ball}'
    color-dark: '{colors.ball-dark}'
  top-bar:
    background: '{colors.window}'
    background-dark: '{colors.window-dark}'
    border-bottom: '{colors.border}'
    border-bottom-dark: '{colors.border-dark}'
    padding: '{spacing.md} {spacing.4xl}'
  brand-mark:
    size: 22px
    radius: '{rounded.sm}'
    background: '{colors.wall}'
    background-dark: '{colors.wall-dark}'
  breadcrumb-home-btn:
    text: '{typography.body}'
    color: '{colors.ink-soft}'
    color-dark: '{colors.ink-soft-dark}'
    hover-color: '{colors.accent}'
    hover-color-dark: '{colors.accent-dark}'
  icon-btn:
    size: 30px
    radius: '{rounded.md}'
    background: '{colors.panel}'
    background-dark: '{colors.panel-dark}'
    border: '{colors.border}'
    border-dark: '{colors.border-dark}'
  pill-btn:
    radius: '{rounded.md}'
    padding: '{spacing.xs} {spacing.lg}'
    text: '{typography.body}'
    background: '{colors.panel}'
    background-dark: '{colors.panel-dark}'
    primary-background: '{colors.accent}'
    primary-background-dark: '{colors.accent-strong-dark}'
    primary-text: '{colors.window}'
  kbd-tag:
    radius: '{rounded.xs}'
    text: '{typography.kbd}'
    padding: '0 {spacing.xs}'
  settings-window:
    background: '{colors.window}'
    background-dark: '{colors.window-dark}'
    radius: '{rounded.lg}'
    section-label: '{typography.label}'
  explainer-popup:
    background: '{colors.window}'
    background-dark: '{colors.window-dark}'
    radius: '{rounded.lg}'
    body-text: '{typography.body-secondary}'
  inline-message:
    text: '{typography.body-secondary}'
    error-color: '{colors.exit}'
    error-color-dark: '{colors.exit-dark}'
  win-banner:
    background: '{colors.accent-bg}'
    background-dark: '{colors.accent-bg-dark}'
    text-color: '{colors.accent}'
    text-color-dark: '{colors.accent-dark}'
    radius: '{rounded.lg}'
  record-group:
    radius: '{rounded.md}'
    background: '{colors.window}'
    background-dark: '{colors.window-dark}'
    border: '{colors.border}'
    border-dark: '{colors.border-dark}'
    row-padding: '{spacing.sm} {spacing.md}'
    row-hover-background: '{colors.panel}'
    row-hover-background-dark: '{colors.panel-dark}'
    name-text: '{typography.body}'
    combo-tag-text: '{typography.label}'
    combo-tag-radius: '{rounded.xs}'
    time-text: '{typography.hud-stat}'
    timestamp-color: '{colors.ink-soft}'
    timestamp-color-dark: '{colors.ink-soft-dark}'
    chevron-size: 9px
    chevron-color: '{colors.ink-soft}'
    chevron-color-dark: '{colors.ink-soft-dark}'
    combo-list-indent: '{spacing.5xl}'
  status-light:
    size: 10px
    radius: '{rounded.full}'
  fog-overlay:
    background: '{colors.bg}'
    background-dark: '{colors.bg-dark}'
    opacity: 0.85
    animation: none
  status-light-default:
    ready: '{colors.accent}'
    ready-dark: '{colors.accent-dark}'
    moving: '{colors.exit}'
    moving-dark: '{colors.exit-dark}'
---

## Brand & Style

Labyrinthes is a solo hobbyist maze tool that is nonetheless shown to friends and tested by real second-hand users — it needs to read as precise and trustworthy, not as a toy, without ever tipping into cold or corporate. The locked direction is **Blueprint**: a drafting-table register borrowed from technical instruments — coordinate labels, a monospace HUD, a hairline grid backdrop, small radii, and a single restrained blue accent. The maze itself is the invention worth showing off (the 0/1/2/3 cell-encoding scheme); the chrome around it should behave like a measuring instrument that gets out of the way, not compete with it.

This register earns its keep for three reasons specific to this product: (1) the app's core value proposition — build a maze cell-by-cell, solve it with exact coordinates and timers — is inherently technical, so a technical visual register is honest rather than affected; (2) a solo developer showing work to friends benefits from a "this was made carefully" signal more than a "this is fun and colorful" signal, since the fun is supposed to come from the puzzle, not the chrome; (3) density stays medium-high (every HUD stat that exists is shown, shortcuts stay printed on buttons) because the target user is a small, engaged audience who benefits from information-dense controls, not a mass consumer audience that needs hand-holding.

Full mockups for the locked light direction live in [`mockups/direction-blueprint.html`](mockups/direction-blueprint.html); the three rejected directions (`direction-warm-trail.html`, `direction-crisp-contrast.html`, `direction-soft-depth.html`) are kept in `.working/` for historical reference only — their tokens must not be used and they are not linked from this spine. **Spines win on conflict**: where this document and the promoted mockups disagree, this document is current (two component specs below explicitly supersede details still visible in the mockup HTML — the broken-wall treatment and the Builder/Player switcher, most notably).

## Colors

Both light (`Blueprint`) and dark (`Obsidian Draft`) palettes are locked — see [`mockups/direction-blueprint.html`](mockups/direction-blueprint.html)'s `<style>` header comment for the light hex values and [`mockups/color-themes-dark.html`](mockups/color-themes-dark.html)'s "Obsidian Draft" column for the dark ones (the file's other two dark candidates, Blueprint Nocturne and Graphite Studio, were rejected and must not be used). Tokens are paired as `{name}` / `{name}-dark` in one flat `colors` object rather than as separate DESIGN.md files per mode: every component in this product needs both variants specified side by side to stay visually equivalent across the theme toggle, and a single paired-token file makes that equivalence checkable at a glance instead of requiring a diff between two documents.

- **`{colors.bg}` / `{colors.bg-dark}`** — page backdrop behind the app window. Light is a cool blue-gray (`#eef2f7`); dark is near-black (`#0a0d12`), not navy — Obsidian Draft was chosen over the more literally "blueprint-paper" navy candidate (Blueprint Nocturne, rejected) specifically for its server-room, eyes-on-the-maze focus.
- **`{colors.window}` / `{colors.window-dark}`** — the app chrome surface itself (title bar, top bar). `#ffffff` light, `#12161d` dark.
- **`{colors.panel}` / `{colors.panel-dark}`** — side tool bars, HUD chips, settings rows. One step off `{colors.window}` toward `{colors.bg}`, giving structure without a hard border everywhere.
- **`{colors.border}` / `{colors.border-dark}`** — hairline dividers and default component borders. Never used for emphasis — emphasis is `{colors.accent}`'s job.
- **`{colors.ink}` / `{colors.ink-dark}`** and **`{colors.ink-soft}` / `{colors.ink-soft-dark}`** — primary and secondary text. Ink-soft is for labels, captions, and de-emphasized values; never for anything a user must read to act correctly (that's ink or accent).
- **`{colors.accent}` / `{colors.accent-dark}`** — the one interactive/active color in the system: active tool state, primary buttons, the ball, the live "Time" HUD chip, links. Dark mode brightens `#2563eb` → `#3b82f6` specifically for AA contrast against the near-black corridor/background — do not carry the light-mode hex into dark mode as-is.
- **`{colors.accent-bg}` / `{colors.accent-bg-dark}`** — the tint background used behind an active/selected state (active tool button, "Time" HUD chip, win banner). Never used as a large surface fill.
- **`{colors.wall}` / `{colors.wall-dark}`** and **`{colors.corridor}` / `{colors.corridor-dark}`** — the maze's structural colors. This pairing **deliberately inverts** between modes: in light mode the corridor is the brightest thing on screen (`#ffffff`) and the wall is dark (`#263445`); in dark mode the corridor is the *darkest* thing on screen (`#05070a`, darker than the page background) and the wall is the lighter, lit structural bar (`#3a4656`). This is not a straight color-swap — it's a deliberate "walls are the thing that's lit" logic that only makes sense per-mode, so implementers must not attempt to derive one from the other algorithmically.
- **`{colors.entry}` / `{colors.entry-dark}`** (green) and **`{colors.exit}` / `{colors.exit-dark}`** (amber/orange) — entry and exit markers. Always paired with a distinct icon/shape (see Components → marker) — color is reinforcement, never the sole differentiator, per the accessibility floor.
- **`{colors.ball}` / `{colors.ball-dark}`** — matches `{colors.accent}` in both modes; the ball reads as "the thing you control," visually tied to the same hue as every other interactive/live element.
- **`{colors.ghost}` / `{colors.ghost-dark}`** — disabled or not-yet-set state: the unset-exit ghost marker, disabled controls.
- **`{colors.accent-on-tint}`** — a darker, more saturated blue (`#1d4ed8`) used *only* as the text color when accent text sits directly on `{colors.accent-bg}` (the light-mode active-tool-button state). The base `{colors.accent}` on `{colors.accent-bg}` measures roughly 4.2:1 — just under the 4.5:1 AA text threshold — so this token exists purely to restore AA there; it is not a general accent replacement and has no dark-mode counterpart (the dark-mode equivalent pairing was not flagged).
- **`{colors.accent-strong-dark}`** — a darker fill (`#1e40af`) used *only* as the background of primary-emphasis controls (e.g. the primary `pill-btn`) in dark mode. White text on the standard `{colors.accent-dark}` (`#3b82f6`) measures roughly 3.3:1 — under AA — so primary-fill contexts in dark mode use this stronger fill instead, while `{colors.accent-dark}` remains the lighter general interactive/live accent everywhere else (the ball, the live Time chip).

## Typography

Two stacks, matching the two things this product needs to say clearly: prose/labels, and exact numbers.

- **`{typography.heading}`** and **`{typography.heading-sm}`** — the system UI font stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`) for screen titles and the brand wordmark. Bold, tight letter-spacing, no display face — Blueprint doesn't get an editorial flourish font; the system stack keeps it native-feeling across platforms.
- **`{typography.body}`** — the same system stack at 13px/600, used for all interactive control labels (buttons, tool names, tabs). Semibold rather than regular so labels hold their own against the hairline grid backdrop.
- **`{typography.body-secondary}`** — 14px/400, used for explanatory prose: intro copy, tooltip bodies, first-activation explainer text, inline error/empty-state messages.
- **`{typography.label}`** — 10px/700, uppercase (apply `text-transform: uppercase` at the component level — not a token field), 0.06em tracking. Used for group labels in the side bars, HUD chip captions, and settings section headers.
- **`{typography.hud-stat}`** — the monospace stack (`ui-monospace, SFMono-Regular, "Cascadia Mono", Consolas, monospace`) at 16px/700. Reserved for values that are literally numeric/coordinate data the user is meant to read precisely: Level, Difficulty, Time, Pos, Grid dimensions, wall counts. This is the single biggest signal of the "measuring instrument" register — never use the monospace stack for prose.
- **`{typography.kbd}`** — the monospace stack at 10px, used only inside `{components.kbd-tag}`.

## Layout & Spacing

The IA-level layout is fixed for both Builder and Player: the maze sits centered in its own `{components.maze-frame}`, flanked left and right by tool side bars, under a full-width top bar. `{spacing}` is a scale derived from the mockup's actual paddings/gaps, normalized rather than left as raw pixels:

| Token | Value | Typical use |
|---|---|---|
| `{spacing.xs}` | 6px | tight internal gaps (button icon-to-kbd gap) |
| `{spacing.sm}` | 8px | side-bar internal gaps, icon-button row gaps |
| `{spacing.md}` | 10px | tool-btn horizontal padding |
| `{spacing.lg}` | 12px | side-bar horizontal padding, pill-btn horizontal padding |
| `{spacing.xl}` | 14px | topbar-left gap, HUD-chip horizontal padding |
| `{spacing.2xl}` | 16px | side-bar vertical padding |
| `{spacing.3xl}` | 18px | HUD row gap |
| `{spacing.4xl}` | 20px | maze-frame padding, top-bar padding |
| `{spacing.5xl}` | 24px | maze-frame-to-legend gap, page horizontal padding |
| `{spacing.section-gap}` | 40px | gap between stacked screens/sections on a page |
| `{spacing.page-margin}` | 64px | outer page vertical padding |

The maze stage itself carries a faint hairline grid backdrop (repeating 1px lines at 22px intervals in `{colors.border}`) behind the maze-frame — a texture, not a spacing unit; implementers should not treat 22px as part of the spacing scale.

## Elevation & Depth

Shadows are minimal and used only to lift the window chrome and the maze-frame off the page — never as a hierarchy device between sibling components. Two shadow levels: a hairline `0 1px 2px` low-opacity shadow on most bordered surfaces (window, maze-frame, hud-chip), and a slightly larger `0 8px 24px` ambient shadow reserved for the outermost app window against the desktop backdrop. Depth otherwise comes from `{colors.border}` hairlines and tonal steps (`{colors.bg}` → `{colors.window}` → `{colors.panel}`), consistent with the drafting-table register: real elevation is rare in technical instruments, and Blueprint should feel closer to a panel of dials than a stack of cards.

## Shapes

Radii form a real scale, smallest to largest, matching the mockup's actual usage rather than one blanket radius:

| Token | Value | Used for |
|---|---|---|
| `{rounded.xs}` | 3px | the maze's own inner border (`{components.maze-frame.inner-border-radius}`), kbd tags |
| `{rounded.sm}` | 5px | entry/exit markers, ghost-marker |
| `{rounded.md}` | 6px | tool-btn, hud-chip, icon-btn, pill-btn, switch/tab controls |
| `{rounded.lg}` | 8px | the outer app window, settings window, explainer popup, win banner |
| `{rounded.xl}` | 10px | the maze-frame (the bordered container around the maze grid) |
| `{rounded.full}` | 50% | the ball only — the single fully-round shape in the system, which is exactly why it should always read unambiguously as "the ball" |

## Components

Visual specs only — behavioral rules live in `EXPERIENCE.md → Component Patterns`. Reference mockups: [`mockups/direction-blueprint.html`](mockups/direction-blueprint.html) (light, structural reference for every component below), [`mockups/color-themes-dark.html`](mockups/color-themes-dark.html) (dark token values only — its snippet layout is illustrative, not authoritative), and the key-screen mocks — [`mockups/key-home.html`](mockups/key-home.html), [`mockups/key-player-gameplay.html`](mockups/key-player-gameplay.html), [`mockups/key-builder-edit.html`](mockups/key-builder-edit.html), [`mockups/key-player-selection.html`](mockups/key-player-selection.html) — which apply every token below to the full IA surfaces (see `EXPERIENCE.md → Information Architecture` for which mock covers which surface). **Spines win on conflict** — two components below deliberately diverge from what's drawn in `direction-blueprint.html`; each says so explicitly.

- **`tool-btn`** (side bars, both apps) — `{rounded.md}` radius, `{colors.border}`/`{colors.border-dark}` 1px border, `{colors.window}`/`{colors.window-dark}` background, `{spacing.sm} {spacing.md}` padding, label in `{typography.body}` left-aligned with an optional `kbd-tag` right-aligned. **Active state** (currently-selected tool, e.g. "Break Wall"): background switches to `{colors.accent-bg}`/`{colors.accent-bg-dark}`, border to `{colors.accent}`/`{colors.accent-dark}`, text to `{colors.accent-on-tint}` in light mode (AA fix, see Colors) and `{colors.accent-dark}` in dark mode. Grouped under a `{typography.label}` group heading (e.g. "Tools", "Session", "Grid").
- **`hud-chip`** — read-only stat display: `{rounded.md}` radius, `{colors.panel}`/`{colors.panel-dark}` background, `{spacing.sm} {spacing.xl}` padding, a `{typography.label}` caption ("LEVEL", "TIME", "POS") over a `{typography.hud-stat}` value. **Live/accent variant** (the running Time chip): background `{colors.accent-bg}`/`{colors.accent-bg-dark}`, value text tinted accent — the one HUD chip allowed to visually signal "live," everything else stays neutral.
- **`maze-frame` + `wall-bar`** — the frame is a `{rounded.xl}`-radius bordered box (`{colors.border}`/`{colors.border-dark}`, `{spacing.4xl}` padding) housing the maze grid, whose own border is a separate, tighter `{rounded.xs}`-radius 3px line in `{colors.wall}`/`{colors.wall-dark}`. Wall bars inside the grid are 3px solid `{colors.wall}`/`{colors.wall-dark}` segments. **A broken wall is drawn as a gap — nothing rendered at that segment — never a dashed or patterned bar.** This corrects `direction-blueprint.html`'s `.wall-bar.broken` dashed-blue treatment, which reads ambiguously as a wall variant rather than an absence; the memlog explicitly revised this so the player unambiguously sees the wall is gone.
- **`marker`** (entry/exit) — 22×22px, `{rounded.sm}` radius, filled `{colors.entry}`/`{colors.entry-dark}` (entry, circle glyph) or `{colors.exit}`/`{colors.exit-dark}` (exit, flag/arrow glyph) with a soft 3px halo of the same hue at 15% opacity. The glyph shape is load-bearing, not decorative — see Accessibility Floor.
- **`ghost-marker`** — same 22×22px / `{rounded.sm}` footprint as `marker`, but unfilled: 1.5px dashed `{colors.ghost}`/`{colors.ghost-dark}` border, no fill, a `?` glyph. Marks "exit not yet set" during Builder editing.
- **`ball`** — 20×20px, `{rounded.full}` (the only fully-circular shape in the system), radial-gradient fill lightening toward `{colors.ball}`/`{colors.ball-dark}`, with a soft accent-hue halo and a small drop shadow so it visibly sits above the maze plane.
- **Top bar / brand mark / breadcrumb-Home-button** — full-width bar, `{colors.window}`/`{colors.window-dark}` background, bottom border in `{colors.border}`/`{colors.border-dark}`, `{spacing.md} {spacing.4xl}` padding. Left side: `brand-mark` (22×22px, `{rounded.sm}`, `{colors.wall}`/`{colors.wall-dark}` fill, white glyph) plus the "Labyrinthes" wordmark in `{typography.heading-sm}`. **`direction-blueprint.html` draws a Builder/Player `.switch` toggle here — that control is superseded.** Per the memlog's navigation revision, Home is the sole general router; the top bar instead carries a breadcrumb-style Home/back affordance (`{typography.body}`, `{colors.ink-soft}`/`{colors.ink-soft-dark}`, accent on hover) showing the current surface's place in the hierarchy (e.g. "Home / Player / Classic Maze 4"). Right side keeps `icon-btn` and `pill-btn` controls as drawn.
- **`icon-btn`** — 30×30px square, `{rounded.md}` radius, `{colors.panel}`/`{colors.panel-dark}` background, `{colors.border}`/`{colors.border-dark}` border, centered glyph in `{colors.ink-soft}`/`{colors.ink-soft-dark}`. Used for utility actions (Settings, theme toggle) that don't need a text label.
- **`pill-btn`** — `{rounded.md}` radius, `{spacing.xs} {spacing.lg}` padding, label in `{typography.body}` plus an optional trailing `kbd-tag`. Default variant: `{colors.panel}`/`{colors.panel-dark}` background, `{colors.border}`/`{colors.border-dark}` border. **Primary variant** (one per screen, e.g. "New Maze", "Save"): `{colors.accent}` fill in light mode, `{colors.accent-strong-dark}` fill in dark mode (AA fix, see Colors), `{colors.window}` text in both modes.
- **`kbd-tag` + hover tooltip** — the shortcut stays printed on the control itself: a small `{rounded.xs}`-radius pill in `{typography.kbd}`, low-opacity background matched to whatever surface it sits on. This is a final, corrected decision — the memlog briefly considered hover-only shortcut display and then reverted it. **Separately**, every control also carries a hover tooltip in `{typography.body-secondary}` that describes what the action *does* in plain language (e.g. "Removes the wall between the cursor and the next cell" for Break Wall) — the tooltip is never a restatement of the shortcut, the `kbd-tag` already shows that.
- **`settings-window`** — a dedicated window (not an inline panel), `{colors.window}`/`{colors.window-dark}` background, `{rounded.lg}` radius, left-hand or top category navigation (Appearance / Ball / Difficulty / Shortcuts / …) with each category label in `{typography.label}`, content area using standard form rows.
- **First-activation explainer popup** — a small `{rounded.lg}` popover/dialog, `{colors.window}`/`{colors.window-dark}` background, body copy in `{typography.body-secondary}`, anchored near the Level/Difficulty control it explains.
- **Inline error / empty-state message** — no modal chrome: text directly under or beside the concerned field/action, `{typography.body-secondary}`, `{colors.exit}`/`{colors.exit-dark}` for error states (reusing the exit/warning hue rather than introducing a new red), `{colors.ink-soft}`/`{colors.ink-soft-dark}` for neutral empty states.
- **Win banner** — `{rounded.lg}` radius, `{colors.accent-bg}`/`{colors.accent-bg-dark}` background, `{colors.accent}`/`{colors.accent-dark}` text, appears inline above/around the maze-frame on solve rather than as a modal takeover.
- **`record-group`** (Home, Personal Records zone) — one card per maze, `{rounded.md}` radius, `{colors.window}`/`{colors.window-dark}` background over `{colors.border}`/`{colors.border-dark}`. The header row (`{spacing.sm} {spacing.md}` padding) holds, left to right: a 9px chevron glyph in `{colors.ink-soft}`/`{colors.ink-soft-dark}` (rotates 90° open, absent entirely for a single-combo maze), the maze name in `{typography.body}`, a small `{rounded.xs}` combo-tag pill in `{typography.label}` reading `L{n}` or `L{n} · D{n}`, the time in `{typography.hud-stat}`, and a relative timestamp ("2 days ago") in `{colors.ink-soft}`/`{colors.ink-soft-dark}` at 11px. Hovering a multi-combo header (it's clickable) tints the row `{colors.panel}`/`{colors.panel-dark}`; a single-combo header has no hover treatment, since it isn't interactive. When expanded, an indented (`{spacing.5xl}`) combo list appears below the header, one row per (Level, Difficulty), each with its own combo-tag + time pair, no chevron, no timestamp — see [`mockups/key-home.html`](mockups/key-home.html) for the flat/collapsed/expanded states side by side.
- **HARD-mode fog overlay + status light** — while HARD mode is active, a translucent scrim in `{colors.bg}`/`{colors.bg-dark}` at `{components.fog-overlay.opacity}` (0.85, no animation — instant show/hide tied to ball-moving state) sits over the maze-frame during ball movement, standing in for "the ball is currently hidden." **Z-order is load-bearing:** the scrim sits above the corridor/ball plane but *below* wall-bars and markers, so walls, entry, and exit render crisply on top of it — only the ball's plane is obscured, never the structure. A small 10px `{rounded.full}` **status light** near the HUD shows ready-vs-moving state; its color is user-configurable in Settings (Appearance/Difficulty category). `[ASSUMPTION]` Default colors before the user customizes: ready = `{colors.accent}`/`{colors.accent-dark}`, moving = `{colors.exit}`/`{colors.exit-dark}` (amber, signals caution) — see `{components.status-light-default}`. Non-blocking; easy to revise.

## Do's and Don'ts

| Do | Don't |
|---|---|
| Print the shortcut on the button (`kbd-tag`) and describe the action in a separate hover tooltip | Rely on hover-only shortcut discovery, or use the tooltip to restate the shortcut |
| Draw a broken wall as a gap — nothing rendered | Use a dashed/patterned bar for a broken wall |
| Route Builder ↔ Player through Home, except the explicit Test-in-Player / Edit-in-Builder contextual actions | Add a persistent top-bar Builder/Player switcher |
| Use `{typography.hud-stat}` (monospace) only for numeric/coordinate data | Set prose or labels in the monospace stack |
| Pair every entry/exit/wall distinction with shape, not just `{colors.entry}`/`{colors.exit}`/`{colors.wall}` hue | Rely on color alone to distinguish maze elements |
| Keep the wall/corridor brightness relationship mode-specific (light: bright corridor, dark wall; dark: near-black corridor, lit wall) | Derive dark-mode wall/corridor by mechanically inverting the light-mode hex values |
| Show inline, contextual error/empty-state text next to the concerned control | Use modal dialogs for validation errors or empty states |
| Reserve `{colors.accent}`/`{colors.accent-dark}` for interactive/active/live meaning | Use the accent hue decoratively or for a second unrelated status meaning |
| Group a maze's records into one expandable `record-group` row, headlined by its most-recently-set-or-broken combo | Flatten a maze's multiple (Level, Difficulty) records into one row with no way to see the rest, or compute/show a cross-combo "fastest" time |
