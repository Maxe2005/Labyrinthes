"""Structural boundary tests for the `labyrinthes` package layout.

These tests scan source files with `ast` only -- they never `import` the
code under test -- so they hold even before `application/`/`adapters/`
exist, and they never require Tkinter to be importable/available.

Enforced boundaries (see epic-1-context.md "Technical Decisions"):
- `domain/` and `application/` depend on nothing UI-related: no `tkinter`
  and no `labyrinthes.adapters*`.
- The three screen packages under `adapters/tkinter/` (`home/`, `builder/`,
  `player/`) never import each other directly; all navigation goes through
  the shell's router instead.
- `adapters/tkinter/common/` never imports any of the three screen
  packages, since screens depend on `common/` and not the reverse.
"""

import ast
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "labyrinthes"


def iter_module_imports(directory: Path):
    """Yield `(file, imported_dotted_module)` for every import in `directory`.

    Walks `directory` recursively for `.py` files and parses each with `ast`
    (no execution, no real import). Absolute imports are yielded as-is;
    relative imports (`from . import x`, `from ..adapters import y`) are
    resolved against the importing file's own dotted module path so callers
    always see a true absolute dotted path. Yields nothing for a directory
    that does not exist.
    """
    if not directory.is_dir():
        return

    for file in sorted(directory.rglob("*.py")):
        tree = ast.parse(file.read_text(encoding="utf-8"), filename=str(file))
        package_name = _package_name_for(file)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    yield file, alias.name
            elif isinstance(node, ast.ImportFrom):
                yield file, _resolve_from_import(node, package_name)


def _package_name_for(file: Path) -> str:
    """Dotted `__package__` value that governs relative imports in `file`.

    This is the dotted path of `file`'s *parent directory*, rooted at
    `labyrinthes` -- true for both a regular module and a package's
    `__init__.py` alike, matching CPython's own `__package__` semantics.
    """
    relative = file.relative_to(PACKAGE_ROOT.parent)
    return ".".join(relative.parts[:-1])


def _resolve_from_import(node: ast.ImportFrom, package_name: str) -> str:
    """Dotted module path a `from ... import ...` statement refers to."""
    if node.level == 0:
        return node.module or ""

    # Mirrors importlib's `_resolve_name`: level=1 is the importing file's
    # own package; each further level climbs one package up from there.
    base = package_name if node.level == 1 else package_name.rsplit(".", node.level - 1)[0]
    return f"{base}.{node.module}" if node.module else base


def test_domain_and_application_do_not_import_tkinter_or_adapters():
    forbidden_directories = [PACKAGE_ROOT / "domain", PACKAGE_ROOT / "application"]

    violations = [
        (file, imported)
        for directory in forbidden_directories
        for file, imported in iter_module_imports(directory)
        if imported == "tkinter"
        or imported.startswith("tkinter.")
        or imported == "labyrinthes.adapters"
        or imported.startswith("labyrinthes.adapters.")
    ]

    assert not violations, "domain/application must not import tkinter or adapters:\n" + "\n".join(
        f"  {file}: imports {imported!r}" for file, imported in violations
    )


def test_tkinter_screens_do_not_import_each_other():
    screens_root = PACKAGE_ROOT / "adapters" / "tkinter"
    screen_names = ("home", "builder", "player")

    violations = []
    for screen_name in screen_names:
        other_screens = [name for name in screen_names if name != screen_name]
        for file, imported in iter_module_imports(screens_root / screen_name):
            if any(
                imported == f"labyrinthes.adapters.tkinter.{other}"
                or imported.startswith(f"labyrinthes.adapters.tkinter.{other}.")
                for other in other_screens
            ):
                violations.append((file, imported))

    assert not violations, "tkinter screens must not import each other:\n" + "\n".join(
        f"  {file}: imports {imported!r}" for file, imported in violations
    )


def test_common_does_not_import_screens():
    common_directory = PACKAGE_ROOT / "adapters" / "tkinter" / "common"
    screen_names = ("home", "builder", "player")

    violations = [
        (file, imported)
        for file, imported in iter_module_imports(common_directory)
        if any(
            imported == f"labyrinthes.adapters.tkinter.{screen}"
            or imported.startswith(f"labyrinthes.adapters.tkinter.{screen}.")
            for screen in screen_names
        )
    ]

    assert not violations, "common/ must not import screen packages:\n" + "\n".join(
        f"  {file}: imports {imported!r}" for file, imported in violations
    )
