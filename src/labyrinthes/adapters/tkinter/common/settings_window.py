"""`SettingsWindow` -- the non-modal Settings dialog every screen's icon opens (Story 1.8).

Left-hand category navigation holding category content: "Appearance"
(placeholder) and "Confirmation" (Story 2.10's four per-action toggles).
Ball/Difficulty/Shortcuts don't exist as domain concepts yet (Epics 2/3,
Story 1.10) -- stubbing categories with nothing behind them would invite
dead UI, so only the category-nav *structure* is built now (see the spec's
Design Notes). Never calls `grab_set()`: the screen that opened this
window stays fully mounted and interactive behind it.

Lifecycle (Story 1.11): each screen's `open_settings()` constructs this as
`SettingsWindow(parent, theme=theme, settings_repository=...)` -- a real Tk
child `Toplevel` of the app's persistent container (the same `parent`
`Router` passes into every screen's `mount()`), not of the screen's own
`frame`. Earlier (Stories
1.8, 1.9, 1.10) it was parented to `frame` instead, so `Router.navigate()`
mounting the next screen and then calling `previous_frame.destroy()` would
cascade-destroy this window too, via Tk's ordinary parent-child `Toplevel`
semantics -- silently closing any open `SettingsWindow` as a side effect
of navigating away from the screen that opened it. That was deferred three
times as "nothing stateful to lose yet" (`deferred-work.md`'s Story 1.8
and 1.10 entries; Story 1.9 hit the identical mechanism but never got its
own ledger entry -- see the 1.10 entry's cross-reference), until the Epic
1 retrospective judged the deferral no longer safe once Epic 2 lands real
stateful gameplay UI. Story 1.11 fixes it: `parent` outlives every
`previous_frame.destroy()` call, so a `SettingsWindow` opened on any
screen now survives navigating away from it, staying open and interactive
over whichever screen is mounted next.

Residual gap, deliberately not fixed here: a `SettingsWindow` that
survives a theme toggle keeps rendering the `Theme` it was constructed
with -- nothing re-themes it in place, since it's no longer torn down and
rebuilt by the toggle's full re-navigate the way the screen underneath it
is. Not reachable in a way that matters yet ("Appearance" is still only
`_APPEARANCE_PLACEHOLDER`, so there's no themed control whose staleness
would be visible beyond the window's own background/text colors); revisit
once `SettingsWindow` has content worth keeping in sync live.

Story 2.10 gives this window its first real content and the port it
previously lacked. `__init__` now takes a required, keyword-only
`settings_repository: SettingsRepository`; the category nav becomes a real
focusable control (NFR6) -- `<Button-1>`/`<Return>`/`<Space>` select a
category, the active one renders in `colors.accent`, a focus ring follows
`<FocusIn>` (Story 1.10 tokens); and a new "Confirmation" category holds
four themed `tk.Checkbutton` rows, one per Player action, each initialized
from its `read_confirm_*` reader and persisted via its `write_confirm_*`
writer on toggle. Each reader is called at window-construction time, so a
window opened *after* a toggle reflects the stored value (AC-3's
persistence surface); the `JsonSettingsRepository` reads fresh from disk
on every call, and the gated Player actions read fresh at action time --
see the story's Design Notes on AC-3 being structural.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from labyrinthes.adapters.tkinter.common.tokens import (
    FOCUS_RING_THICKNESS,
    RESTING_RING_THICKNESS,
    SPACING,
    TYPOGRAPHY,
    Theme,
    colors_for,
)
from labyrinthes.application.builder_session import BuilderTool
from labyrinthes.application.confirmation_settings import (
    read_confirm_invalid_input,
    read_confirm_level_change,
    read_confirm_redefine_marker,
    read_confirm_restart,
    read_confirm_switch_maze,
    write_confirm_invalid_input,
    write_confirm_level_change,
    write_confirm_redefine_marker,
    write_confirm_restart,
    write_confirm_switch_maze,
)
from labyrinthes.application.defaults_settings import (
    read_builder_default_tool,
    read_new_maze_defaults,
    read_random_maze_defaults,
    write_builder_default_tool,
    write_new_maze_default_columns,
    write_new_maze_default_rows,
    write_random_maze_default_columns,
    write_random_maze_default_rows,
)
from labyrinthes.application.settings_repository import SettingsRepository
from labyrinthes.application.theme_logo_settings import read_theme_logo, write_theme_logo
from labyrinthes.application.window_settings import (
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    read_window_size,
    write_window_height,
    write_window_width,
)

__all__ = ["SettingsWindow"]

_CATEGORIES = ("Appearance", "Confirmation", "Defaults")
_APPEARANCE_PLACEHOLDER = "Appearance settings are coming soon."

# `(row text, reader, writer)` for the confirmation toggles -- one per
# gated action, in the order the specs' action lists name them. The first
# four are Player actions (Story 2.10); the last is a Builder action
# (Story 3.4).
_CONFIRMATION_TOGGLES = (
    (
        "Confirm before switching/restarting mazes",
        read_confirm_switch_maze,
        write_confirm_switch_maze,
    ),
    ("Confirm before restarting", read_confirm_restart, write_confirm_restart),
    ("Confirm before changing level", read_confirm_level_change, write_confirm_level_change),
    ("Alert me about invalid input", read_confirm_invalid_input, write_confirm_invalid_input),
    (
        "Confirm before redefining an entry/exit",
        read_confirm_redefine_marker,
        write_confirm_redefine_marker,
    ),
)


class SettingsWindow(tk.Toplevel):
    """A non-modal Settings dialog: left-hand category list, right-hand content pane."""

    def __init__(
        self,
        parent: tk.Widget,
        *,
        theme: Theme,
        settings_repository: SettingsRepository,
    ) -> None:
        super().__init__(parent)
        self.title("Settings")
        self._theme = theme
        self._settings_repository = settings_repository
        self._nav_focused: dict[str, bool] = {}
        self._default_dimension_errors: dict[tk.Entry, tk.Label] = {}
        colors = colors_for(theme)
        self.configure(background=colors.window)

        nav = tk.Frame(self, background=colors.panel)
        nav.pack(side="left", fill="y")
        self._category_labels: dict[str, tk.Label] = {}
        for category in _CATEGORIES:
            # `TYPOGRAPHY.label` (10px/700), not `.body` -- `DESIGN.md`'s
            # `settings-window` component spec calls for category-nav text
            # in the small nav-label token, the same one used for other
            # group-label elements in the design system.
            label = tk.Label(
                nav,
                text=category,
                font=TYPOGRAPHY.label.to_tk_font(),
                background=colors.panel,
                foreground=colors.ink,
                anchor="w",
                takefocus=True,
                highlightthickness=RESTING_RING_THICKNESS,
                cursor="hand2",
            )
            label.pack(fill="x", padx=SPACING["lg"], pady=SPACING["sm"])
            label.bind("<Button-1>", self._make_select_handler(category))
            label.bind("<Return>", self._make_select_handler(category))
            label.bind("<space>", self._make_select_handler(category))
            label.bind("<FocusIn>", self._make_focus_handler(category, True))
            label.bind("<FocusOut>", self._make_focus_handler(category, False))
            self._category_labels[category] = label

        self._content = tk.Frame(self, background=colors.window)
        self._content.pack(side="left", fill="both", expand=True)
        self._select_category(_CATEGORIES[0])

        # Story 4.8: centered, resizable, and its own F11 fullscreen --
        # scoped to this `Toplevel` alone, never the root (see
        # `_toggle_fullscreen`'s docstring).
        self._fullscreen = False
        self.bind("<F11>", self._toggle_fullscreen)
        self._center_on_screen()
        self.resizable(True, True)

    def _center_on_screen(self) -> None:
        """Center this window on the primary screen at its current natural size.

        This `Toplevel`'s own natural-post-mount-size centering (unlike
        `app/composition_root.py::build_app()`'s root-window centering,
        which Story 4.10's follow-up changed to a fixed, `shared`-scope-
        setting-driven size read once at startup instead -- see that
        module's docstring). Position only (`+x+y`, no `WxH`) -- an
        explicit size would pin this window at its first category's
        natural size and stop it auto-growing when a taller category is
        later selected.
        """
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = max(0, (self.winfo_screenwidth() - width) // 2)
        y = max(0, (self.winfo_screenheight() - height) // 2)
        self.geometry(f"+{x}+{y}")

    def _toggle_fullscreen(self, _event: tk.Event | None = None) -> str:
        """Toggle fullscreen for *this* window only (Story 4.8's Design Notes).

        `bind_all()`'s F11 toggle (bound once at the root, in
        `composition_root.py`) is interpreter-wide, so it would also fire
        while this `Toplevel` has focus. Binding locally here instead, and
        returning `"break"`, relies on Tk checking a focused widget's own
        toplevel bindtag before the shared `"all"` bindtag: the `"break"`
        return stops that scan right there, so the root's global toggle
        never also runs. Fullscreen state is tracked as a plain bool (no Tk
        getter exists for it), local to this window alone.
        """
        self._fullscreen = not self._fullscreen
        self.attributes("-fullscreen", self._fullscreen)
        return "break"

    def _make_select_handler(self, category: str):
        def _select(_event: tk.Event | None = None) -> None:
            self._select_category(category)

        return _select

    def _make_focus_handler(self, category: str, focused: bool):
        def _on_focus(_event: tk.Event | None = None) -> None:
            self._nav_focused[category] = focused
            self._apply_nav_style(category)

        return _on_focus

    def _apply_nav_style(self, category: str) -> None:
        label = self._category_labels[category]
        colors = colors_for(self._theme)
        active = category == self._active_category
        foreground = colors.accent if active else colors.ink
        if self._nav_focused.get(category, False):
            label.configure(
                foreground=foreground,
                highlightthickness=FOCUS_RING_THICKNESS,
                highlightbackground=colors.accent,
                highlightcolor=colors.accent,
            )
        else:
            label.configure(
                foreground=foreground,
                highlightthickness=RESTING_RING_THICKNESS,
                highlightbackground=colors.panel,
                highlightcolor=colors.panel,
            )

    def _select_category(self, name: str) -> None:
        self._active_category = name
        for category in _CATEGORIES:
            self._apply_nav_style(category)

        for child in self._content.winfo_children():
            child.destroy()
        self._confirmation_rows = {}
        if name == "Appearance":
            self._build_appearance(self._content)
        elif name == "Confirmation":
            self._build_confirmation(self._content)
        else:
            self._build_defaults(self._content)

    def _build_appearance(self, container: tk.Frame) -> None:
        self._build_logo_picker(container)

    def _build_logo_picker(self, container: tk.Frame) -> None:
        from labyrinthes.application.logos import logo_path

        colors = colors_for(self._theme)
        logo_frame = tk.Frame(container, background=colors.window)
        logo_frame.pack(fill="both", expand=True, padx=SPACING["2xl"], pady=SPACING["2xl"])

        try:
            from PIL import Image, ImageTk

            current_key = read_theme_logo(self._settings_repository)
            img = Image.open(logo_path(current_key))
            img = img.resize((128, 128), Image.Resampling.LANCZOS)
            self._logo_photo = ImageTk.PhotoImage(img)
            logo_label = tk.Label(
                logo_frame,
                image=self._logo_photo,
                background=colors.window,
            )
            logo_label.pack(anchor="w", pady=(0, SPACING["sm"]))
        except Exception:
            tk.Label(
                logo_frame,
                text="—",
                font=TYPOGRAPHY.body.to_tk_font(),
                background=colors.window,
                foreground=colors.ink_soft,
            ).pack(anchor="w")

        nav_frame = tk.Frame(logo_frame, background=colors.window)
        nav_frame.pack(anchor="w", pady=SPACING["xs"])

        current = read_theme_logo(self._settings_repository)

        prev_btn = tk.Button(
            nav_frame,
            text="◀",
            font=TYPOGRAPHY.body.to_tk_font(),
            background=colors.window,
            foreground=colors.ink,
            command=self._on_prev_logo,
            cursor="hand2",
        )
        prev_btn.pack(side="left", padx=(0, SPACING["sm"]))

        self._logo_key_label = tk.Label(
            nav_frame,
            text=current,
            font=TYPOGRAPHY.body.to_tk_font(),
            background=colors.window,
            foreground=colors.ink,
        )
        self._logo_key_label.pack(side="left", padx=SPACING["sm"], fill="x", expand=True)

        next_btn = tk.Button(
            nav_frame,
            text="▶",
            font=TYPOGRAPHY.body.to_tk_font(),
            background=colors.window,
            foreground=colors.ink,
            command=self._on_next_logo,
            cursor="hand2",
        )
        next_btn.pack(side="left", padx=(SPACING["sm"], 0))

    def _on_prev_logo(self) -> None:
        from labyrinthes.application.logos import _LOGO_OPTIONS, logo_path

        current = read_theme_logo(self._settings_repository)
        keys = [o[0] for o in _LOGO_OPTIONS]
        if current not in keys:
            current = keys[0]
        current_idx = keys.index(current)
        new_idx = (current_idx - 1) % len(keys)
        new_key = keys[new_idx]
        write_theme_logo(self._settings_repository, new_key)
        self._logo_key_label.configure(text=new_key)
        try:
            from PIL import Image, ImageTk

            img = Image.open(logo_path(new_key))
            img = img.resize((128, 128), Image.Resampling.LANCZOS)
            self._logo_photo = ImageTk.PhotoImage(img)
            logo_frame = self._logo_key_label.master
            for child in logo_frame.winfo_children():
                if isinstance(child, tk.Label) and child.cget("image") == str(self._logo_photo):
                    child.configure(image=self._logo_photo)
                    break
        except Exception:
            pass

    def _on_next_logo(self) -> None:
        from labyrinthes.application.logos import _LOGO_OPTIONS, logo_path

        current = read_theme_logo(self._settings_repository)
        keys = [o[0] for o in _LOGO_OPTIONS]
        if current not in keys:
            current = keys[0]
        current_idx = keys.index(current)
        new_idx = (current_idx + 1) % len(keys)
        new_key = keys[new_idx]
        write_theme_logo(self._settings_repository, new_key)
        self._logo_key_label.configure(text=new_key)
        try:
            from PIL import Image, ImageTk

            img = Image.open(logo_path(new_key))
            img = img.resize((128, 128), Image.Resampling.LANCZOS)
            self._logo_photo = ImageTk.PhotoImage(img)
            logo_frame = self._logo_key_label.master
            for child in logo_frame.winfo_children():
                if isinstance(child, tk.Label) and child.cget("image") == str(self._logo_photo):
                    child.configure(image=self._logo_photo)
                    break
        except Exception:
            pass

    def _build_confirmation(self, container: tk.Frame) -> None:
        colors = colors_for(self._theme)
        self._confirmation_rows: dict[str, tk.BooleanVar] = {}
        for text, reader, writer in _CONFIRMATION_TOGGLES:
            variable = tk.BooleanVar(value=reader(self._settings_repository))
            checkbutton = tk.Checkbutton(
                container,
                text=text,
                variable=variable,
                command=lambda v=variable, w=writer: w(self._settings_repository, v.get()),
                background=colors.window,
                foreground=colors.ink,
                activebackground=colors.window,
                activeforeground=colors.ink,
                selectcolor=colors.panel,
                font=TYPOGRAPHY.body.to_tk_font(),
            )
            checkbutton.pack(anchor="w", fill="x", padx=SPACING["2xl"], pady=SPACING["sm"])
            self._confirmation_rows[text] = variable

    def _build_defaults(self, container: tk.Frame) -> None:
        colors = colors_for(self._theme)

        # Default Builder tool dropdown
        tool_frame = tk.Frame(container, background=colors.window)
        tool_frame.pack(fill="x", padx=SPACING["2xl"], pady=SPACING["md"])

        tk.Label(
            tool_frame,
            text="Default Builder tool",
            font=TYPOGRAPHY.body.to_tk_font(),
            background=colors.window,
            foreground=colors.ink,
            anchor="w",
        ).pack(anchor="w", pady=(0, SPACING["xs"]))

        current_tool = read_builder_default_tool(self._settings_repository)
        tool_var = tk.StringVar(value=current_tool.value)
        tool_options = [t.value for t in BuilderTool]

        tool_menu = tk.OptionMenu(tool_frame, tool_var, *tool_options)
        tool_menu.configure(
            background=colors.window,
            foreground=colors.ink,
            activebackground=colors.window,
            activeforeground=colors.ink,
            font=TYPOGRAPHY.body.to_tk_font(),
            cursor="hand2",
        )
        tool_menu.pack(fill="x")

        def on_tool_change(*_args: str) -> None:
            write_builder_default_tool(self._settings_repository, BuilderTool(tool_var.get()))

        tool_var.trace_add("write", on_tool_change)

        # Dimension fields - New Maze defaults
        new_maze_frame = tk.Frame(container, background=colors.window)
        new_maze_frame.pack(fill="x", padx=SPACING["2xl"], pady=(SPACING["lg"], SPACING["md"]))

        tk.Label(
            new_maze_frame,
            text="New Maze defaults",
            font=TYPOGRAPHY.body.to_tk_font(),
            background=colors.window,
            foreground=colors.ink,
            anchor="w",
        ).pack(anchor="w", pady=(0, SPACING["xs"]))

        new_maze_cols, new_maze_rows = read_new_maze_defaults(self._settings_repository)
        self._add_default_dimension_field(
            new_maze_frame,
            "Columns",
            str(new_maze_cols),
            lambda v: write_new_maze_default_columns(self._settings_repository, v),
        )
        self._add_default_dimension_field(
            new_maze_frame,
            "Rows",
            str(new_maze_rows),
            lambda v: write_new_maze_default_rows(self._settings_repository, v),
        )

        # Dimension fields - Random Maze defaults
        random_maze_frame = tk.Frame(container, background=colors.window)
        random_maze_frame.pack(fill="x", padx=SPACING["2xl"], pady=(SPACING["lg"], SPACING["md"]))

        tk.Label(
            random_maze_frame,
            text="Random Maze defaults",
            font=TYPOGRAPHY.body.to_tk_font(),
            background=colors.window,
            foreground=colors.ink,
            anchor="w",
        ).pack(anchor="w", pady=(0, SPACING["xs"]))

        random_maze_cols, random_maze_rows = read_random_maze_defaults(self._settings_repository)
        self._add_default_dimension_field(
            random_maze_frame,
            "Columns",
            str(random_maze_cols),
            lambda v: write_random_maze_default_columns(self._settings_repository, v),
        )
        self._add_default_dimension_field(
            random_maze_frame,
            "Rows",
            str(random_maze_rows),
            lambda v: write_random_maze_default_rows(self._settings_repository, v),
        )

        # Window size (Story 4.10 follow-up) -- applies on next launch, not
        # live, same precedent as Story 4.9's logo-change timing.
        window_frame = tk.Frame(container, background=colors.window)
        window_frame.pack(fill="x", padx=SPACING["2xl"], pady=(SPACING["lg"], SPACING["md"]))

        tk.Label(
            window_frame,
            text="Window size (applies on next launch)",
            font=TYPOGRAPHY.body.to_tk_font(),
            background=colors.window,
            foreground=colors.ink,
            anchor="w",
        ).pack(anchor="w", pady=(0, SPACING["xs"]))

        # Captured once here, not re-queried inside the writer lambdas below:
        # if the window moved to a different-resolution monitor between
        # opening Settings and editing the field, a fresh
        # `winfo_screenwidth()`/`winfo_screenheight()` read at write time
        # could disagree with the `max_value` bound the field was just
        # validated against, so the inline "Clamped to X" note and the
        # actually-persisted value could diverge.
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width, window_height = read_window_size(
            self._settings_repository, screen_width, screen_height
        )
        self._add_default_dimension_field(
            window_frame,
            "Width",
            str(window_width),
            lambda v: write_window_width(self._settings_repository, v, screen_width),
            min_value=MIN_WINDOW_WIDTH,
            max_value=screen_width,
            clamp=True,
        )
        self._add_default_dimension_field(
            window_frame,
            "Height",
            str(window_height),
            lambda v: write_window_height(self._settings_repository, v, screen_height),
            min_value=MIN_WINDOW_HEIGHT,
            max_value=screen_height,
            clamp=True,
        )

    def _add_default_dimension_field(
        self,
        parent: tk.Frame,
        label: str,
        initial_value: str,
        writer: Callable,
        *,
        min_value: int = 1,
        max_value: int | None = None,
        clamp: bool = False,
    ) -> None:
        """A `label` + `tk.Entry` + inline-error-label row, validated live.

        `min_value`/`max_value` bound the field (`max_value=None` falls back
        to the maze-size bound below, the original New Maze/Random Maze
        columns/rows behavior). `clamp=False` (the default, matching that
        original behavior) rejects an out-of-bounds entry -- an inline error
        shows and `writer` is never called, so the previously stored value
        is left untouched. `clamp=True` (the Window size fields, Story 4.10
        follow-up) instead *clamps* an out-of-bounds entry into range,
        writes the clamped value, and shows an informational inline note --
        matching the setting's own `write_window_width`/`write_window_height`
        clamping contract (a value is always persisted, never just refused).
        """
        colors = colors_for(self._theme)

        row = tk.Frame(parent, background=colors.window)
        row.pack(fill="x", pady=(0, SPACING["xs"]))

        tk.Label(
            row,
            text=label,
            font=TYPOGRAPHY.body.to_tk_font(),
            background=colors.window,
            foreground=colors.ink,
            width=8,
            anchor="w",
        ).pack(side="left")

        entry = tk.Entry(row, width=6)
        entry.insert(0, initial_value)
        entry.pack(side="left")
        entry.bind(
            "<KeyRelease>",
            lambda _e: self._validate_default_dimension(
                entry, writer, min_value=min_value, max_value=max_value, clamp=clamp
            ),
        )

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

        self._default_dimension_errors[entry] = error_label

    def _validate_default_dimension(
        self,
        entry: tk.Entry,
        writer: Callable,
        *,
        min_value: int = 1,
        max_value: int | None = None,
        clamp: bool = False,
    ) -> None:
        from labyrinthes.domain.maze_size_bounds import DEFAULT_MAZE_SIZE_BOUNDS

        text = entry.get()
        error_label = self._default_dimension_errors.get(entry)
        if error_label is None:
            return
        colors = colors_for(self._theme)

        bound = max_value
        if bound is None:
            # We don't know if this is columns or rows here, but the
            # writers clamp on read too. For UX, check against the max
            # bounds (the original New Maze/Random Maze fields' own
            # behavior, unaffected by `clamp`/explicit bounds).
            bound = max(DEFAULT_MAZE_SIZE_BOUNDS.max_columns, DEFAULT_MAZE_SIZE_BOUNDS.max_rows)

        try:
            value = int(text)
        except ValueError:
            error_label.configure(text="Enter a whole number.", foreground=colors.exit)
            return

        if value < min_value or value > bound:
            if clamp:
                # The value *was* accepted and persisted (clamped), not
                # rejected -- `colors.ink_soft`, not the error red, so this
                # doesn't read as "something went wrong" the way "Enter a
                # whole number."/"Maximum is N." do below. The entry's own
                # displayed text is also rewritten to the clamped value, so
                # the field never visibly disagrees with what was actually
                # persisted (e.g. a stray "99999" left showing above a
                # "Clamped to 1920." note) until Settings is closed and
                # reopened.
                clamped = max(min_value, min(value, bound))
                entry.delete(0, "end")
                entry.insert(0, str(clamped))
                error_label.configure(text=f"Clamped to {clamped}.", foreground=colors.ink_soft)
                writer(clamped)
                return
            if value < min_value:
                message = (
                    "Must be a positive number." if min_value <= 1 else f"Minimum is {min_value}."
                )
            else:
                message = f"Maximum is {bound}."
            error_label.configure(text=message, foreground=colors.exit)
            return

        error_label.configure(text="")
        writer(value)
