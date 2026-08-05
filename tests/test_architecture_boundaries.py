"""Static, AST-based scan enforcing the domain/UI architecture boundaries.

Source files are parsed, never imported — this must not require Tkinter to
be available and must not execute any scanned code as a side effect. It is
allowed (and expected) to pass today, before `application/`/`adapters/`
exist: a missing directory contributes zero files and zero violations,
establishing the gate ahead of the code it will guard (Story 1.2).

Resolving `from <pkg> import <name>` statically cannot distinguish a
submodule import (`labyrinthes.adapters.tkinter.builder`) from a plain
attribute access on `<pkg>`. We over-approximate for safety: both the
resolved base module and, for every imported name, `f"{base}.{name}"` are
checked against the forbidden-prefix list. This is what catches
`from labyrinthes.adapters.tkinter import builder` and
`from labyrinthes import adapters`, not only `from ..builder import x`.
"""

import ast
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "src" / "labyrinthes"
SRC_ROOT = PACKAGE_ROOT.parent

SCREENS = ("home", "builder", "player")


def _iter_python_files(directory: Path) -> list[Path]:
    """Return every `.py` file under `directory`, or `[]` if it doesn't exist."""
    if not directory.is_dir():
        return []
    return sorted(directory.rglob("*.py"))


def _module_name_for(path: Path) -> str:
    """Dotted module name of `path`, e.g. `labyrinthes.adapters.tkinter.home`."""
    parts = list(path.relative_to(SRC_ROOT).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _enclosing_package(module_name: str, is_package: bool) -> str:
    """The dotted package a module belongs to, used to resolve relative imports."""
    if is_package:
        return module_name
    if "." not in module_name:
        return ""
    return module_name.rsplit(".", 1)[0]


def _resolve_relative_base(module_package: str, level: int) -> str:
    """Walk `level` packages up from `module_package` (mirrors `from . import`)."""
    if level <= 1:
        return module_package
    parts = module_package.split(".") if module_package else []
    keep = max(len(parts) - (level - 1), 0)
    return ".".join(parts[:keep])


def _imported_modules(path: Path) -> set[str]:
    """All dotted module paths a file's imports could plausibly refer to.

    For each `ast.ImportFrom`, yields both the resolved base module and, for
    every imported name, `base.name` — see module docstring for why.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    module_name = _module_name_for(path)
    module_package = _enclosing_package(module_name, is_package=path.name == "__init__.py")

    resolved: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                resolved.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                base = node.module or ""
            else:
                base = _resolve_relative_base(module_package, node.level)
                if node.module:
                    base = f"{base}.{node.module}" if base else node.module
            if base:
                resolved.add(base)
            for alias in node.names:
                if alias.name == "*":
                    continue
                resolved.add(f"{base}.{alias.name}" if base else alias.name)
    return resolved


def _is_forbidden(module: str, forbidden_prefix: str) -> bool:
    return module == forbidden_prefix or module.startswith(f"{forbidden_prefix}.")


def _find_violations(directory: Path, forbidden_prefixes: Sequence[str]) -> list[str]:
    """Repo-relative `path: import` strings for every forbidden import found."""
    violations = []
    for path in _iter_python_files(directory):
        for module in sorted(_imported_modules(path)):
            if any(_is_forbidden(module, prefix) for prefix in forbidden_prefixes):
                violations.append(f"{path.relative_to(REPO_ROOT)}: {module}")
    return violations


def test_domain_and_application_do_not_import_tkinter_or_adapters():
    directories = [PACKAGE_ROOT / "domain", PACKAGE_ROOT / "application"]
    forbidden_prefixes = ["tkinter", "labyrinthes.adapters"]

    violations = [
        violation
        for directory in directories
        for violation in _find_violations(directory, forbidden_prefixes)
    ]

    assert not violations, "forbidden imports found:\n" + "\n".join(violations)


def test_tkinter_screens_do_not_import_each_other():
    violations = []
    for screen in SCREENS:
        directory = PACKAGE_ROOT / "adapters" / "tkinter" / screen
        forbidden_prefixes = [
            f"labyrinthes.adapters.tkinter.{other}" for other in SCREENS if other != screen
        ]
        violations.extend(_find_violations(directory, forbidden_prefixes))

    assert not violations, "forbidden imports found:\n" + "\n".join(violations)


def test_common_does_not_import_screens():
    directory = PACKAGE_ROOT / "adapters" / "tkinter" / "common"
    forbidden_prefixes = [f"labyrinthes.adapters.tkinter.{screen}" for screen in SCREENS]

    violations = _find_violations(directory, forbidden_prefixes)

    assert not violations, "forbidden imports found:\n" + "\n".join(violations)


def test_tkinter_screens_do_not_import_storage_adapters():
    violations = []
    for screen in SCREENS:
        directory = PACKAGE_ROOT / "adapters" / "tkinter" / screen
        violations.extend(_find_violations(directory, ["labyrinthes.adapters.storage"]))

    assert not violations, "forbidden imports found:\n" + "\n".join(violations)
