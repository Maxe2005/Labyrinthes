"""`ConfirmDialog` -- the shared non-modal confirmation-prompt dialog (Story 2.10).

The first of AD-11's "confirmation-prompt dialogs": a themed `Toplevel`
with a message, a primary Confirm `PillButton`, and an optional Cancel
`PillButton`. `<Return>` confirms from anywhere in the dialog (Tk's
bindtags include the toplevel, so the binding fires whatever widget holds
focus); `<Escape>` and the WM close button cancel. Initial focus lands on
the Confirm pill (NFR6).

Deliberately **non-modal** (no `grab_set()`): the codebase-wide dialog
convention is non-modal (`SettingsWindow`/`SaveMazeDialog`/
`GenerateRandomDialog` all assert `grab_status() is None`), and a
`grab_set()` under the withdrawn `tk_root` test fixture raises
`TclError: grab failed: window not viewable`. Because the dialog can't
block its source action, every gated action carries an explicit open-dialog
guard on the owning screen (`_confirm_dialog is not None` -> no-op) so a
second trigger never stacks a second dialog -- see the story's Design Notes.

Alert mode: `cancel_label=None` + `on_confirm=None` + `confirm_label="OK"`
renders a single OK pill used for the legacy `alerte mauvaise entree`
(invalid-input) prompt -- OK/Escape/WM-close all just dismiss.

`on_confirm`/`on_close` are optional and skipped when `None`.
`_on_confirm_clicked`/`_on_cancel_clicked` both call `on_close()` first
(the owning screen's guard-clear), destroy, and only then call
`on_confirm()` (confirm path). Parented to the screen that opens it (not
the app's persistent container, unlike `SettingsWindow`) so it is
cascade-destroyed with that screen on a navigate-away -- the same
lifecycle as `GenerateRandomDialog`. Registers no binding in the canonical
keybinding table (Story 1.10): `<Return>`/`<Escape>` are standard dialog
affordances, not app shortcuts.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from labyrinthes.adapters.tkinter.common.pill_btn import PillButton
from labyrinthes.adapters.tkinter.common.tokens import SPACING, TYPOGRAPHY, Theme, colors_for

__all__ = ["ConfirmDialog"]

OnConfirmFn = Callable[[], None]
OnCloseFn = Callable[[], None]


class ConfirmDialog(tk.Toplevel):
    """A themed, non-modal yes/no (or OK-only alert) confirmation prompt."""

    def __init__(
        self,
        parent: tk.Widget,
        *,
        theme: Theme,
        message: str,
        on_confirm: OnConfirmFn | None = None,
        on_close: OnCloseFn | None = None,
        confirm_label: str = "Confirm",
        cancel_label: str | None = "Cancel",
    ) -> None:
        super().__init__(parent)
        self.title("Confirm")
        self._theme = theme
        self._on_confirm = on_confirm
        self._on_close = on_close

        colors = colors_for(theme)
        self.configure(background=colors.window)

        form = tk.Frame(self, background=colors.window)
        form.pack(padx=SPACING["2xl"], pady=SPACING["2xl"], fill="both", expand=True)

        tk.Label(
            form,
            text=message,
            font=TYPOGRAPHY.body.to_tk_font(),
            background=colors.window,
            foreground=colors.ink,
            wraplength=320,
            justify="left",
        ).pack(anchor="w", pady=(0, SPACING["lg"]))

        buttons = tk.Frame(form, background=colors.window)
        buttons.pack(anchor="e")

        if cancel_label is not None:
            self._cancel_button = PillButton(
                buttons,
                cancel_label,
                theme=theme,
                primary=False,
                command=self._on_cancel_clicked,
            )
            self._cancel_button.pack(side="left", padx=(0, SPACING["sm"]))

        self._confirm_button = PillButton(
            buttons,
            confirm_label,
            theme=theme,
            primary=True,
            command=self._on_confirm_clicked,
        )
        self._confirm_button.pack(side="left")
        self._confirm_button.focus_set()

        self.bind("<Return>", self._on_confirm_clicked)
        self.bind("<Escape>", self._on_cancel_clicked)
        self.protocol("WM_DELETE_WINDOW", self._on_cancel_clicked)

        # Sit above the owning screen (not modal -- `lift()` only) so the
        # prompt is visibly in front of the action that opened it.
        self.transient(parent)
        self.lift()

    def _close(self, confirmed: bool) -> None:
        # `on_close` first (the owning screen's guard-clear), then destroy,
        # then `on_confirm` -- mirroring `SaveMazeDialog`'s destroy-before-
        # callback order so `on_confirm`'s re-render never tears down a
        # handler's own window as an incidental side effect.
        if self._on_close is not None:
            self._on_close()
        self.destroy()
        if confirmed and self._on_confirm is not None:
            self._on_confirm()

    def _on_confirm_clicked(self, _event: tk.Event | None = None) -> None:
        self._close(confirmed=True)

    def _on_cancel_clicked(self, _event: tk.Event | None = None) -> None:
        self._close(confirmed=False)
