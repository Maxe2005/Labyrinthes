"""The canonical keybinding table -- one source of truth (Story 1.10).

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

__all__ = ["KEYBINDINGS", "Keybinding", "bind_shortcut", "keybinding"]


@dataclass(frozen=True)
class Keybinding:
    """One canonical shortcut: its action id, printed label, and key.

    `.display`/`.event` are both derived from `key` alone -- there is no
    way to set the printed text and the bound Tk sequence to two different
    keys by accident.
    """

    action_id: str
    label: str
    key: str

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
    Keybinding("generate_random", "Generate random", "n"),
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
    sequences = (kb.event, f"<KeyPress-{kb.key.upper()}>")
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
