"""Regression tests pinning the AST import-scanner's own resolution behavior.

Builds throwaway `src/labyrinthes/...`-shaped trees under `tmp_path` -- never
the real `src/labyrinthes/` tree -- and asserts the scanner catches known
synthetic violations (submodule-style, name-based, relative imports) and
reports zero violations for a known-clean fixture.

Both prior implementation attempts at this story had a working-looking
scanner with a real resolution bug (a missed name-based import form, then a
missed `common/` subpackage in the storage check) that the boundary tests in
`test_architecture_boundaries.py` never caught, because `domain/` is clean by
construction and `application/`/`adapters/` don't exist yet -- those tests
were tautologically green either way. These fixture tests exercise the
scanner directly against known violations so a regression here fails loudly
instead of the boundary tests trivially passing.
"""

from pathlib import Path

from tests.test_architecture_boundaries import find_forbidden_imports


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_submodule_style_import_of_forbidden_target_is_detected(tmp_path):
    src_root = tmp_path / "src"
    home_dir = src_root / "labyrinthes" / "adapters" / "tkinter" / "home"
    foo = _write(home_dir / "foo.py", "from ..builder import something\n")

    violations = find_forbidden_imports(
        home_dir, src_root, ("labyrinthes.adapters.tkinter.builder",)
    )

    assert (foo, "labyrinthes.adapters.tkinter.builder") in violations


def test_name_based_import_of_forbidden_package_is_detected(tmp_path):
    src_root = tmp_path / "src"
    domain_dir = src_root / "labyrinthes" / "domain"
    foo = _write(domain_dir / "foo.py", "from labyrinthes import adapters\n")

    violations = find_forbidden_imports(domain_dir, src_root, ("labyrinthes.adapters",))

    assert (foo, "labyrinthes.adapters") in violations


def test_relative_import_is_detected(tmp_path):
    src_root = tmp_path / "src"
    common_dir = src_root / "labyrinthes" / "adapters" / "tkinter" / "common"
    x = _write(common_dir / "x.py", "from ..home import y\n")

    violations = find_forbidden_imports(
        common_dir, src_root, ("labyrinthes.adapters.tkinter.home",)
    )

    assert (x, "labyrinthes.adapters.tkinter.home") in violations


def test_directory_with_no_forbidden_imports_yields_zero_violations(tmp_path):
    src_root = tmp_path / "src"
    domain_dir = src_root / "labyrinthes" / "domain"
    _write(domain_dir / "foo.py", "from dataclasses import dataclass\n\nimport itertools\n")

    violations = find_forbidden_imports(domain_dir, src_root, ("tkinter", "labyrinthes.adapters"))

    assert violations == []
