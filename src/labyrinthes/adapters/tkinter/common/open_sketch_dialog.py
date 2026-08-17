"""`OpenSketchDialog` -- dialog for opening an existing Sketch (Story 3.1).

A `tk.Toplevel` parented to the calling widget, not the app's persistent
container: nothing here is worth surviving a navigate-away, unlike
`SettingsWindow` (see that module's docstring for the contrast).

Uses the shared `read_maze_size_bounds` from settings (FR-4: "The bounds
are defined once, in settings, and read by both the Builder and the Game").
After the user selects a sketch, the dialog loads it via `MazeRepository`
and calls the `on_confirm` callback with the loaded `Maze` object.

The on_confirm signature is `OnConfirmFn = Callable[[Maze], None]` -- unlike
`GenerateRandomDialog` which passes width/rows/position separately, this
encapsulates the full maze so the caller can navigate wherever it needs.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from labyrinthes.adapters.tkinter.common.tokens import SPACING, TYPOGRAPHY, Theme, colors_for
from labyrinthes.application.maze_repository import MazeKind, MazeRepository
from labyrinthes.application.settings_repository import SettingsRepository
from labyrinthes.domain.maze import Maze

OnConfirmFn = Callable[[Maze], None]


class OpenSketchDialog(tk.Toplevel):
    """Dialog for selecting and opening an existing Sketch."""

    def __init__(
        self,
        parent: tk.Widget,
        *,
        theme: Theme,
        settings_repository: SettingsRepository,
        maze_repository: MazeRepository,
        on_confirm: OnConfirmFn,
    ) -> None:
        super().__init__(parent)
        self.title("Open Sketch")
        self._theme = theme
        self._settings_repository = settings_repository
        self._maze_repository = maze_repository
        self._on_confirm = on_confirm

        colors = colors_for(theme)
        self.configure(background=colors.window)

        form = tk.Frame(self, background=colors.window)
        form.pack(padx=SPACING["2xl"], pady=SPACING["2xl"], fill="both", expand=True)

        # Sketch selection label and dropdown
        tk.Label(
            form,
            text="Select a sketch:",
            font=TYPOGRAPHY.body.to_tk_font(),
            background=colors.window,
            foreground=colors.ink,
            anchor="w",
        ).pack(fill="x", pady=(0, SPACING["xs"]))

        self._sketch_var = tk.StringVar()
        sketches = self._maze_repository.list_names(MazeKind.SKETCH)
        if sketches:
            self._sketch_menu = tk.OptionMenu(form, self._sketch_var, *sketches)
            self._sketch_menu.pack(fill="x", pady=(0, SPACING["xs"]))
            # Select first sketch by default
            self._sketch_var.set(sketches[0])
        else:
            self._no_sketch_label = tk.Label(
                form,
                text="No sketches found. Create a new maze instead.",
                font=TYPOGRAPHY.body_secondary.to_tk_font(),
                background=colors.window,
                foreground=colors.exit,
                anchor="w",
            )
            self._no_sketch_label.pack(fill="x", pady=(0, SPACING["xs"]))

        # Error display
        self._error_label = tk.Label(
            form,
            text="",
            font=TYPOGRAPHY.body_secondary.to_tk_font(),
            background=colors.window,
            foreground=colors.exit,
            anchor="w",
        )
        self._error_label.pack(fill="x", pady=(0, SPACING["lg"]))

        # Buttons
        buttons = tk.Frame(self, background=colors.window)
        buttons.pack(padx=SPACING["2xl"], pady=(0, SPACING["2xl"]), anchor="e")

        self._cancel_button = ttk.Button(buttons, text="Cancel", command=self._on_cancel)
        self._cancel_button.pack(side="left", padx=(0, SPACING["sm"]))

        self._confirm_button = ttk.Button(
            buttons, text="Open", command=self._on_confirm_clicked, state="disabled"
        )
        self._confirm_button.pack(side="left")

        self.bind("<Escape>", self._on_cancel)

        self._validate()

    # -- validation ---------------------------------------------------

    def _parsed_selection(self) -> str | None:
        return self._sketch_var.get() if hasattr(self, "_sketch_var") else None

    def _compute_errors(self) -> str | None:
        selection = self._parsed_selection()
        if selection is None:
            return "Select a sketch to open."
        if not hasattr(self, "_no_sketch_label"):
            return None
        # If there are no sketches, we can't open one
        if not hasattr(self, "_no_sketch_label"):
            return "No sketches available."
        return None

    def _validate(self) -> None:
        errors = self._compute_errors()
        self._error_label.configure(text=errors or "")
        if errors:
            self._confirm_button.configure(state="disabled")
        else:
            self._confirm_button.configure(state="normal")

    # -- actions ---------------------------------------------------

    def _on_field_changed(self, _event: tk.Event | None = None) -> None:
        self._validate()

    def _on_confirm_clicked(self) -> None:
        selection = self._parsed_selection()
        if selection is None:
            return
        try:
            maze: Maze = self._maze_repository.load(selection, MazeKind.SKETCH)
        except Exception as e:
            self._error_label.configure(text=f"Failed to load sketch: {e}")
            self._confirm_button.configure(state="disabled")
            return
        self._on_confirm(maze)
        self.destroy()

    def _on_cancel(self, _event: tk.Event | None = None) -> None:
        self.destroy()


__all__ = ["OpenSketchDialog", "OnConfirmFn"]
