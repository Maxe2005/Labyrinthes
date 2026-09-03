"""`_LeftPanel`/`_RightPanel` -- the Mode/Levels/Difficulty/Edit-in-Builder
and Movement button columns (Story 4.10, split from the former single
`_Sidebar` so each half can flank the centered `Stage` independently).

Every button's command is a callback supplied by `GameplayScreen`
(`screen.py`), which owns the session and decides what each click actually
does (including the `_toplevel_has_focus()` guard); these widgets only
build the buttons and expose small `set_*`/`sync_*` setters the screen
calls after a session change. Neither holds session state of its own.

`_LeftPanel` always builds the "Mode"/"Levels"/"Difficulty" groups; the
Difficulty pair is disabled (not hidden) via `set_difficulty(...,
enabled=False)` whenever the level is ONE or MAX (Story 2.7). Its "Edit in
Builder" button is only built at all when `show_edit_in_builder` is `True`
(eligible only for a `CLASSIC`/`SAVED_RANDOM` maze, decided by the caller).

`_RightPanel` builds the "Movement" group and exposes an empty `save_zone`
frame the screen builds/rebuilds the conditional Save `PillButton`
(GENERATED mazes only) into via `GameplayScreen._build_save_zone()`.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from labyrinthes.adapters.tkinter.common import (
    SPACING,
    TYPOGRAPHY,
    Theme,
    ToolButton,
    build_group_heading,
    keybinding,
)
from labyrinthes.adapters.tkinter.common.tokens import colors_for

__all__ = ["_LeftPanel", "_RightPanel"]


class _LeftPanel(tk.Frame):
    """The Mode(HARD)/Levels/Difficulty/Edit-in-Builder button column."""

    def __init__(
        self,
        parent: tk.Widget,
        *,
        theme: Theme,
        hard_active: bool,
        level_label: str,
        difficulty_label: str,
        difficulty_enabled: bool,
        show_edit_in_builder: bool,
        on_toggle_hard_mode: Callable[[], None],
        on_level_minus: Callable[[], None],
        on_level_plus: Callable[[], None],
        on_difficulty_minus: Callable[[], None],
        on_difficulty_plus: Callable[[], None],
        on_edit_in_builder: Callable[[], None] | None = None,
    ) -> None:
        self._theme = theme
        colors = colors_for(theme)
        super().__init__(parent, background=colors.window)

        build_group_heading(self, "Mode", colors).pack(anchor="w", pady=(0, SPACING["sm"]))

        hard_kb = keybinding("toggle_hard_mode")
        self._mode_hard_button = ToolButton(
            self,
            "HARD",
            theme=theme,
            shortcut=hard_kb.display,
            command=on_toggle_hard_mode,
        )
        self._mode_hard_button.pack(anchor="w")
        self._mode_hard_button.set_active(hard_active)

        build_group_heading(self, "Levels", colors).pack(
            anchor="w", pady=(SPACING["lg"], SPACING["sm"])
        )

        level_row = tk.Frame(self, background=colors.window)
        level_row.pack(anchor="w")

        self._level_minus_button = ToolButton(level_row, "−", theme=theme, command=on_level_minus)
        self._level_minus_button.pack(side="left", padx=(0, SPACING["sm"]))

        self._level_value_label = tk.Label(
            level_row,
            text=level_label,
            font=TYPOGRAPHY.hud_stat.to_tk_font(),
            background=colors.window,
            foreground=colors.ink,
        )
        self._level_value_label.pack(side="left", padx=(0, SPACING["sm"]))

        self._level_plus_button = ToolButton(level_row, "+", theme=theme, command=on_level_plus)
        self._level_plus_button.pack(side="left")

        build_group_heading(self, "Difficulty", colors).pack(
            anchor="w", pady=(SPACING["lg"], SPACING["sm"])
        )

        difficulty_row = tk.Frame(self, background=colors.window)
        difficulty_row.pack(anchor="w")

        self._difficulty_minus_button = ToolButton(
            difficulty_row, "−", theme=theme, command=on_difficulty_minus
        )
        self._difficulty_minus_button.pack(side="left", padx=(0, SPACING["sm"]))

        self._difficulty_value_label = tk.Label(
            difficulty_row,
            text=difficulty_label,
            font=TYPOGRAPHY.hud_stat.to_tk_font(),
            background=colors.window,
            foreground=colors.ink,
        )
        self._difficulty_value_label.pack(side="left", padx=(0, SPACING["sm"]))

        self._difficulty_plus_button = ToolButton(
            difficulty_row, "+", theme=theme, command=on_difficulty_plus
        )
        self._difficulty_plus_button.pack(side="left")

        if show_edit_in_builder:
            assert on_edit_in_builder is not None
            edit_kb = keybinding("edit_in_builder")
            self._edit_in_builder_button = ToolButton(
                self,
                "Edit in Builder",
                theme=theme,
                shortcut=edit_kb.display,
                command=on_edit_in_builder,
            )
            self._edit_in_builder_button.pack(anchor="w", pady=(SPACING["lg"], SPACING["sm"]))

        self.set_difficulty(difficulty_label, enabled=difficulty_enabled)

    # -- sync setters, called by `screen.py` after a session change --------

    def sync_hard_button(self, active: bool) -> None:
        self._mode_hard_button.set_active(active)

    def set_level(self, label: str) -> None:
        self._level_value_label.configure(text=label)

    def set_difficulty(self, label: str, *, enabled: bool) -> None:
        self._difficulty_minus_button.set_enabled(enabled)
        self._difficulty_plus_button.set_enabled(enabled)
        colors = colors_for(self._theme)
        self._difficulty_value_label.configure(
            text=label,
            foreground=colors.ink if enabled else colors.ghost,
        )


class _RightPanel(tk.Frame):
    """The Movement button group, plus the conditional Save button's zone."""

    def __init__(
        self,
        parent: tk.Widget,
        *,
        theme: Theme,
        mode_active: bool,
        speed_label: str,
        on_toggle_mode: Callable[[], None],
        on_cycle_speed: Callable[[], None],
    ) -> None:
        self._theme = theme
        colors = colors_for(theme)
        super().__init__(parent, background=colors.window)

        build_group_heading(self, "Movement", colors).pack(anchor="w", pady=(0, SPACING["sm"]))

        mode_kb = keybinding("toggle_movement_mode")
        self._mode_button = ToolButton(
            self,
            "Smooth",
            theme=theme,
            shortcut=mode_kb.display,
            command=on_toggle_mode,
        )
        self._mode_button.pack(anchor="w", pady=(0, SPACING["sm"]))
        self._mode_button.set_active(mode_active)

        self._speed_button = ToolButton(
            self,
            speed_label,
            theme=theme,
            command=on_cycle_speed,
        )
        self._speed_button.pack(anchor="w")

        # Built/rebuilt by `GameplayScreen._build_save_zone()` -- empty for
        # a maze that isn't `GENERATED` (see `save_zone`).
        self._save_zone = tk.Frame(self, background=colors.window)
        self._save_zone.pack(anchor="w", pady=(SPACING["lg"], 0))

    @property
    def save_zone(self) -> tk.Widget:
        """The frame `GameplayScreen` builds the conditional Save button into."""
        return self._save_zone

    # -- sync setters, called by `screen.py` after a session change --------

    def sync_mode_button(self, active: bool) -> None:
        self._mode_button.set_active(active)

    def set_speed_label(self, label: str) -> None:
        self._speed_button.set_text(label)
