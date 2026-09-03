"""GameplayScreen shell windowing: canvas fit-to-space + Ctrl+wheel/`+`/`-`
zoom (Story 4.8)."""

from labyrinthes.adapters.tkinter.common.keybindings import keybinding
from labyrinthes.adapters.tkinter.common.tokens import SPACING, Theme
from labyrinthes.adapters.tkinter.player.gameplay import GameplayScreen
from labyrinthes.adapters.tkinter.player.gameplay.screen import _wheel_zoom_delta
from tests.adapters.tkinter.player.gameplay._helpers import _classic_maze


class _FakeConfigureEvent:
    """A minimal stand-in for a `<Configure>` event: `_on_canvas_configure`
    only reads `.width`/`.height`."""

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height


class _FakeWheelEvent:
    """A minimal stand-in for `<Control-MouseWheel>`/`<Control-Button-4/5>`."""

    def __init__(self, *, num: int = 0, delta: int = 0) -> None:
        self.num = num
        self.delta = delta


def _screen(tk_root, fake_maze_repository, fake_settings_repository, maze=None):
    return GameplayScreen(
        tk_root,
        maze if maze is not None else _classic_maze(width=20, height=20),
        Theme.LIGHT,
        maze_repository=fake_maze_repository,
        settings_repository=fake_settings_repository,
    )


def test_maze_frame_is_packed_to_claim_space_without_stretching_canvas_fills_it(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = _screen(tk_root, fake_maze_repository, fake_settings_repository)

    frame_info = screen._maze_frame.pack_info()
    canvas_info = screen._maze_canvas.pack_info()

    # Story 4.10 follow-up: `maze-frame` claims leftover space without
    # stretching to it (`expand=True`, no `fill`) so it stays snug around
    # the canvas and centers in `Stage.content` -- the canvas itself still
    # fills/expands within that now-snug frame.
    assert frame_info.get("fill", "none") == "none"
    assert frame_info["expand"] == 1
    assert canvas_info["fill"] == "both"
    assert canvas_info["expand"] == 1


def test_on_canvas_configure_fits_the_canvas_to_the_reported_available_space(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = _screen(tk_root, fake_maze_repository, fake_settings_repository)
    assert screen._maze_canvas._cell_size == 24  # 20x20: min(480 // 20, 480 // 20) == 24

    # `_on_canvas_configure` (Story 4.10 follow-up) subtracts the HUD row's
    # own rendered height -- plus its bottom `pady` gap -- from the
    # reported `Stage.content` height before fitting, since the HUD sits
    # above the maze-frame in the same column. `update_idletasks()` first,
    # mirroring what `_on_canvas_configure` itself does, so `winfo_reqheight()`
    # here reads the same real (not the pre-layout stale `1`) value it does.
    screen.update_idletasks()
    hud_height = screen._hud.winfo_reqheight() + SPACING["lg"]
    available_height = 400 - hud_height

    screen._on_canvas_configure(_FakeConfigureEvent(400, 400))

    expected = min(40, max(16, min(400 // 20, available_height // 20)))
    assert screen._maze_canvas._cell_size == expected


def test_configure_and_wheel_zoom_are_bound_on_the_canvas_itself(
    tk_root, fake_maze_repository, fake_settings_repository
):
    # Regression: the earlier tests above call `_on_canvas_configure`/
    # `_on_wheel_zoom` directly, which would still pass even if the
    # `.bind(...)` calls wiring them to real events were deleted or bound
    # to the wrong widget. This asserts the bindings are actually
    # registered -- `<Configure>` on `self._stage.content` (Story 4.10
    # follow-up: the canvas no longer resizes with its parent, so its own
    # `<Configure>` would only ever reflect its own `.configure()` calls),
    # wheel zoom still on `_maze_canvas` itself.
    screen = _screen(tk_root, fake_maze_repository, fake_settings_repository)

    assert screen._stage.content.bind("<Configure>") != ""
    assert screen._maze_canvas.bind("<Control-MouseWheel>") != ""
    assert screen._maze_canvas.bind("<Control-Button-4>") != ""
    assert screen._maze_canvas.bind("<Control-Button-5>") != ""


def test_zoom_in_and_zoom_out_change_the_canvas_cell_size(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = _screen(tk_root, fake_maze_repository, fake_settings_repository)
    baseline = screen._maze_canvas._cell_size

    screen._zoom_in()
    assert screen._maze_canvas._cell_size == baseline + 2

    screen._zoom_out()
    screen._zoom_out()
    assert screen._maze_canvas._cell_size == baseline - 2


def test_zoom_in_player_and_zoom_out_player_are_bound_globally(
    tk_root, fake_maze_repository, fake_settings_repository
):
    _screen(tk_root, fake_maze_repository, fake_settings_repository)

    assert tk_root.bind_all(keybinding("zoom_in_player").event) != ""
    assert tk_root.bind_all(keybinding("zoom_out_player").event) != ""


def test_wheel_zoom_delta_reads_x11_button_events():
    assert _wheel_zoom_delta(_FakeWheelEvent(num=4)) == 2
    assert _wheel_zoom_delta(_FakeWheelEvent(num=5)) == -2


def test_wheel_zoom_delta_reads_windows_macos_delta_events():
    assert _wheel_zoom_delta(_FakeWheelEvent(delta=120)) == 2
    assert _wheel_zoom_delta(_FakeWheelEvent(delta=-120)) == -2


def test_wheel_zoom_delta_is_a_no_op_for_a_zero_delta():
    assert _wheel_zoom_delta(_FakeWheelEvent(delta=0)) == 0


def test_on_wheel_zoom_applies_the_delta_to_the_canvas(
    tk_root, fake_maze_repository, fake_settings_repository
):
    screen = _screen(tk_root, fake_maze_repository, fake_settings_repository)
    baseline = screen._maze_canvas._cell_size

    screen._on_wheel_zoom(_FakeWheelEvent(num=4))

    assert screen._maze_canvas._cell_size == baseline + 2
