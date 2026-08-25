"""`NewMazeDialog` -- the 2-field new-maze dimensions dialog (Story 3.1).

A `tk.Toplevel` parented to the calling widget, not the app's persistent
container: nothing here is worth surviving a navigate-away, unlike
`SettingsWindow` (see that module's docstring for the contrast).

Two `tk.Entry` fields (columns, rows) re-validate on every `<KeyRelease>`
across both, mirroring `GenerateRandomDialog`'s (Story 2.2) per-field
validation shape. An invalid field shows a per-field inline error
(`typography.body_secondary`/`colors.exit`, `DESIGN.md`'s inline-error
convention). Clicking "Create" while any field is invalid leaves the
dialog open with the error still visible and performs no navigation --
the "leave errors visible, no state change" pattern, not a disabled-button
one (no `common/` widget supports one, and the spec explicitly rules it
out).

Field-to-field keyboard navigation (Up/Down, boundary-aware Left/Right,
Enter-advances-then-Create) is delegated to the shared
`FieldNavigator` -- see that module's docstring for the full behavior;
this dialog only supplies the field order and the `Create` button as the
chain's final stop.

Bounds come from the shared `read_maze_size_bounds(settings_repository)`
reader (FR-4: "The bounds are defined once, in settings, and read by both
the Builder and the Game") -- never hardcoded here, and never written back.

The on_confirm signature is `OnConfirmFn = Callable[[Maze], None]` -- unlike
`GenerateRandomDialog` which passes width/rows/position separately, this
encapsulates the full new `Maze` (kind=`MazeKind.SKETCH`, `id=None`) so the
caller can navigate wherever it needs.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from labyrinthes.adapters.tkinter.common.field_navigation import FieldNavigator
from labyrinthes.adapters.tkinter.common.pill_btn import PillButton
from labyrinthes.adapters.tkinter.common.tokens import SPACING, TYPOGRAPHY, Theme, colors_for
from labyrinthes.application.defaults_settings import read_new_maze_defaults
from labyrinthes.application.maze_size_bounds import read_maze_size_bounds
from labyrinthes.application.settings_repository import SettingsRepository
from labyrinthes.domain.grid import Grid
from labyrinthes.domain.maze import Maze, MazeKind
from labyrinthes.domain.maze_size_bounds import validate_dimensions
from labyrinthes.domain.position import Position

__all__ = ["NewMazeDialog", "OnConfirmFn"]

_FIELD_ORDER = ("columns", "rows")
_FIELD_LABELS = {"columns": "Columns", "rows": "Rows"}
_NOT_A_NUMBER_MESSAGE = "Enter a whole number."

OnConfirmFn = Callable[[Maze], None]


class NewMazeDialog(tk.Toplevel):
    """Configure and confirm a new empty sketch maze's columns/rows."""

    def __init__(
        self,
        parent: tk.Widget,
        *,
        theme: Theme,
        settings_repository: SettingsRepository,
        on_confirm: OnConfirmFn,
    ) -> None:
        super().__init__(parent)
        self.title("New Maze")
        self._theme = theme
        self._on_confirm = on_confirm
        # Read-with-fallback, never written back to (see module docstring).
        self._bounds = read_maze_size_bounds(settings_repository)
        # Read defaults at construction time (Story 4.6).
        default_columns, default_rows = read_new_maze_defaults(settings_repository)

        colors = colors_for(theme)
        self.configure(background=colors.window)

        self._entries: dict[str, tk.Entry] = {}
        self._error_labels: dict[str, tk.Label] = {}

        form = tk.Frame(self, background=colors.window)
        form.pack(padx=SPACING["2xl"], pady=SPACING["2xl"], fill="both", expand=True)

        self._add_field(form, "columns", str(default_columns))
        self._add_field(form, "rows", str(default_rows))
        self._entries["columns"].focus_set()

        buttons = tk.Frame(self, background=colors.window)
        buttons.pack(padx=SPACING["2xl"], pady=(0, SPACING["2xl"]), anchor="e")

        self._cancel_button = PillButton(buttons, "Cancel", theme=theme, command=self._on_cancel)
        self._cancel_button.pack(side="left", padx=(0, SPACING["sm"]))

        self._confirm_button = PillButton(
            buttons, "Create", theme=theme, primary=True, command=self._on_confirm_clicked
        )
        self._confirm_button.pack(side="left")

        self._navigator = FieldNavigator(
            [self._entries[key] for key in _FIELD_ORDER], self._confirm_button
        )

        self.bind("<Escape>", self._on_cancel)

        self._validate()

    def _add_field(self, parent: tk.Widget, key: str, initial_text: str) -> None:
        colors = colors_for(self._theme)

        row = tk.Frame(parent, background=colors.window)
        row.pack(fill="x", pady=(0, SPACING["xs"]))

        tk.Label(
            row,
            text=_FIELD_LABELS[key],
            font=TYPOGRAPHY.body.to_tk_font(),
            background=colors.window,
            foreground=colors.ink,
            width=8,
            anchor="w",
        ).pack(side="left")

        entry = tk.Entry(row, width=6)
        entry.insert(0, initial_text)
        entry.pack(side="left")
        entry.bind("<KeyRelease>", self._on_field_changed)
        # Consume "b"/"B", "c"/"C", "p"/"P" locally before they reach the
        # global `open_builder`/`open_new_maze`/`open_player` shortcuts'
        # `bind_all()` handlers -- this dialog is opened from Home while
        # Home's frame (and its shortcuts) are still live, so typing any of
        # these letters (e.g. the "abc" non-numeric-field scenario) would
        # otherwise stack a second dialog or navigate away mid-edit.
        # Mirrors `GenerateRandomDialog`'s identical `<KeyPress-n>` guard
        # (Story 2.2) and `ClassicMazeGallery._jump_entry`'s (Story 2.1).
        for letter in ("b", "B", "c", "C", "p", "P"):
            entry.bind(f"<KeyPress-{letter}>", lambda _event: "break")
        self._entries[key] = entry

        error_label = tk.Label(
            parent,
            text="",
            font=TYPOGRAPHY.body_secondary.to_tk_font(),
            background=colors.window,
            foreground=colors.exit,
            anchor="w",
            justify="left",
        )
        error_label.pack(fill="x", pady=(0, SPACING["sm"]))
        self._error_labels[key] = error_label

    # -- validation ---------------------------------------------------

    def _parsed_fields(self) -> tuple[dict[str, int], dict[str, str]]:
        """Parse every field as a whole number; `(parsed ints, parse-error messages)`."""
        parsed: dict[str, int] = {}
        errors: dict[str, str] = {}
        for key in _FIELD_ORDER:
            text = self._entries[key].get()
            try:
                parsed[key] = int(text)
            except ValueError:
                errors[key] = _NOT_A_NUMBER_MESSAGE
        return parsed, errors

    def _compute_errors(self) -> dict[str, str]:
        """Field-name -> inline error message for every currently-invalid field.

        Each bounds check only requires its own field to have parsed -- a
        parse error in "rows" must never mask an out-of-bounds error already
        knowable in "columns" (and vice versa), mirroring
        `GenerateRandomDialog._compute_errors`'s masking fix.
        """
        parsed, errors = self._parsed_fields()

        if "columns" in parsed:
            height = parsed.get("rows", self._bounds.min_rows)
            for message in validate_dimensions(self._bounds, parsed["columns"], height):
                if message.startswith("Columns"):
                    errors["columns"] = message
        if "rows" in parsed:
            width = parsed.get("columns", self._bounds.min_columns)
            for message in validate_dimensions(self._bounds, width, parsed["rows"]):
                if message.startswith("Rows"):
                    errors["rows"] = message

        return errors

    def _validate(self) -> dict[str, str]:
        errors = self._compute_errors()
        for key, label in self._error_labels.items():
            label.configure(text=errors.get(key, ""))
        return errors

    def _on_field_changed(self, _event: tk.Event | None = None) -> None:
        self._validate()

    # -- actions ---------------------------------------------------

    def _on_confirm_clicked(self, _event: tk.Event | None = None) -> None:
        errors = self._validate()
        if errors:
            # Leave the dialog open with the inline error(s) visible -- no
            # navigation, no maze creation, no state change.
            return
        parsed, _parse_errors = self._parsed_fields()
        columns, rows = parsed["columns"], parsed["rows"]
        maze = Maze(
            grid=Grid.filled(columns, rows),
            entry=Position(row=0, col=0),
            exit=Position(row=rows - 1, col=columns - 1),
            kind=MazeKind.SKETCH,
            id=None,
        )
        self._on_confirm(maze)
        self.destroy()

    def _on_cancel(self, _event: tk.Event | None = None) -> None:
        self.destroy()
