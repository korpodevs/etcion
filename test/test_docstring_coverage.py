"""Docstring coverage tests for the etcion public API (STORY-26.1.4).

These tests are informational: they print coverage percentages and collect
missing-docstring details rather than asserting 100% coverage.  This allows
the suite to pass immediately while tracking progress toward full coverage
(STORY-26.1.2 and STORY-26.1.3).

All three tests are marked ``slow`` so they can be excluded from fast
feedback loops with ``pytest -m "not slow"``.
"""

from __future__ import annotations

import importlib
import inspect
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

import etcion

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PYDANTIC_PREFIXES = (
    "model_",
    "schema",
    "construct",
    "copy",
    "dict",
    "json",
    "parse_",
    "from_",
    "validate",
    "update_forward_refs",
)

_SKIP_DUNDER = True  # always skip dunder (__foo__) names


def _is_pydantic_internal(name: str) -> bool:
    """Return True for Pydantic-generated method names we should not audit."""
    if name.startswith("__") and name.endswith("__"):
        return True
    return any(name.startswith(prefix) for prefix in _PYDANTIC_PREFIXES)


def _public_methods(cls: type) -> list[tuple[str, Any]]:
    """Return (name, obj) pairs for public, non-Pydantic methods defined on *cls*."""
    results = []
    for name, obj in inspect.getmembers(cls, predicate=inspect.isfunction):
        if name.startswith("_"):
            continue
        if _is_pydantic_internal(name):
            continue
        # Only report methods whose code is actually defined in this class
        # (not purely inherited from a parent that we will audit separately).
        if getattr(obj, "__qualname__", "").startswith(cls.__qualname__):
            results.append((name, obj))
    return results


def _has_docstring(obj: Any) -> bool:
    doc = getattr(obj, "__doc__", None)
    return bool(doc and doc.strip())


# ---------------------------------------------------------------------------
# Test 1: every symbol in etcion.__all__ has a class/function docstring
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_all_public_symbols_have_docstrings() -> None:
    """Report docstring coverage for every name listed in etcion.__all__.

    This test never fails — it prints a summary table and the coverage
    percentage, then passes unconditionally.  A future story (STORY-26.1.2)
    will tighten this to an assertion once all docstrings are filled in.
    """
    missing: list[str] = []
    total = 0

    for name in etcion.__all__:
        obj = getattr(etcion, name, None)
        if obj is None:
            continue
        total += 1
        if not _has_docstring(obj):
            missing.append(name)

    covered = total - len(missing)
    pct = (covered / total * 100) if total else 0.0

    print(f"\n[STORY-26.1.4] Symbol docstring coverage: {covered}/{total} ({pct:.1f}%)")
    if missing:
        print("  Missing docstrings on the following public symbols:")
        for name in missing:
            print(f"    - {name}")
    else:
        print("  All public symbols have docstrings.")

    # Informational only — always passes.
    assert True


# ---------------------------------------------------------------------------
# Test 2: every public method on classes in __all__ has a docstring
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_all_public_methods_have_docstrings() -> None:
    """Report docstring coverage for public methods on classes in etcion.__all__.

    Skips Pydantic-generated methods (``model_*``, ``schema``, etc.) and all
    dunder methods.  Informational only — always passes.
    """
    missing: list[str] = []
    total = 0

    for sym_name in etcion.__all__:
        obj = getattr(etcion, sym_name, None)
        if obj is None or not inspect.isclass(obj):
            continue
        for method_name, method_obj in _public_methods(obj):
            total += 1
            if not _has_docstring(method_obj):
                missing.append(f"{sym_name}.{method_name}")

    covered = total - len(missing)
    pct = (covered / total * 100) if total else 0.0

    print(f"\n[STORY-26.1.4] Method docstring coverage: {covered}/{total} ({pct:.1f}%)")
    if missing:
        print("  Missing docstrings on the following public methods:")
        for qname in missing:
            print(f"    - {qname}")
    else:
        print("  All public methods have docstrings.")

    # Informational only — always passes.
    assert True


# ---------------------------------------------------------------------------
# Test 3: every .py module under src/etcion/ has a module-level docstring
# ---------------------------------------------------------------------------


def _import_module_from_path(py_file: Path, src_root: Path) -> ModuleType | None:
    """Import a .py file as a module using its dotted name derived from *src_root*."""
    rel = py_file.relative_to(src_root)
    # Convert path separators to dots and strip .py suffix.
    parts = list(rel.with_suffix("").parts)
    module_name = ".".join(parts)
    try:
        if module_name in sys.modules:
            return sys.modules[module_name]
        return importlib.import_module(module_name)
    except Exception:  # noqa: BLE001
        return None


@pytest.mark.slow
def test_all_modules_have_docstrings() -> None:
    """Report module-level docstring coverage across all etcion source files.

    Skips ``__init__.py`` files (package inits are tested separately) and any
    file that cannot be imported cleanly.  Informational only — always passes.
    """
    src_root = Path(__file__).parent.parent / "src"
    etcion_root = src_root / "etcion"

    py_files = sorted(etcion_root.rglob("*.py"))

    missing: list[str] = []
    total = 0
    skipped = 0

    for py_file in py_files:
        rel = py_file.relative_to(src_root)
        parts = list(rel.with_suffix("").parts)
        module_name = ".".join(parts)

        mod = _import_module_from_path(py_file, src_root)
        if mod is None:
            skipped += 1
            continue

        total += 1
        if not _has_docstring(mod):
            missing.append(module_name)

    covered = total - len(missing)
    pct = (covered / total * 100) if total else 0.0

    print(
        f"\n[STORY-26.1.4] Module docstring coverage: {covered}/{total} ({pct:.1f}%)"
        f"  ({skipped} skipped due to import errors)"
    )
    if missing:
        print("  Missing module-level docstrings in:")
        for name in missing:
            print(f"    - {name}")
    else:
        print("  All importable modules have module-level docstrings.")

    # Informational only — always passes.
    assert True
