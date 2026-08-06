"""Application shell: the single composition root and screen router (Story 1.7).

Owns the one `tk.Tk()` root and the `Router` that Home, Builder, and Player
register into via a shared `mount(parent, state) -> Frame` interface. This is
the only layer allowed to import concrete screen modules directly (AD-10).
"""
