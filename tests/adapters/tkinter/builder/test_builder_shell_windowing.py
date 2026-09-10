"""Builder shell windowing: canvas fit-to-space + Ctrl+wheel/`+`/`-` zoom (Story 4.8)."""

from labyrinthes.adapters.tkinter.builder.edit_area import _BuilderEditArea, _wheel_zoom_delta
from labyrinthes.adapters.tkinter.common import Theme
from labyrinthes.adapters.tkinter.common.keybindings import keybinding
from labyrinthes.adapters.tkinter.common.tokens import SPACING
from tests.adapters.tkinter.builder._helpers import _sketch_maze


class _FakeConfigureEvent:
    """A minimal stand-in for a `<Configure>` event: `_on_canvas_configure`
    only reads `.width`/`.height` (mirrors `_helpers._FakeEvent`)."""

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height


class _FakeWheelEvent:
    """A minimal stand-in for `<Control-MouseWheel>`/`<Control-Button-4/5>`."""

    def __init__(self, *, num: int = 0, delta: int = 0) -> None:
        self.num = num
        self.delta = delta


def _area(tk_root, navigate_stub, fake_settings_repository, fake_maze_repository, maze=None):
    navigate, _ = navigate_stub
    return _BuilderEditArea(
        tk_root,
        maze if maze is not None else _sketch_maze(20, 20),
        Theme.LIGHT,
        navigate=navigate,
        settings_repository=fake_settings_repository,
        maze_repository=fake_maze_repository,
    )


def test_canvas_is_packed_to_fill_and_expand_its_available_space(
    tk_root, navigate_stub, fake_settings_repository, fake_maze_repository
):
    area = _area(tk_root, navigate_stub, fake_settings_repository, fake_maze_repository)

    info = area._canvas.pack_info()

    assert info["fill"] == "both"
    assert info["expand"] == 1


def test_maze_frame_is_packed_to_claim_space_without_stretching(
    tk_root, navigate_stub, fake_settings_repository, fake_maze_repository
):
    # Story 4.10 follow-up: `maze-frame` claims leftover space without
    # stretching to it (`expand=True`, no `fill`) so it stays snug around
    # the canvas and centers in `Stage.content`, instead of stretching to
    # fill the whole stage.
    area = _area(tk_root, navigate_stub, fake_settings_repository, fake_maze_repository)

    info = area._maze_frame.pack_info()

    assert info.get("fill", "none") == "none"
    assert info["expand"] == 1


def test_on_canvas_configure_fits_the_canvas_to_the_reported_available_space(
    tk_root, navigate_stub, fake_settings_repository, fake_maze_repository
):
    area = _area(tk_root, navigate_stub, fake_settings_repository, fake_maze_repository)
    assert area._canvas._cell_size == 24  # 20x20: min(480 // 20, 480 // 20) == 24

    # `_on_canvas_configure` (Story 4.10 follow-up) subtracts the HUD row's
    # own rendered height -- plus its bottom `pady` gap -- from the
    # reported `Stage.content` height before fitting, since the HUD sits
    # above the maze-frame in the same column. `update_idletasks()` first,
    # mirroring what `_on_canvas_configure` itself does, so `winfo_reqheight()`
    # here reads the same real (not the pre-layout stale `1`) value it does.
    area.update_idletasks()
    hud_height = area._hud_row.winfo_reqheight() + SPACING["lg"]
    available_height = 400 - hud_height

    area._on_canvas_configure(_FakeConfigureEvent(400, 400))

    expected = min(40, max(16, min(400 // 20, available_height // 20)))
    assert area._canvas._cell_size == expected


def test_configure_and_wheel_zoom_are_bound_on_the_canvas_itself(
    tk_root, navigate_stub, fake_settings_repository, fake_maze_repository
):
    # Regression: the earlier tests above call `_on_canvas_configure`/
    # `_on_wheel_zoom` directly, which would still pass even if the
    # `.bind(...)` calls wiring them to real events were deleted or bound
    # to the wrong widget. This asserts the bindings are actually
    # registered -- `<Configure>` on `self._stage.content` (Story 4.10
    # follow-up: the canvas no longer resizes with its parent, so its own
    # `<Configure>` would only ever reflect its own `.configure()` calls),
    # wheel zoom still on `_canvas` itself.
    area = _area(tk_root, navigate_stub, fake_settings_repository, fake_maze_repository)

    assert area._stage.content.bind("<Configure>") != ""
    assert area._canvas.bind("<Control-MouseWheel>") != ""
    assert area._canvas.bind("<Control-Button-4>") != ""
    assert area._canvas.bind("<Control-Button-5>") != ""


def test_zoom_in_and_zoom_out_change_the_canvas_cell_size(
    tk_root, navigate_stub, fake_settings_repository, fake_maze_repository
):
    area = _area(tk_root, navigate_stub, fake_settings_repository, fake_maze_repository)
    baseline = area._canvas._cell_size

    area._zoom_in()
    assert area._canvas._cell_size == baseline + 2

    area._zoom_out()
    area._zoom_out()
    assert area._canvas._cell_size == baseline - 2


def test_zoom_in_builder_and_zoom_out_builder_are_bound_globally(
    tk_root, navigate_stub, fake_settings_repository, fake_maze_repository
):
    _area(tk_root, navigate_stub, fake_settings_repository, fake_maze_repository)

    assert tk_root.bind_all(keybinding("zoom_in_builder").event) != ""
    assert tk_root.bind_all(keybinding("zoom_out_builder").event) != ""


def test_wheel_zoom_delta_reads_x11_button_events():
    assert _wheel_zoom_delta(_FakeWheelEvent(num=4)) == 2
    assert _wheel_zoom_delta(_FakeWheelEvent(num=5)) == -2


def test_wheel_zoom_delta_reads_windows_macos_delta_events():
    assert _wheel_zoom_delta(_FakeWheelEvent(delta=120)) == 2
    assert _wheel_zoom_delta(_FakeWheelEvent(delta=-120)) == -2


def test_wheel_zoom_delta_is_a_no_op_for_a_zero_delta():
    assert _wheel_zoom_delta(_FakeWheelEvent(delta=0)) == 0


def test_on_wheel_zoom_applies_the_delta_to_the_canvas(
    tk_root, navigate_stub, fake_settings_repository, fake_maze_repository
):
    area = _area(tk_root, navigate_stub, fake_settings_repository, fake_maze_repository)
    baseline = area._canvas._cell_size

    area._on_wheel_zoom(_FakeWheelEvent(num=4))

    assert area._canvas._cell_size == baseline + 2
