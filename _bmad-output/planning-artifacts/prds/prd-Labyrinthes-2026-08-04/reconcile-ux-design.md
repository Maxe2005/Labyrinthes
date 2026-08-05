# Input Reconciliation — UX Spine/Design vs. PRD (FR-26/27/28, §6 Accessibility)

**Verdict:** Mostly reconciled — Personal Records and Home's core scope/gating/empty-state language track the UX docs closely, but 4 gaps survive, the most significant being an over-broad gating rule on FR-26 and a missing breadcrumb-navigation capability.

## Gaps

### 1. FR-26's gating consequence over-applies the "Builder-editable source" rule to `Test in Player`
- **Source:** `EXPERIENCE.md` Navigation model paragraph: "a contextual `Test in Player` action in the Builder opens the Player directly on the current maze, bypassing Home... the **mirror action**, `Edit in Builder`, exists from a maze context in the Player wherever a maze traces back to a Builder-editable source (classics and saved randoms — not procedurally-generated-and-unsaved mazes, which have no Builder file to open)."
  The gating clause is scoped, in the source, to `Edit in Builder` only (Player → Builder direction) — because only in that direction can the maze lack a backing file. `Test in Player` (Builder → Game) starts from a maze already open in an editing session, so it structurally can't hit that case.
- **PRD drift:** `prd.md` FR-26's Consequences lump both exceptions under one shared gate: "Two contextual exceptions bypass Home... `Test in Player`... and `Edit in Builder`... **gated to** mazes with a Builder-editable source (a classic or a saved random maze; not an unsaved procedurally-generated maze)."
- **Suggested fix:** Split the consequence bullet so the Builder-editable-source gate is stated only for `Edit in Builder`/FR-19, and `Test in Player`/FR-8 is described as ungated (always available from an active Builder session).

### 2. Breadcrumb/Home-return navigation mechanism is not captured anywhere in prd.md
- **Source:** `EXPERIENCE.md` Component Patterns: "Top bar / breadcrumb-Home-button | All screens | Breadcrumb reflects the actual navigation depth (e.g. 'Home / Player / Classic Maze 4'); clicking any earlier crumb jumps there directly. The Home segment is always present and always clickable, since Home is the router of record." Also echoed in `DESIGN.md`'s Do's/Don'ts ("Route Builder ↔ Player through Home... Add a persistent top-bar Builder/Player switcher" — Don't).
- **Gap:** FR-26 states Home is "the sole general router" and that "no persistent switcher... exists elsewhere," but never states *how* a user gets back to Home from a deep screen. The always-present, always-clickable breadcrumb trail is the actual mechanism that makes Home functionally "sole router" rather than just the entry point — it's a testable, product-level navigation capability, not a visual-token detail.
- **Suggested fix:** Add a consequence to FR-26 along the lines of: "Every screen carries a persistent, clickable breadcrumb trail back to Home (and to intermediate levels, where applicable); the Home segment is always present."

### 3. Settings' "reachable from any screen" scope is ambiguous / possibly narrowed in FR-26
- **Source:** `EXPERIENCE.md` Information Architecture table: `Settings | Top-bar icon, **from any screen**`. Settings is a global, always-available entry point (Home, Builder, and Game alike), independent of Home.
- **PRD drift risk:** FR-26 is the only place in `prd.md` that states Settings' entry point, phrased as "The user opens the app to a Home screen that routes to the Builder and to the Game, and **gives access to Settings**." Read in isolation, this implies Settings access is a Home capability, not a top-bar affordance present identically on every screen (Builder and Game included).
- **Suggested fix:** Reword FR-26 (or add a consequence) to state Settings is reachable via a top-bar icon present on every screen, not routed through Home specifically.

### 4. First-activation explainer's tone/register is not carried into FR-28
- **Source:** `EXPERIENCE.md` Voice and Tone table (plain, direct, "never baby-talk, never exclamation-driven") explicitly governs explanatory prose, and the First-activation explainer is called out by name as using `{typography.body-secondary}` — the same "explanatory prose" register — per both `EXPERIENCE.md` and `DESIGN.md` (Typography section: "explanatory prose: intro copy, tooltip bodies, **first-activation explainer text**, inline error/empty-state messages").
- **Gap:** FR-28's Consequences are purely mechanical (every tier gets it, auto-show is settings-toggleable, ⓘ always reopens it) with no testable requirement that the explanation stay in the product's plain, non-alarmist register — notably relevant here since the explainer's main job (per UJ-C) is describing a mode that hides the ball, which could easily read as a warning/scolding if not deliberately kept neutral.
- **Suggested fix:** Low priority / optional — could be left to the UX spec as-is, but if the PRD wants an explicit voice guardrail for FR-28 (as it already does implicitly for FR-27's empty-state wording), add a one-line consequence referencing the plain-language, non-alarmist tone.

---
*Gap count: 4. No gaps found regarding Personal Records' local-only scope, empty-state wording, "most relevant/recent first" ordering, or the Accessibility NFR — these all track their EXPERIENCE.md/DESIGN.md sources closely.*
