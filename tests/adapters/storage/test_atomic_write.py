import os
import stat

import pytest

from labyrinthes.adapters.storage import atomic_write
from labyrinthes.adapters.storage.atomic_write import atomic_open_for_write


def test_writes_content_and_leaves_no_temp_file(tmp_path):
    path = tmp_path / "file.txt"

    with atomic_open_for_write(path, encoding="utf-8") as handle:
        handle.write("hello")

    assert path.read_text(encoding="utf-8") == "hello"
    assert list(tmp_path.iterdir()) == [path]


def test_written_file_matches_the_umask_respecting_default_mode_not_tempfiles_0600(tmp_path):
    path = tmp_path / "file.txt"
    current_umask = os.umask(0)
    os.umask(current_umask)
    expected_mode = 0o666 & ~current_umask

    with atomic_open_for_write(path, encoding="utf-8") as handle:
        handle.write("hello")

    assert stat.S_IMODE(path.stat().st_mode) == expected_mode


def test_a_replace_that_fails_leaves_no_stray_temp_file(tmp_path, monkeypatch):
    path = tmp_path / "file.txt"
    path.write_text("original", encoding="utf-8")

    def flaky_replace(*args, **kwargs):
        raise OSError("boom")

    monkeypatch.setattr(atomic_write.os, "replace", flaky_replace)

    with pytest.raises(OSError, match="boom"), atomic_open_for_write(path, encoding="utf-8") as h:
        h.write("new content")

    assert path.read_text(encoding="utf-8") == "original"
    assert list(tmp_path.iterdir()) == [path]


def test_a_write_that_raises_mid_write_leaves_an_existing_prior_file_untouched(tmp_path):
    path = tmp_path / "file.txt"
    path.write_text("original", encoding="utf-8")

    with pytest.raises(RuntimeError), atomic_open_for_write(path, encoding="utf-8") as handle:
        handle.write("corrupt")
        raise RuntimeError("boom")

    assert path.read_text(encoding="utf-8") == "original"
    assert list(tmp_path.iterdir()) == [path]


def test_a_write_that_raises_mid_write_with_no_prior_file_leaves_no_stray_temp_file(tmp_path):
    path = tmp_path / "file.txt"

    with pytest.raises(RuntimeError), atomic_open_for_write(path, encoding="utf-8") as handle:
        handle.write("partial")
        raise RuntimeError("boom")

    assert not path.exists()
    assert list(tmp_path.iterdir()) == []
