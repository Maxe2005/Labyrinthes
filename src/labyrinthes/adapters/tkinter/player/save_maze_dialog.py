"""`SaveMazeDialog` -- name-entry dialog for saving a generated maze (Story 2.3).

A `tk.Toplevel` parented to `GameplayScreen`, modeled on
`generate_random_dialog.py`: nothing here is worth surviving a
navigate-away, so it is never parented to the app's persistent container
(unlike `SettingsWindow` -- see that module's docstring for the contrast).

The name field's own shape validation (empty-after-stripping / contains a
path separator) duplicates `adapters/storage/paths.py::maze_file_path`'s
two rules rather than importing them -- `adapters/tkinter/player/` never
imports `adapters/storage/` directly (AD-9). The entered name is
`.strip()`-ped before validation, collision-checking, and `on_confirm` --
a whitespace-only name is rejected as empty, and leading/trailing
whitespace can't produce an invisible near-duplicate of an existing name
that bypasses the collision warning.

Duplicate-name handling is a two-click arm/confirm *inside this dialog*,
not a separate confirmation dialog (Story 2.3 establishes this pattern;
see the story's Design Notes -- FR-5's "match the Builder's save
behavior" points at Story 3.6, not yet implemented anywhere). The first
click on a name already in `existing_names` shows an inline warning and
relabels the Save button "Overwrite" without saving; a second click on the
*same, unchanged* name performs the save via `on_confirm`. Arming is keyed
off the field's exact raw text, so only an actual edit (not a
cursor-only key like an arrow/Home/End) resets it back to "Save".

`Cancel` (default `PillButton`) and `<Escape>` both close the dialog with
no side effect. `<Return>` in the name field triggers Save, mirroring
`GenerateRandomDialog`'s own field-to-primary-action binding. "s"/"S"
keystrokes in the name field are locally consumed (`"break"`) before
`bind_all()`'s global `save_maze` shortcut can see them -- the same guard
`ClassicMazeGallery`'s jump entry already applies to "n"/"N" -- since a
maze *name* is far likelier to contain "s" than a numeric field is to
contain "n", and without it a second `SaveMazeDialog` would stack on top
of this one mid-typing. Story 2.4 adds the same guard for the arrow keys
(`Up`/`Down`/`Left`/`Right`, the real Tk keysyms -- not lowercase): the
global `move_*` shortcuts are now also registered via `bind_all()`
(`GameplayScreen`), so without this, editing the cursor position while
typing a save name would also move the ball behind this dialog.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from labyrinthes.adapters.tkinter.common.pill_btn import PillButton
from labyrinthes.adapters.tkinter.common.tokens import SPACING, TYPOGRAPHY, Theme, colors_for

__all__ = ["SaveMazeDialog"]

_NAME_REQUIRED_MESSAGE = "Name is required."
_PATH_SEPARATOR_MESSAGE = "Name must not contain a path separator."
_PATH_SEPARATORS = ("/", "\\")

OnConfirmFn = Callable[[str], None]


def _validate_name(name: str) -> str | None:
    """The inline error for `name`, or `None` if it's shape-valid.

    Duplicates `maze_file_path`'s two rules (empty / contains a path
    separator) locally rather than importing them from `adapters/storage/`
    (AD-9, see the module docstring).
    """
    if not name:
        return _NAME_REQUIRED_MESSAGE
    if any(separator in name for separator in _PATH_SEPARATORS):
        return _PATH_SEPARATOR_MESSAGE
    return None


class SaveMazeDialog(tk.Toplevel):
    """Name entry, live validation, and arm/confirm overwrite for saving a maze."""

    def __init__(
        self,
        parent: tk.Widget,
        *,
        theme: Theme,
        existing_names: list[str],
        on_confirm: OnConfirmFn,
    ) -> None:
        super().__init__(parent)
        self.title("Save maze")
        self._theme = theme
        self._existing_names = existing_names
        self._on_confirm = on_confirm
        self._armed_name: str | None = None

        colors = colors_for(theme)
        self.configure(background=colors.window)

        form = tk.Frame(self, background=colors.window)
        form.pack(padx=SPACING["2xl"], pady=SPACING["2xl"], fill="both", expand=True)

        row = tk.Frame(form, background=colors.window)
        row.pack(fill="x", pady=(0, SPACING["xs"]))

        tk.Label(
            row,
            text="Name",
            font=TYPOGRAPHY.body.to_tk_font(),
            background=colors.window,
            foreground=colors.ink,
            width=12,
            anchor="w",
        ).pack(side="left")

        self._name_entry = tk.Entry(row, width=24)
        self._name_entry.pack(side="left")
        self._name_entry.bind("<KeyRelease>", self._on_name_changed)
        self._name_entry.bind("<Return>", self._on_save_clicked)
        # Consume "s"/"S" locally before they reach the global `save_maze`
        # shortcut's `bind_all()` handler -- mirrors `ClassicMazeGallery`'s
        # jump-entry guard for "n"/"N" (see that module's comment).
        # Otherwise typing an "s" into a maze *name* (far likelier than into
        # a numeric field) both inserts the character and reopens a second
        # `SaveMazeDialog` stacked on this one.
        self._name_entry.bind("<KeyPress-s>", lambda _event: "break")
        self._name_entry.bind("<KeyPress-S>", lambda _event: "break")
        # Story 2.4's now-global movement shortcuts are *not* guarded the
        # same "break" way here: an instance-level "break" stops Tk's
        # bindtag scan before the "Entry" class binding ever runs, which is
        # what performs cursor movement/self-insert -- confirmed live, a
        # "break" guard on Up/Down/Left/Right would silently disable the
        # entry's own cursor navigation, not just suppress the shortcut.
        # `GameplayScreen._on_move` guards itself instead (see its
        # docstring), by checking focus before moving the ball -- this
        # dialog's `_name_entry` needs no changes for that to work.
        self._name_entry.focus_set()

        self._message_label = tk.Label(
            form,
            text="",
            font=TYPOGRAPHY.body_secondary.to_tk_font(),
            background=colors.window,
            foreground=colors.exit,
            anchor="w",
            justify="left",
            wraplength=360,
        )
        self._message_label.pack(fill="x", pady=(0, SPACING["sm"]))

        buttons = tk.Frame(self, background=colors.window)
        buttons.pack(padx=SPACING["2xl"], pady=(0, SPACING["2xl"]), anchor="e")

        self._cancel_button = PillButton(buttons, "Cancel", theme=theme, command=self._on_cancel)
        self._cancel_button.pack(side="left", padx=(0, SPACING["sm"]))

        self._save_button = PillButton(
            buttons, "Save", theme=theme, primary=True, command=self._on_save_clicked
        )
        self._save_button.pack(side="left")

        self.bind("<Escape>", self._on_cancel)

    # -- arming --------------------------------------------------------

    def _reset_arming(self) -> None:
        if self._armed_name is not None:
            self._armed_name = None
            self._save_button.set_text("Save")

    def _on_name_changed(self, _event: tk.Event | None = None) -> None:
        # Compared against the raw (unstripped) field text, the same value
        # `_armed_name` was captured from -- a non-content `<KeyRelease>`
        # (arrow keys, Home/End, Shift) fires this handler too but leaves
        # the text unchanged, so arming must survive it; only an actual
        # edit resets it.
        if self._name_entry.get() != self._armed_name:
            self._reset_arming()
        if self._armed_name is not None:
            # Still armed (a cursor-only keystroke left the text and thus
            # the arming untouched) -- leave the overwrite warning in place
            # rather than clearing it out from under the still-"Overwrite"
            # button, which would leave the button with no visible
            # explanation of what it's about to overwrite.
            return
        self._message_label.configure(text=_validate_name(self._name_entry.get().strip()) or "")

    # -- actions ---------------------------------------------------

    def _on_save_clicked(self, _event: tk.Event | None = None) -> None:
        raw = self._name_entry.get()
        name = raw.strip()
        error = _validate_name(name)
        if error is not None:
            self._reset_arming()
            self._message_label.configure(text=error)
            return

        if name in self._existing_names and self._armed_name != raw:
            # First click on a colliding name: arm, warn, relabel -- no
            # save yet (see the module docstring's arm/confirm summary).
            self._armed_name = raw
            self._save_button.set_text("Overwrite")
            self._message_label.configure(
                text=f"A maze named '{name}' already exists — Save again to overwrite it."
            )
            return

        # Destroy *before* invoking `on_confirm` -- `on_confirm` typically
        # triggers the owning widget's own re-render (e.g.
        # `GameplayScreen._build_save_zone()`, which destroys its own
        # children), and this dialog is one of those children. Closing
        # this dialog's own window first, via its own controlled path,
        # means that rebuild's cleanup loop no longer needs to tear down an
        # already-executing handler's window as an incidental side effect.
        self.destroy()
        self._on_confirm(name)

    def _on_cancel(self, _event: tk.Event | None = None) -> None:
        self.destroy()
