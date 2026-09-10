---
title: 'Story 4.9: Top-bar brand logo — follows the logo setting'
type: 'feature'
created: '2026-08-26'
status: 'done'
review_loop_iteration: 0
context: []
baseline_commit: 63025b12389cc3db81c3b688e15bc31d99e01f96
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The top bar on every screen shows only the text "Labyrinthes" as the brand mark. FR-32 requires the user's selected logo (from the Appearance settings) to appear before the app name on every screen's top bar.

**Approach:** Extend `TopBar` to accept an optional `PhotoImage` logo and render it left of the brand text. Each screen's `mount()` reads the `game`-scope `theme_logo` setting via `read_theme_logo()`, loads the corresponding image using the existing `logos._logo_path()` and PIL, and passes the `PhotoImage` to `TopBar`. When the theme changes, the existing flow re-navigates (re-mounts the screen), which reloads the logo against the new theme's background colors. When the user changes the logo in Settings, the new logo appears on the next navigation (no live re-navigate on Settings save — acceptable per the UX spec's non-alarmist voice).

## Boundaries & Constraints

**Always:** The logo renders at a fixed 24×24px (scaled from the 128×128 source) to match the heading text height. If the logo image fails to load (missing file, corrupt, PIL not available), fall back silently to text-only — never crash. The logo setting lives in `game` scope (`THEME_LOGO` key) and defaults to `"default"`; all three screens (Home, Builder, Player) read the same setting so the brand mark is consistent everywhere. `TopBar` stays in `common/` and does not import `application/logos` or `PIL` — screens load the image and pass the ready `PhotoImage`.

**Ask First:** None — the logo size, fallback behavior, and scope are fixed by FR-32 and the existing logo picker implementation (Story 2.11).

**Never:** Never add a new settings key or scope. Never make `TopBar` depend on `application/` or `PIL`. Never duplicate the logo-loading logic — reuse `logos._logo_path()` and the existing 13 logo assets. Never change the `SettingsWindow` logo picker (already complete).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| App launches, logo setting is default | `theme_logo` = `"default"` (or unset) | Top bar shows logo-02.jpg (24×24) + "Labyrinthes" | N/A |
| User changes logo in Settings, then navigates | `theme_logo` = `"water"` | Next screen shows water logo + "Labyrinthes" | N/A |
| Logo file missing on disk | `theme_logo` = `"logo-99"` (invalid) | Text-only "Labyrinthes", no crash | Silent fallback |
| PIL not installed | Any logo setting | Text-only "Labyrinthes", no crash | Silent fallback |
| Theme toggle while on a screen | Theme changes LIGHT→DARK | Screen re-navigates, logo re-renders on new theme background | N/A |

</frozen-after-approval>

## Code Map

- `src/labyrinthes/adapters/tkinter/common/top_bar.py` -- `TopBar.__init__` (lines 31-83): add optional `logo: tk.PhotoImage | None` parameter; if provided, pack a `tk.Label` with the image before the brand text label.
- `src/labyrinthes/adapters/tkinter/home/screen.py` -- `mount()` (lines 59-143): read `theme_logo` via `read_theme_logo(settings_repository)`, load image via `_load_logo_image(theme, logo_key)`, pass to `TopBar`.
- `src/labyrinthes/adapters/tkinter/builder/screen.py` -- `mount()` (lines 49-130): same logo loading and pass-through to `TopBar`.
- `src/labyrinthes/adapters/tkinter/player/screen.py` -- `mount()` (lines 65-179): same logo loading and pass-through to `TopBar`.
- `src/labyrinthes/application/theme_logo_settings.py` -- `read_theme_logo()` (line 30): already exists, reads `game` scope `THEME_LOGO` with default `"default"`.
- `src/labyrinthes/application/logos.py` -- `_logo_path()` (line 32): already exists, resolves logo key to asset path under `player/assets/logos/`.
- `src/labyrinthes/adapters/tkinter/common/tokens.py` -- `SPACING`, `TYPOGRAPHY`, `colors_for()`: used for logo label styling consistency.

## Tasks & Acceptance

**Execution:**
- [x] `src/labyrinthes/adapters/tkinter/common/top_bar.py` -- add optional `logo` param, render logo label before brand text if provided -- AC 1, 2
- [x] `src/labyrinthes/adapters/tkinter/home/screen.py` -- load logo image in `mount()`, pass to `TopBar` -- AC 1, 2
- [x] `src/labyrinthes/adapters/tkinter/builder/screen.py` -- load logo image in `mount()`, pass to `TopBar` -- AC 1, 2
- [x] `src/labyrinthes/adapters/tkinter/player/screen.py` -- load logo image in `mount()`, pass to `TopBar` -- AC 1, 2
- [x] Tests -- verify logo renders on all three screens, fallback on missing file/PIL, logo updates after Settings change + navigation -- AC 1-4
- [x] Run `ruff check src/`, `ruff format --check src/`, `pytest` (relevant tests) -- all green

**Acceptance Criteria:**
- Given the app starts, when Home mounts, then the top bar shows the configured logo (24×24) immediately left of "Labyrinthes".
- Given a screen with a maze canvas (Builder, Player), when it mounts, then its top bar shows the same logo as Home.
- Given the logo file is missing or PIL is unavailable, when a screen mounts, then the top bar shows only "Labyrinthes" with no error.
- Given the user changes the logo in Settings, when they navigate to another screen, then the new logo appears in the top bar.

## Design Notes

Logo loading helper (duplicated in three screens, ~10 lines each):
```python
def _load_logo_image(theme: Theme, logo_key: str) -> tk.PhotoImage | None:
    try:
        from PIL import Image, ImageTk
        from labyrinthes.application.logos import _logo_path

        path = _logo_path(logo_key)
        img = Image.open(path)
        img = img.resize((24, 24), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None
```
The 24×24 size matches the heading font height (`TYPOGRAPHY.heading_sm` ≈ 24px). The logo label uses `background=colors.window` so it blends with the top bar.

Settings logo change → top bar update: the Settings window writes the setting immediately. The top bar only refreshes on `mount()`, so the new logo appears on the next navigation or theme toggle (which triggers a re-navigate). This is acceptable — the UX spec prioritizes non-alarmist behavior over live sync for secondary branding elements. The logo image itself is theme-agnostic; only the top bar background/colors change with theme.

## Verification

**Commands:**
- `ruff check .` -- expected: no errors
- `ruff format --check .` -- expected: no reformatting needed
- `pytest -q` -- expected: all tests pass, including new top-bar logo tests

**Manual checks (if no CLI):**
- Launch app: Home top bar shows default logo + "Labyrinthes".
- Open Settings (from Player), change logo to "water", close Settings, navigate to Home → logo updated.
- Open Builder → logo matches.
- Delete a logo file, restart → text-only, no crash.