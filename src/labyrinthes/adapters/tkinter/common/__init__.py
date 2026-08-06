"""Shared design tokens and Tkinter widget primitives (Story 1.6), plus the
shared navigation contract, breadcrumb, top bar, and Settings dialog
(Story 1.8).

Imported by `home/`/`builder/`/`player/` -- never duplicated per screen.
Imports only stdlib/`tkinter`; never `adapters/storage/`, never one of the
three screen packages (AD-1, AD-9, enforced by
`tests/test_architecture_boundaries.py`).
"""

from labyrinthes.adapters.tkinter.common.breadcrumb import Breadcrumb, BreadcrumbSegment
from labyrinthes.adapters.tkinter.common.hud_chip import HudChip
from labyrinthes.adapters.tkinter.common.icon_btn import IconButton
from labyrinthes.adapters.tkinter.common.kbd_tag import KbdTag
from labyrinthes.adapters.tkinter.common.navigation import NavigateFn, ScreenId, ScreenMountFn
from labyrinthes.adapters.tkinter.common.pill_btn import PillButton
from labyrinthes.adapters.tkinter.common.settings_window import SettingsWindow
from labyrinthes.adapters.tkinter.common.tokens import (
    RADII,
    SPACING,
    TYPOGRAPHY,
    ColorTokens,
    FontSpec,
    Theme,
    TypographyTokens,
    colors_for,
)
from labyrinthes.adapters.tkinter.common.tool_btn import ToolButton, ToolButtonGroup
from labyrinthes.adapters.tkinter.common.tooltip import Tooltip
from labyrinthes.adapters.tkinter.common.top_bar import TopBar

__all__ = [
    "RADII",
    "SPACING",
    "TYPOGRAPHY",
    "Breadcrumb",
    "BreadcrumbSegment",
    "ColorTokens",
    "FontSpec",
    "HudChip",
    "IconButton",
    "KbdTag",
    "NavigateFn",
    "PillButton",
    "ScreenId",
    "ScreenMountFn",
    "SettingsWindow",
    "Theme",
    "ToolButton",
    "ToolButtonGroup",
    "Tooltip",
    "TopBar",
    "TypographyTokens",
    "colors_for",
]
