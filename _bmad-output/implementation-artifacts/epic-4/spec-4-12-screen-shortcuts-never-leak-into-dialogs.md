---
title: 'Story 4.12: Screen shortcuts never fire while a text-entry dialog is focused'
type: 'bugfix'
created: '2026-09-04'
status: 'done'
review_loop_iteration: 0
context:
  - _bmad-output/implementation-artifacts/epic-4/epic-4-context.md
baseline_commit: e6011997e5d82124250b21c4af26481b3e84db28
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `bind_shortcut()` (`adapters/tkinter/common/keybindings.py`) registers every screen shortcut via `widget.bind_all()`, which fires regardless of Tk focus. Two dialogs (`_SaveNameDialog`, `SaveMazeDialog`) work around this by binding their own per-letter `<KeyPress-x>` → `"break"` guards on the name entry — but this stops Tk's bindtag scan *before* the `Entry` class binding runs, so it also silently blocks those letters from ever being typed into the name field. It's also enumerably incomplete: 11 of 13 Builder shortcuts plus Space/Enter remain unguarded there.

**Approach:** Give `bind_shortcut()`'s dispatch handler a single focus-aware guard: skip `callback()` (never `"break"`) when `widget.focus_get()` is a `tk.Entry`/`tk.Text`. Delete the two dialogs' now-redundant, now-provably-buggy per-letter guards — their letters will type normally again, and the shortcut is still suppressed, this time without misfiring.

## Boundaries & Constraints

**Always:**
- `bind_shortcut()`'s inner `handler()` (`keybindings.py:158-159`) checks `widget.focus_get()`; if it is a `tk.Entry` or `tk.Text` instance, `handler` returns without calling `callback()`. No `"break"` is ever returned by `handler` — unaffected by this change either way, since `bind_all` is the last-checked bindtag.
- Delete `_SaveNameDialog`'s four guards (`builder/save_dialog.py:97-108`, comment + `<KeyPress-s/S/t/T>`) and `SaveMazeDialog`'s two guards (`player/save_maze_dialog.py:114-121`, comment + `<KeyPress-s/S>`) — the centralized guard supersedes them.
- `KEYBINDINGS`, `Keybinding.scope`, and both collision tests in `test_keybindings.py` stay untouched — dispatch-only fix.
- `GameplayScreen._toplevel_has_focus()` (guards movement/mode-toggle against *other Toplevels*, not text focus) is untouched — different mechanism, still needed.

**Ask First:** None — FR-36 and the sprint-change-proposal (2026-08-25) fully determine scope.

**Never:** Never touch `NewMazeDialog`'s or `GenerateRandomDialog`'s existing per-letter guards (`common/new_maze_dialog.py:138-139`, `player/generate_random_dialog.py:140-141`) — their fields are numeric, the guarded letters (b/c/p/n) are never legitimately typed there, so leaving them is zero-cost and the new centralized guard makes them belt-and-suspenders, not required reading for this story. Never widen the guard to non-text widgets — `SettingsWindow`'s broader no-`grab_set()` gap (deferred-work.md, spec-4-8 review) stays open for anything that isn't a focused `tk.Entry`/`tk.Text`; only that case is FR-36's scope.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Type a shortcut letter while a dialog's `tk.Entry` has focus | `SaveMazeDialog` open, `_name_entry` focused, user types "s" | Character "s" is inserted normally; `save_maze` does not fire | N/A |
| Type the same letter while no dialog is open | Player screen focused (canvas), user presses "s" | `save_maze` fires as before | N/A |
| Shortcut key pressed while focus is on a non-text widget inside an open dialog | e.g. a `tk.Button` inside `NewMazeDialog` has focus | Shortcut still fires (known, explicitly out-of-scope gap) | N/A |
| `NewMazeDialog`/`GenerateRandomDialog` numeric field focused, guarded letter typed | e.g. "b" typed in `NewMazeDialog`'s width field | Existing local `"break"` guard still consumes it (unchanged); centralized guard is redundant here, not exercised | N/A |

</frozen-after-approval>

## Code Map

- `src/labyrinthes/adapters/tkinter/common/keybindings.py:158-159` -- `bind_shortcut()`'s `handler()`; add the focus check here, closing over `widget` (already a parameter)
- `src/labyrinthes/adapters/tkinter/builder/save_dialog.py:97-108` -- `_SaveNameDialog`, delete comment + 4 `bind()` calls
- `src/labyrinthes/adapters/tkinter/player/save_maze_dialog.py:114-121` -- `SaveMazeDialog`, delete comment + 2 `bind()` calls
- `tests/adapters/tkinter/common/test_keybindings.py` -- add focus-guard tests near existing `test_bind_shortcut_*` tests (imports `tk`, has `tk_root` fixture already)
- `tests/adapters/tkinter/player/test_save_maze_dialog.py:154-164` -- `test_name_entry_locally_consumes_s_before_the_global_save_maze_shortcut` now asserts a binding that no longer exists; replace it
- `tests/adapters/tkinter/builder/test_builder_save_flow.py` -- no existing `KeyPress` assertions to remove (searched); optionally add one new regression test mirroring the Player-side replacement

## Tasks & Acceptance

