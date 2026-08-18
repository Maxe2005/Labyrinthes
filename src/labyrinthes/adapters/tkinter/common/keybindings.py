"""The canonical keybinding table -- one source of truth (Story 1.10).

Story 3.2 adds a `scope: ScreenId | None` field: keys are unique *within*
each scope group, not globally. Entries with `scope=None` (every
pre-existing entry) form one group; entries with an explicit `ScreenId`
form their own separate group. This lets 'b'/'p' mean `open_builder`/
`open_player` on Home (scope=None) and *also* `break_wall`/`pass_through`
on Builder (scope=`ScreenId.BUILDER`) without a collision: Home and
Builder are never mounted simultaneously, so their real `bind_all()`
registrations never coexist, even though both keys appear (in different
groups) in this one table.

Before this module, `kbd_tag.py` printed shortcut text with no key binding
behind it (its own docstring called this out as "Story 1.10's job"), and
nothing stopped two controls from printing the same letter. Every printed
`kbd-tag` and every real `bind_all()` registration is meant to derive from
one `Keybinding` entry here, not from two independent literals a future
edit could let drift apart -- `.display` (what gets printed) and `.event`
(what gets bound) are both computed from the single `key` field for exactly
that reason. `KEYBINDINGS` is the full table; `test_keybindings.py` asserts
no two entries share a `key`, so a collision is caught by an automated test
rather than discovered by two shortcuts silently fighting over the same
key press at runtime.

`bind_shortcut()` is the one place a screen wires a `Keybinding` into a
real, live binding. It uses `widget.bind_all()`, not `widget.bind()`,
because a screen-wide shortcut must fire no matter which child widget
currently holds focus -- a plain `bind()` only fires when the bound widget
itself is focused. It binds both the lower- and upper-case keysym for
`key` (X11 treats Shift+B and a CapsLock-typed "b" as the keysym `"B"`,
distinct from plain `"b"`) so the shortcut fires regardless of case, since
the printed `kbd-tag` is always uppercase.

Since `bind_all()` is global to the whole Tk interpreter, `bind_shortcut()`
also binds the widget's own `<Destroy>` to unregister it -- but a screen
that re-navigates to *itself* (e.g. Story 1.9's theme toggle re-rendering
the current screen) mounts its new frame, and registers its shortcuts,
*before* the old frame is torn down (`Router.navigate()`'s new-before-old
ordering). A naive unconditional `unbind_all()` on the old frame's
`<Destroy>` would then wipe out the *new* frame's just-installed binding
for the same key, since `unbind_all()` clears whichever registration is
currently live, not specifically "the one this call installed". A small
per-interpreter, per-sequence token registry guards against this: each
`bind_shortcut()` call stamps the sequences it installs with a fresh
token, and its `<Destroy>` cleanup only unbinds if its own token is still
the current one for that sequence -- if a newer call already replaced it,
cleanup is a no-op, leaving the newer registration alone.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass

from labyrinthes.adapters.tkinter.common.navigation import ScreenId

__all__ = ["KEYBINDINGS", "Keybinding", "bind_shortcut", "keybinding"]


@dataclass(frozen=True)
class Keybinding:
    """One canonical shortcut: its action id, printed label, key, and scope.

    `.display`/`.event` are both derived from `key` alone -- there is no
    way to set the printed text and the bound Tk sequence to two different
    keys by accident. `scope` groups entries for uniqueness (see the module
    docstring): `None` for the original screen-agnostic table, an explicit
    `ScreenId` for a key that's only ever bound on that one screen.
    """

    action_id: str
    label: str
    key: str
    scope: ScreenId | None = None

    @property
    def display(self) -> str:
        """The always-visible `kbd-tag` text, e.g. `"b"` -> `"B"`."""
        return self.key.upper()

    @property
    def event(self) -> str:
        """The Tk bind sequence for this key, e.g. `"b"` -> `"<KeyPress-b>"`."""
        return f"<KeyPress-{self.key}>"


KEYBINDINGS: tuple[Keybinding, ...] = (
    Keybinding("open_builder", "Open Builder", "b"),
    Keybinding("open_player", "Open Player", "p"),
    Keybinding("open_new_maze", "New Maze", "c"),
    Keybinding("generate_random", "Generate random", "n"),
    Keybinding("save_maze", "Save", "s"),
    Keybinding("move_up", "Move up", "Up"),
    Keybinding("move_down", "Move down", "Down"),
    Keybinding("move_left", "Move left", "Left"),
    Keybinding("move_right", "Move right", "Right"),
    Keybinding("toggle_movement_mode", "Toggle movement mode", "m"),
    Keybinding("toggle_hard_mode", "Toggle HARD mode", "h"),
    Keybinding("break_wall", "Break Wall", "b", ScreenId.BUILDER),
    Keybinding("pass_through", "Pass-through", "p", ScreenId.BUILDER),
    Keybinding("destroy_zone", "Destroy Zone", "d", ScreenId.BUILDER),
    Keybinding("restore_zone", "Restore Zone", "r", ScreenId.BUILDER),
)

_BY_ACTION_ID: dict[str, Keybinding] = {kb.action_id: kb for kb in KEYBINDINGS}


def keybinding(action_id: str) -> Keybinding:
    """The `Keybinding` registered under `action_id`.

    Raises `KeyError` for an unknown id -- a typo'd action id is a
    programming error, not a runtime condition to degrade gracefully from.
    """
    return _BY_ACTION_ID[action_id]


# `(id(interpreter), sequence) -> token` for whichever `bind_shortcut()`
# call most recently registered `sequence` on that interpreter -- lets a
# `<Destroy>`-triggered cleanup tell "am I still the current registration"
# from "has someone already replaced me" (see the module docstring).
_current_registration: dict[tuple[int, str], object] = {}


def bind_shortcut(
    widget: tk.Misc, kb: Keybinding, callback: Callable[[], None]
) -> Callable[[tk.Event | None], None]:
    """Register `kb` as a real, interpreter-wide key binding firing `callback`.

    Binds both case variants of `kb.key` (see the module docstring) so the
    shortcut fires regardless of Shift/CapsLock state. Returns the wrapped
    handler (ignoring Tk's event argument) so tests can invoke it directly,
    mirroring this codebase's `_on_click()` convention for widgets whose
    real X11 events can't be reliably synthesized under a withdrawn
    `tk_root`.
    """

    def handler(_event: tk.Event | None = None) -> None:
        callback()

    interpreter_id = id(widget.tk)
    # `kb.event` is the canonical lowercase sequence (see its own docstring
    # -- "what gets bound"); reusing it here, rather than re-deriving
    # `f"<KeyPress-{kb.key.lower()}>"` independently, is what keeps that
    # claim actually true instead of two copies of the same derivation
    # that could drift apart.
    sequences = (kb.event,)
    # The uppercase case-variant only makes sense for a single alphabetic
    # keysym (e.g. "b" -> "B", for Shift/CapsLock): a multi-char keysym
    # like "Up" has no such variant, and `f"<KeyPress-{kb.key.upper()}>"`
    # (i.e. "<KeyPress-UP>") is not a valid Tk keysym at all --
    # `widget.bind_all(...)` raises `TclError: bad event type or keysym
    # "UP"` for it (confirmed against a live Tk instance). Guarding this
    # is what lets movement keybindings register at all.
    if len(kb.key) == 1 and kb.key.isalpha():
        sequences += (f"<KeyPress-{kb.key.upper()}>",)
    token = object()
    for sequence in sequences:
        widget.bind_all(sequence, handler)
        _current_registration[(interpreter_id, sequence)] = token

    def _on_destroy(_event: tk.Event | None = None) -> None:
        for sequence in sequences:
            registry_key = (interpreter_id, sequence)
            if _current_registration.get(registry_key) is token:
                widget.unbind_all(sequence)
                del _current_registration[registry_key]

    widget.bind("<Destroy>", _on_destroy, add="+")

    return handler
