from labyrinthes.adapters.tkinter.common.breadcrumb import Breadcrumb, BreadcrumbSegment
from labyrinthes.adapters.tkinter.common.tokens import (
    FOCUS_RING_THICKNESS,
    RESTING_RING_THICKNESS,
    Theme,
    colors_for,
)


def test_renders_one_label_per_segment_in_order(tk_root):
    segments = [
        BreadcrumbSegment("Home", on_click=lambda: None),
        BreadcrumbSegment("Builder"),
    ]
    breadcrumb = Breadcrumb(tk_root, segments, theme=Theme.LIGHT)

    assert [label.cget("text") for label in breadcrumb._labels] == ["Home", "Builder"]


def test_set_label_updates_the_segments_text_in_place(tk_root):
    segments = [
        BreadcrumbSegment("Home", on_click=lambda: None),
        BreadcrumbSegment("Player", on_click=lambda: None),
        BreadcrumbSegment("Random Maze"),
    ]
    breadcrumb = Breadcrumb(tk_root, segments, theme=Theme.LIGHT)

    breadcrumb.set_label(2, "Saved Random Maze")

    assert [label.cget("text") for label in breadcrumb._labels] == [
        "Home",
        "Player",
        "Saved Random Maze",
    ]


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


def test_clickable_segment_is_keyboard_focusable_with_return_and_space_bound(tk_root):
    segments = [BreadcrumbSegment("Home", on_click=lambda: None)]
    breadcrumb = Breadcrumb(tk_root, segments, theme=Theme.LIGHT)
    label = breadcrumb._labels[0]

    assert label.cget("takefocus")
    assert label.bind("<Return>") != ""
    assert label.bind("<space>") != ""


def test_trailing_current_segment_is_not_keyboard_focusable(tk_root):
    segments = [
        BreadcrumbSegment("Home", on_click=lambda: None),
        BreadcrumbSegment("Builder"),
    ]
    breadcrumb = Breadcrumb(tk_root, segments, theme=Theme.LIGHT)

    assert breadcrumb._focus_handlers[1] is None


def test_clickable_segment_rests_with_a_ring_matching_the_breadcrumb_background(tk_root):
    colors = colors_for(Theme.LIGHT)
    segments = [BreadcrumbSegment("Home", on_click=lambda: None)]
    breadcrumb = Breadcrumb(tk_root, segments, theme=Theme.LIGHT)
    label = breadcrumb._labels[0]

    assert label.cget("highlightthickness") == RESTING_RING_THICKNESS
    assert label.cget("highlightbackground") == colors.window
    assert label.cget("highlightcolor") == colors.window


def test_clickable_segment_focus_in_shows_an_accent_ring_and_recolors_like_hover(tk_root):
    colors = colors_for(Theme.LIGHT)
    segments = [BreadcrumbSegment("Home", on_click=lambda: None)]
    breadcrumb = Breadcrumb(tk_root, segments, theme=Theme.LIGHT)
    label = breadcrumb._labels[0]

    # `tk_root` is withdrawn, so real Tab traversal isn't reliably
    # synthesizable; invoke the bound handler directly (see this module's
    # existing hover-transition tests).
    on_focus_in, _on_focus_out = breadcrumb._focus_handlers[0]
    on_focus_in()

    assert label.cget("highlightthickness") == FOCUS_RING_THICKNESS
    assert label.cget("highlightbackground") == colors.accent
    assert label.cget("highlightcolor") == colors.accent
    assert label.cget("foreground") == colors.accent


def test_clickable_segment_focus_out_reverts_ring_and_recolors_back_to_resting(tk_root):
    colors = colors_for(Theme.LIGHT)
    segments = [BreadcrumbSegment("Home", on_click=lambda: None)]
    breadcrumb = Breadcrumb(tk_root, segments, theme=Theme.LIGHT)
    label = breadcrumb._labels[0]

    on_focus_in, on_focus_out = breadcrumb._focus_handlers[0]
    on_focus_in()
    on_focus_out()

    assert label.cget("highlightthickness") == RESTING_RING_THICKNESS
    assert label.cget("highlightbackground") == colors.window
    assert label.cget("highlightcolor") == colors.window
    assert label.cget("foreground") == colors.ink_soft


def test_mouse_leaving_a_focused_segment_keeps_the_focus_color_and_ring(tk_root):
    # Regression: hovering, then tabbing to the same segment, then moving
    # the mouse off must not revert to resting style while keyboard focus
    # is still present -- hover and focus each independently drive the
    # same recolor, and losing one must not clobber the other.
    colors = colors_for(Theme.LIGHT)
    segments = [BreadcrumbSegment("Home", on_click=lambda: None)]
    breadcrumb = Breadcrumb(tk_root, segments, theme=Theme.LIGHT)
    label = breadcrumb._labels[0]
    on_enter, on_leave = breadcrumb._hover_handlers[0]
    on_focus_in, _on_focus_out = breadcrumb._focus_handlers[0]

    on_enter()
    on_focus_in()
    on_leave()

    assert label.cget("foreground") == colors.accent
    assert label.cget("highlightthickness") == FOCUS_RING_THICKNESS
    assert label.cget("highlightbackground") == colors.accent


def test_losing_focus_while_still_hovered_keeps_the_hover_color_but_drops_the_ring(tk_root):
    # Regression: focusing, then losing focus while the mouse is still
    # hovering, must keep the hover text color (not revert to resting)
    # even though the ring itself is focus-only and does go away.
    colors = colors_for(Theme.LIGHT)
    segments = [BreadcrumbSegment("Home", on_click=lambda: None)]
    breadcrumb = Breadcrumb(tk_root, segments, theme=Theme.LIGHT)
    label = breadcrumb._labels[0]
    on_enter, _on_leave = breadcrumb._hover_handlers[0]
    on_focus_in, on_focus_out = breadcrumb._focus_handlers[0]

    on_focus_in()
    on_enter()
    on_focus_out()

    assert label.cget("foreground") == colors.accent
    assert label.cget("highlightthickness") == RESTING_RING_THICKNESS
    assert label.cget("highlightbackground") == colors.window
