from labyrinthes.adapters.tkinter.common.breadcrumb import Breadcrumb, BreadcrumbSegment
from labyrinthes.adapters.tkinter.common.tokens import Theme, colors_for


def test_renders_one_label_per_segment_in_order(tk_root):
    segments = [
        BreadcrumbSegment("Home", on_click=lambda: None),
        BreadcrumbSegment("Builder"),
    ]
    breadcrumb = Breadcrumb(tk_root, segments, theme=Theme.LIGHT)

    assert [label.cget("text") for label in breadcrumb._labels] == ["Home", "Builder"]


def test_clickable_segment_rests_in_ink_soft_with_hand_cursor(tk_root):
    # `.crumb .seg` rests in `ink-soft`; `accent` is a hover-only color per
    # the locked mockups (`.crumb .seg:hover`), never the resting state.
    colors = colors_for(Theme.LIGHT)
    segments = [BreadcrumbSegment("Home", on_click=lambda: None)]
    breadcrumb = Breadcrumb(tk_root, segments, theme=Theme.LIGHT)

    label = breadcrumb._labels[0]
    assert label.cget("foreground") == colors.ink_soft
    assert label.cget("cursor") == "hand2"


def test_clickable_segment_turns_accent_on_hover_and_back_on_leave(tk_root):
    colors = colors_for(Theme.LIGHT)
    segments = [BreadcrumbSegment("Home", on_click=lambda: None)]
    breadcrumb = Breadcrumb(tk_root, segments, theme=Theme.LIGHT)
    label = breadcrumb._labels[0]

    # `tk_root` is withdrawn, so a real pointer-enter/leave can't be
    # synthesized reliably; invoke the bound handlers directly (see
    # test_icon_btn.py/test_tooltip.py's identical convention).
    on_enter, on_leave = breadcrumb._hover_handlers[0]

    on_enter()
    assert label.cget("foreground") == colors.accent

    on_leave()
    assert label.cget("foreground") == colors.ink_soft


def test_trailing_current_segment_is_not_styled_as_clickable(tk_root):
    colors = colors_for(Theme.LIGHT)
    segments = [
        BreadcrumbSegment("Home", on_click=lambda: None),
        BreadcrumbSegment("Builder"),
    ]
    breadcrumb = Breadcrumb(tk_root, segments, theme=Theme.LIGHT)

    current_label = breadcrumb._labels[1]
    assert current_label.cget("foreground") == colors.ink
    assert current_label.cget("cursor") != "hand2"


def test_clickable_segment_handler_invokes_its_callback(tk_root):
    calls = []
    segments = [
        BreadcrumbSegment("Home", on_click=lambda: calls.append("home")),
        BreadcrumbSegment("Builder"),
    ]
    breadcrumb = Breadcrumb(tk_root, segments, theme=Theme.LIGHT)

    # `tk_root` is withdrawn, so real X11 button-press synthesis isn't
    # reliable; invoke the bound handler directly (see test_icon_btn.py).
    breadcrumb._segment_handlers[0]()

    assert calls == ["home"]


def test_trailing_current_segment_has_no_click_handler(tk_root):
    segments = [
        BreadcrumbSegment("Home", on_click=lambda: None),
        BreadcrumbSegment("Builder"),
    ]
    breadcrumb = Breadcrumb(tk_root, segments, theme=Theme.LIGHT)

    assert breadcrumb._segment_handlers[1] is None
