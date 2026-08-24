"""`_SaveNameDialog` -- name entry, live validation, and arm/confirm overwrite
for the Builder's Save flow (Story 3.6).

Mirrors `player/save_maze_dialog.py`'s `SaveMazeDialog` (Story 2.3)
deliberately: FR-5's "match the Builder's save behavior" was written against
*this* story providing the shape `SaveMazeDialog` follows, so the two are
kept in lock-step -- a duplicate-name collision arms the Save button
(relabeled "Overwrite") and shows an inline warning rather than saving
immediately; a second click on the *same, unchanged* name confirms the
overwrite. Kept local rather than imported from `adapters/tkinter/player/`
per AD-1/AD-9/AD-10 (Builder and Player never import each other); unifying
this with `SaveMazeDialog` into `adapters/tkinter/common/` is a reasonable
follow-up (AD-11), not done here.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from labyrinthes.adapters.tkinter.common import SPACING, TYPOGRAPHY, PillButton, Theme
from labyrinthes.adapters.tkinter.common.tokens import colors_for

__all__ = ["_SaveNameDialog"]

_NAME_REQUIRED_MESSAGE = "Name is required."
_PATH_SEPARATOR_MESSAGE = "Name must not contain a path separator."
_PATH_SEPARATORS = ("/", "\\")


def _validate_save_name(name: str) -> str | None:
    """The inline error for `name`, or `None` if it's shape-valid.

    Duplicates `player/save_maze_dialog.py::_validate_name`'s two rules
    (empty / contains a path separator) locally rather than importing them
    -- `adapters/tkinter/builder/` never imports `adapters/tkinter/player/`
    (AD-1, AD-9/AD-10), so the rules are kept in sync by convention, the
    same way `save_maze_dialog.py` itself duplicates them from
    `adapters/storage/paths.py::maze_file_path` rather than importing that
    (AD-9's Builder/Player-never-import-each-other applies one layer up:
    neither screen package imports the storage adapter directly either).
    """
    if not name:
        return _NAME_REQUIRED_MESSAGE
    if any(separator in name for separator in _PATH_SEPARATORS):
        return _PATH_SEPARATOR_MESSAGE
    return None


class _SaveNameDialog(tk.Toplevel):
    """Name entry, live validation, and arm/confirm overwrite for the Save flow.

    See the module docstring for how this mirrors `player/save_maze_dialog.py`'s
    `SaveMazeDialog`.
    """

    def __init__(
        self,
        parent: tk.Widget,
        *,
        theme: Theme,
        suggested_name: str,
        existing_names: list[str],
        on_confirm: Callable[[str], None],
    ) -> None:
        super().__init__(parent)
        self.title("Save")
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
        self._name_entry.insert(0, suggested_name)
        self._name_entry.select_range(0, "end")
        self._name_entry.pack(side="left")
        self._name_entry.bind("<KeyRelease>", self._on_name_changed)
        self._name_entry.bind("<Return>", self._on_save_clicked)
        # Consume "s"/"S" and "t"/"T" locally before they reach the global
        # `save_maze`/`test_in_player` shortcuts' `bind_all()` handlers --
        # same guard as `SaveMazeDialog._name_entry` (Story 2.3/2.4):
        # otherwise typing a "t" into a maze *name* while the dialog is open
        # fires `_test_in_player` and navigates away mid-save, abandoning
        # the dialog and the session (Story 3.8's review finding), and
        # typing an "s" both inserts the character and reopens a second
        # `_SaveNameDialog` stacked on this one.
        self._name_entry.bind("<KeyPress-s>", lambda _event: "break")
        self._name_entry.bind("<KeyPress-S>", lambda _event: "break")
        self._name_entry.bind("<KeyPress-t>", lambda _event: "break")
        self._name_entry.bind("<KeyPress-T>", lambda _event: "break")
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
            return
        self._message_label.configure(
            text=_validate_save_name(self._name_entry.get().strip()) or ""
        )

    # -- actions ---------------------------------------------------

    def _on_save_clicked(self, _event: tk.Event | None = None) -> None:
        raw = self._name_entry.get()
        name = raw.strip()
        error = _validate_save_name(name)
        if error is not None:
            self._reset_arming()
            self._message_label.configure(text=error)
            return

        if name in self._existing_names and self._armed_name != raw:
            # First click on a colliding name: arm, warn, relabel -- no
            # save yet.
            self._armed_name = raw
            self._save_button.set_text("Overwrite")
            self._message_label.configure(
                text=f'A maze named "{name}" already exists — Save again to overwrite it.'
            )
            return

        # Destroy before invoking `on_confirm`: `on_confirm` triggers
        # `_navigate()`, which mounts a fresh Builder frame -- closing this
        # dialog's own window first, via its own controlled path, avoids
        # relying on that navigation's frame teardown to also clean this up.
        self.destroy()
        self._on_confirm(name)

    def _on_cancel(self, _event: tk.Event | None = None) -> None:
        self.destroy()