**Execution:**
- [x] `keybindings.py` -- add the `focus_get()` guard to `handler()` -- AC 1, 2
- [x] `builder/save_dialog.py` -- delete the four now-buggy `"s"/"t"` guards -- AC 3
- [x] `player/save_maze_dialog.py` -- delete the two now-buggy `"s"` guards -- AC 3
- [x] `test_keybindings.py` -- add: focused `tk.Entry` suppresses callback; focused `tk.Text` suppresses callback; non-text focus (or no focus) still fires -- AC 1, 2
- [x] `test_save_maze_dialog.py` -- replace the obsolete "locally consumes" test with one asserting: (a) no `<KeyPress-s>` binding exists on `_name_entry`, (b) typing "s" via the real `bind_shortcut()`-registered handler with the entry focused does not invoke `on_confirm`/the save callback -- AC 3, 4
- [x] Run `ruff check .`, `ruff format --check .`, `pytest -q` -- all green -- AC 1-4

**Acceptance Criteria:**
- Given any shortcut registered via `bind_shortcut()`, when the Tk focus widget is a `tk.Entry`/`tk.Text`, then `handler()` returns without calling `callback()`.
- Given the same shortcut, when focus is elsewhere (or unset), then `callback()` still fires exactly as before.
- Given `_SaveNameDialog`/`SaveMazeDialog`'s name entries, when a user types "s", "t", "S", or "T", then the character is inserted into the field and no global shortcut fires.
- Given `test_keybindings.py`'s two collision tests, when this story lands, then they still pass unchanged.

## Design Notes

Tk's bindtag order is (widget-instance, class, toplevel, "all"); `bind_all` registers on "all", the *last* tag checked. A class binding (e.g. `Entry`'s built-in character-insertion binding) already ran by the time "all" is reached, regardless of what "all"'s handler returns — so the new guard only needs to skip `callback()`, never `"break"`, and character insertion is unaffected either way. This is also why the old instance-level `"break"` guards were the actual bug: they preempted the *class* binding before it could run, blocking insertion outright, not just the shortcut.

`focus_get()` is called on `widget` (the argument already passed into `bind_shortcut()`), consistent with `GameplayScreen._toplevel_has_focus()`'s existing `self.focus_get()` precedent elsewhere in the codebase.

## Verification

**Commands:**
- `ruff check .` -- expected: no errors
- `ruff format --check .` -- expected: no reformatting needed
- `pytest -q` -- expected: all tests pass, including the new focus-guard tests and the updated `SaveMazeDialog` test

**Manual checks (if no CLI):**
- Launch the Builder, open Save-as-Maze, type a name containing "s" and "t" — both characters appear in the field, no dialog reopens, no navigation to Player.
- Launch the Player, open Save Maze, type a name containing "s" — same result.

## Suggested Review Order

**Centralized dispatch guard**

- Entry point: the one guard that replaces every per-dialog workaround — skip the callback, never `"break"`, when focus is a text field.
  [`keybindings.py:175-177`](../../../src/labyrinthes/adapters/tkinter/common/keybindings.py#L175)

- Documents the new contract and why `GameplayScreen._toplevel_has_focus()` stays a separate, non-consolidated guard.
  [`keybindings.py:156-163`](../../../src/labyrinthes/adapters/tkinter/common/keybindings.py#L156)

**Dialog cleanup (now-redundant, now-provably-buggy guards removed)**

- The four `"s"/"S"/"t"/"T"` `"break"` guards that used to pre-empt the `Entry` class binding are gone.
  [`builder/save_dialog.py:97`](../../../src/labyrinthes/adapters/tkinter/builder/save_dialog.py#L97)

- Same cleanup on the Player side; comment reworded to not overstate similarity with `GameplayScreen._on_move`'s guard.
  [`player/save_maze_dialog.py:111-127`](../../../src/labyrinthes/adapters/tkinter/player/save_maze_dialog.py#L111)

**Tests — dispatch guard (unit level)**

- Focused `tk.Entry` suppresses the callback — the core regression.
  [`test_keybindings.py:296`](../../../tests/adapters/tkinter/common/test_keybindings.py#L296)

- Same for `tk.Text`; non-text focus and no-focus still fire normally.
  [`test_keybindings.py:330`](../../../tests/adapters/tkinter/common/test_keybindings.py#L330)

**Tests — real dialogs (integration level)**

- Builder: "s" no longer fires `save_maze` while the name entry is focused.
  [`test_builder_save_flow.py:465`](../../../tests/adapters/tkinter/builder/test_builder_save_flow.py#L465)

- Builder: "t" no longer fires `test_in_player` mid-save — the original, more severe motivating bug.
  [`test_builder_save_flow.py:502`](../../../tests/adapters/tkinter/builder/test_builder_save_flow.py#L502)

- Player: mirrors the Builder's "s" regression test for `SaveMazeDialog`.
  [`test_save_maze_dialog.py:167`](../../../tests/adapters/tkinter/player/test_save_maze_dialog.py#L167)

- Peripheral: proves no local `"break"` binding remains on either dialog's name entry.
  [`test_builder_save_flow.py:432`](../../../tests/adapters/tkinter/builder/test_builder_save_flow.py#L432)
