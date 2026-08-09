"""Atomic file writes -- write-to-temp-then-rename, never in-place truncation.

Both `write_maze_csv` and `write_setting_value` route their writes through
`atomic_open_for_write` (AC 1): a write interrupted by a process crash or
kill must never leave the previously saved file corrupted or truncated.
`os.replace` (not `Path.rename`) is atomic on both POSIX and Windows. The
temp file is created in `path`'s own parent directory, never the OS default
temp dir, so the final replace is guaranteed to land on the same filesystem
-- a cross-filesystem `os.replace` is not atomic, and on some platforms
isn't even possible.
"""

from __future__ import annotations

import contextlib
import os
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import IO


@contextlib.contextmanager
def atomic_open_for_write(
    path: Path, *, encoding: str, newline: str | None = None
) -> Iterator[IO[str]]:
    """Yield a writable text handle; atomically replace `path` with it on a clean exit.

    Callers are responsible for `path.parent.mkdir(parents=True,
    exist_ok=True)` before calling this -- it doesn't duplicate that. On an
    exception raised inside the `with` block, the temp file is closed and
    deleted, then the exception is re-raised: `path` is left untouched (or
    absent, if it didn't exist yet), and no stray temp file remains.
    """
    with tempfile.NamedTemporaryFile(
        mode="w", dir=path.parent, encoding=encoding, newline=newline, delete=False
    ) as tmp_file:
        tmp_path = Path(tmp_file.name)
        try:
            yield tmp_file
        except BaseException:
            tmp_file.close()
            tmp_path.unlink(missing_ok=True)
            raise
    os.replace(tmp_path, path)
