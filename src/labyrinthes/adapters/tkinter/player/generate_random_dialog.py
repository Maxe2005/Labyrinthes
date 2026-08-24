"""`GenerateRandomDialog` -- the 4-field random-maze configuration dialog (Story 2.2).

A `tk.Toplevel` parented to the `ClassicMazeGallery` instance that opens
it, not the app's persistent container: nothing here is worth surviving a
navigate-away, unlike `SettingsWindow` (see that module's docstring for
the contrast).

Four `tk.Entry` fields (columns, rows, start column, start row) re-validate
on every `<KeyRelease>` across all four -- start-column/row bounds depend
on the *currently entered* columns/rows, not the last-confirmed pair, so a
change to either re-checks all four (see the story's Design Notes). An
invalid field shows a per-field inline error
(`typography.body_secondary`/`colors.exit`, `DESIGN.md`'s inline-error
convention). Clicking "Generate" (a primary `PillButton`) while any field
is invalid leaves the dialog open with the error still visible and performs
no navigation/generation -- the same "no crash, no state change" gate
`ClassicMazeGallery._on_jump` already established, not a disabled-button
pattern (no `common/` widget supports one).

Each `Entry` binds local `<KeyPress-n>`/`<KeyPress-N>` returning `"break"`,
mirroring Story 2.1's review-fixed focus-collision guard on
`ClassicMazeGallery`'s own jump entry, so the global `generate_random`
shortcut can't refire while typing. `Cancel` (default `PillButton`) and
`<Escape>` both close the dialog with no side effect.

Field-to-field keyboard navigation (Up/Down, boundary-aware Left/Right,
Enter-advances-then-Generate) is delegated to the shared `FieldNavigator`
-- see that module's docstring for the full behavior; this dialog only
supplies the field order and the `Generate` button as the chain's final
stop.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from labyrinthes.adapters.tkinter.common.field_navigation import FieldNavigator
from labyrinthes.adapters.tkinter.common.pill_btn import PillButton
from labyrinthes.adapters.tkinter.common.tokens import SPACING, TYPOGRAPHY, Theme, colors_for
from labyrinthes.domain.maze_generation import validate_start_position
from labyrinthes.domain.maze_size_bounds import MazeSizeBounds, validate_dimensions
from labyrinthes.domain.position import Position

__all__ = ["GenerateRandomDialog"]

_FIELD_ORDER = ("columns", "rows", "start_col", "start_row")
_FIELD_LABELS = {
    "columns": "Columns",
    "rows": "Rows",
    "start_col": "Start column",
    "start_row": "Start row",
}
_NOT_A_NUMBER_MESSAGE = "Enter a whole number."

OnConfirmFn = Callable[[int, int, Position], None]


class GenerateRandomDialog(tk.Toplevel):
    """Configure and confirm a random maze's columns/rows/starting position."""

    def __init__(
        self,
        parent: tk.Widget,
        *,
        theme: Theme,
        bounds: MazeSizeBounds,
        on_confirm: OnConfirmFn,
    ) -> None:
        super().__init__(parent)
        self.title("Generate random maze")
        self._theme = theme
        self._bounds = bounds
        self._on_confirm = on_confirm

        colors = colors_for(theme)
        self.configure(background=colors.window)

        self._entries: dict[str, tk.Entry] = {}
        self._error_labels: dict[str, tk.Label] = {}

        form = tk.Frame(self, background=colors.window)
        form.pack(padx=SPACING["2xl"], pady=SPACING["2xl"], fill="both", expand=True)

        self._add_field(form, "columns", str(bounds.min_columns))
        self._add_field(form, "rows", str(bounds.min_rows))
        self._add_field(form, "start_col", "0")
        self._add_field(form, "start_row", "0")
        self._entries["columns"].focus_set()

        buttons = tk.Frame(self, background=colors.window)
        buttons.pack(padx=SPACING["2xl"], pady=(0, SPACING["2xl"]), anchor="e")

        self._cancel_button = PillButton(buttons, "Cancel", theme=theme, command=self._on_cancel)
        self._cancel_button.pack(side="left", padx=(0, SPACING["sm"]))

        self._generate_button = PillButton(
            buttons, "Generate", theme=theme, primary=True, command=self._on_generate_clicked
        )
        self._generate_button.pack(side="left")

        self._navigator = FieldNavigator(
            [self._entries[key] for key in _FIELD_ORDER], self._generate_button
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
            width=12,
            anchor="w",
        ).pack(side="left")

        entry = tk.Entry(row, width=8)
        entry.insert(0, initial_text)
        entry.pack(side="left")
        entry.bind("<KeyRelease>", self._on_field_changed)
        # Consume "n"/"N" locally before they reach the global
        # `generate_random` shortcut's `bind_all()` handler -- mirrors
        # `ClassicMazeGallery._jump_entry`'s identical fix (Story 2.1).
        entry.bind("<KeyPress-n>", lambda _event: "break")
        entry.bind("<KeyPress-N>", lambda _event: "break")
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

        Each of the four checks below only requires *its own* field(s) to
        have parsed -- a parse error in one field (e.g. non-numeric "rows")
        must never mask an out-of-bounds error already knowable in another
        (e.g. "columns" already out of bounds), which independently
        checking only after *both* had parsed would have hidden until the
        parse error was fixed first (found in review).
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

        # Start-position bounds are only meaningful against a real grid
        # shape, so both dimensions must parse to positive ints first --
        # but start_col/start_row are still checked independently of each
        # other beyond that, for the same masking reason as above.
        columns = parsed.get("columns")
        rows = parsed.get("rows")
        if columns is not None and rows is not None and columns > 0 and rows > 0:
            if "start_col" in parsed:
                position = Position(row=parsed.get("start_row", 0), col=parsed["start_col"])
                for message in validate_start_position(columns, rows, position):
                    if message.startswith("Start column"):
                        errors["start_col"] = message
            if "start_row" in parsed:
                position = Position(row=parsed["start_row"], col=parsed.get("start_col", 0))
                for message in validate_start_position(columns, rows, position):
                    if message.startswith("Start row"):
                        errors["start_row"] = message

        return errors

    def _validate(self) -> dict[str, str]:
        errors = self._compute_errors()
        for key, label in self._error_labels.items():
            label.configure(text=errors.get(key, ""))
        return errors

    def _on_field_changed(self, _event: tk.Event | None = None) -> None:
        self._validate()

    # -- actions ---------------------------------------------------

    def _on_generate_clicked(self, _event: tk.Event | None = None) -> None:
        errors = self._validate()
        if errors:
            # Leave the dialog open with the inline error(s) visible --
            # no navigation, no generation, no state change.
            return
        parsed, _parse_errors = self._parsed_fields()
        position = Position(row=parsed["start_row"], col=parsed["start_col"])
        self._on_confirm(parsed["columns"], parsed["rows"], position)
        self.destroy()

    def _on_cancel(self, _event: tk.Event | None = None) -> None:
        self.destroy()
