"""Shared logo loading utility (Story 4.9)."""

from __future__ import annotations

import tkinter as tk

from labyrinthes.adapters.tkinter.common.tokens import Theme
from labyrinthes.application.settings_repository import SettingsRepository


def load_logo_image(
    settings_repository: SettingsRepository
) -> tk.PhotoImage | None:
    """Load the configured logo image (24x24) for the given theme.

    Returns None if the image cannot be loaded (missing file, PIL unavailable,
    corrupt image, etc.) -- caller will render text-only top bar.
    """
    try:
        from PIL import Image, ImageTk

        from labyrinthes.application.logos import _logo_path
    except Exception:
        return None

    from labyrinthes.application.theme_logo_settings import read_theme_logo

    logo_key = read_theme_logo(settings_repository)
    try:
        path = _logo_path(logo_key)
        img = Image.open(path)
        img = img.resize((24, 24), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None