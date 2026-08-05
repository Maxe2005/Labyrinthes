"""AST-based scan enforcing the domain/UI import boundaries (AD-1, AD-9).

Parses source statically -- it never imports the scanned modules -- so this
gate holds even before `application/`/`adapters/` exist, and it never
requires Tkinter to be importable. It establishes the boundary ahead of the
feature code it will guard (Story 1.2):

- `domain/` and `application/` depend on nothing from `adapters/` or any UI
  framework.
- `adapters/tkinter/{home,builder,player}` never import each other, and
  `adapters/tkinter/common/` never imports any of the three screens.
- `adapters/tkinter/` (the whole tree, not only the three screens) never
  imports `adapters/storage/` directly -- storage access always goes
  through an `application/` service.
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "labyrinthes"
SRC_ROOT = PACKAGE_ROOT.parent
REPO_ROOT = SRC_ROOT.parent

SCREEN_PACKAGES = ("home", "builder", "player")


def iter_python_files(directory: Path) -> list[Path]:
    """Every `.py` file under `directory`, or `[]` if the directory doesn't exist yet."""
    if not directory.is_dir():
        return []
    return sorted(directory.rglob("*.py"))


def module_name_for_file(file_path: Path, src_root: Path) -> str:
    """Dotted module name of `file_path`, given the `src`-style root it lives under."""
    parts = list(file_path.relative_to(src_root).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def package_name_for_file(file_path: Path, src_root: Path) -> str:
    """The `__package__` a relative import inside `file_path` would resolve against."""
    module_name = module_name_for_file(file_path, src_root)
    if file_path.name == "__init__.py":
        return module_name
    return module_name.rsplit(".", 1)[0]


def _resolve_relative_module(node: ast.ImportFrom, package: str) -> str | None:
    """Resolve a relative `ast.ImportFrom`'s base module, mirroring CPython's own algorithm."""
    if node.level == 0:
        return node.module
    bits = package.rsplit(".", node.level - 1)
    if len(bits) < node.level:
        return None  # relative import climbs above the top-level package
    base = bits[0]
    return f"{base}.{node.module}" if node.module else base


def resolve_imported_modules(file_path: Path, src_root: Path) -> set[str]:
    """All dotted module paths `file_path` might import, resolved from static AST.

    For `ast.ImportFrom`, yields both the resolved base module and, for each
    imported name, `f"{base}.{name}"` -- a statically-parsed `from x import y`
    cannot tell whether `y` is a submodule or a plain attribute of `x`, so both
    must be treated as potentially-forbidden targets. This is what catches
    `from labyrinthes.adapters.tkinter import builder` and
    `from labyrinthes import adapters` (name-based), not only
    `from ..builder import x` (module-based).

    Walks the whole tree, not just top-level statements, so lazily-imported
    modules (e.g. inside a function or an `if __name__ == "__main__":` guard)
    are caught too. Malformed source is allowed to raise `SyntaxError` rather
    than being swallowed -- a syntax error in a scanned file is itself a real
    problem worth a loud failure.
    """
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    package = package_name_for_file(file_path, src_root)
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = _resolve_relative_module(node, package)
            if base is None:
                continue
            modules.add(base)
            modules.update(f"{base}.{alias.name}" for alias in node.names)
    return modules


def _is_forbidden(module: str, forbidden_prefixes: Iterable[str]) -> bool:
    return any(module == prefix or module.startswith(f"{prefix}.") for prefix in forbidden_prefixes)


def find_forbidden_imports(
    directory: Path, src_root: Path, forbidden_prefixes: Iterable[str]
) -> list[tuple[Path, str]]:
    """Every `(file, forbidden module)` pair found under `directory`."""
    forbidden_prefixes = tuple(forbidden_prefixes)
    violations: list[tuple[Path, str]] = []
    for file_path in iter_python_files(directory):
        for module in sorted(resolve_imported_modules(file_path, src_root)):
            if _is_forbidden(module, forbidden_prefixes):
                violations.append((file_path, module))
    return violations


def _format_violations(violations: list[tuple[Path, str]]) -> str:
    return "\n".join(
        f"{path.relative_to(REPO_ROOT)}: forbidden import {module!r}" for path, module in violations
    )


def test_domain_and_application_do_not_import_tkinter_or_adapters():
    forbidden = ("tkinter", "labyrinthes.adapters")
    violations = [
        violation
        for subpackage in ("domain", "application")
        for violation in find_forbidden_imports(PACKAGE_ROOT / subpackage, SRC_ROOT, forbidden)
    ]
    assert not violations, _format_violations(violations)


def test_tkinter_screens_do_not_import_each_other():
    violations = []
    for screen in SCREEN_PACKAGES:
        other_screens = [other for other in SCREEN_PACKAGES if other != screen]
        forbidden = tuple(f"labyrinthes.adapters.tkinter.{other}" for other in other_screens)
        directory = PACKAGE_ROOT / "adapters" / "tkinter" / screen
        violations.extend(find_forbidden_imports(directory, SRC_ROOT, forbidden))
    assert not violations, _format_violations(violations)


def test_common_does_not_import_screens():
    forbidden = tuple(f"labyrinthes.adapters.tkinter.{screen}" for screen in SCREEN_PACKAGES)
    directory = PACKAGE_ROOT / "adapters" / "tkinter" / "common"
    violations = find_forbidden_imports(directory, SRC_ROOT, forbidden)
    assert not violations, _format_violations(violations)


def test_tkinter_does_not_import_storage_adapters():
    # AD-9: the whole adapters/tkinter/ tree, not only the three screens --
    # common/ must be covered too (this is what iteration 2 of this story missed).
    forbidden = ("labyrinthes.adapters.storage",)
    violations = []
    for subpackage in (*SCREEN_PACKAGES, "common"):
        directory = PACKAGE_ROOT / "adapters" / "tkinter" / subpackage
        violations.extend(find_forbidden_imports(directory, SRC_ROOT, forbidden))
    assert not violations, _format_violations(violations)
