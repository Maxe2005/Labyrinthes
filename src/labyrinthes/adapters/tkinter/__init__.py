"""Tkinter UI adapters (AD-11).

Layout, established incrementally story-by-story:

- `common/` -- shared design tokens and widget primitives (Story 1.6),
  imported by every screen below; never imports any of them back.
- `home/` -- the Home hub screen (Story 1.8).
- `builder/` -- the maze Builder screen (Epic 2).
- `player/` -- the maze Player screen (Epic 3).

Today only `common/` exists; the other three are named here so the intended
shape is visible ahead of the stories that add them.
"""
