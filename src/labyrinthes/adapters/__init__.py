"""Adapters: concrete implementations of the `application/` ports.

`adapters/storage/` (Story 1.4/1.5) imports only `domain/`/`application/`.
`adapters/tkinter/` (Story 1.6+) never imports `adapters/storage/` directly --
storage access always goes through an `application/` service (AD-1).
"""
