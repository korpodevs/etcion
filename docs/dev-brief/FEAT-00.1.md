# Technical Brief: FEAT-00.1 Package Configuration

**Status:** Ready for Implementation

**ADR Link:** `docs/adr/ADR-001-package-configuration.md`

**Epic:** EPIC-000 -- Project Scaffold and Build System

**Date:** 2026-03-23

---

## 1. Feature Summary

FEAT-00.1 establishes the complete build system, package layout, test runner, linter, and type checker for the `pyarchi` library. This feature is the prerequisite for every subsequent epic in the Phase 1 backlog: no metamodel class, enum, validation rule, or test can be written until the project has a working `pyproject.toml`, an importable `src/pyarchi/` package, a pytest configuration, a Ruff linter configuration, and a mypy strict-mode setup with the Pydantic plugin. The five stories in this feature translate the decisions from ADR-001 into concrete files and configuration.

---

## 2. Story-by-Story Implementation Guide

### STORY-00.1.1: Create `pyproject.toml`

**Files to create:**
- `/home/kiera/dev/pyarchi/pyproject.toml`

**Content:** See Section 3 below for the complete file.

**Acceptance Criteria:**
- `pyproject.toml` exists at the repository root.
- Build backend is `hatchling`.
- `[project]` section uses PEP 621 metadata with `name = "pyarchi"`, `version = "0.1.0"`, `requires-python = ">=3.12"`.
- `dependencies` contains exactly `"pydantic>=2.0,<3.0"`.
- No `setup.py`, `setup.cfg`, or `requirements.txt` exists.
- `pip install -e .` succeeds in the virtual environment.

**Gotchas:**
- Hatchling auto-discovers packages under `src/` when `[tool.hatch.build.targets.wheel]` sets `packages = ["src/pyarchi"]`. This must be explicit to avoid discovery of `test/` or `docs/`.
- The `version` field is mandatory in `[project]` for Hatchling. Start at `0.1.0`.

---

### STORY-00.1.2: Establish `src/pyarchi/` package directory

**Files to create:**
- `/home/kiera/dev/pyarchi/src/pyarchi/__init__.py`
- `/home/kiera/dev/pyarchi/src/pyarchi/py.typed` (PEP 561 marker)

**Content for `__init__.py`:** See Section 4 below.

**Content for `py.typed`:** Empty file (zero bytes). Its presence signals to mypy and other type checkers that this package ships inline types.

**Acceptance Criteria:**
- `src/pyarchi/__init__.py` exists and is importable as `import pyarchi`.
- `pyarchi.SPEC_VERSION` returns `"3.2"`.
- `pyarchi.__all__` is defined.
- `src/pyarchi/py.typed` exists (PEP 561 compliance).
- After `pip install -e .`, running `python -c "import pyarchi; print(pyarchi.SPEC_VERSION)"` prints `3.2`.

**Gotchas:**
- The `py.typed` marker file is required for mypy strict mode to treat the package as typed. Without it, mypy will skip type checking of the package when imported by downstream consumers.

---

### STORY-00.1.3: Configure pytest and create `test/conftest.py`

**Files to create:**
- `/home/kiera/dev/pyarchi/test/__init__.py` (empty, makes `test/` a package for pytest discovery)
- `/home/kiera/dev/pyarchi/test/conftest.py`

**Configuration in `pyproject.toml`:** See `[tool.pytest.ini_options]` in Section 3.

**Content for `test/conftest.py`:** See Section 5 below.

**Acceptance Criteria:**
- `[tool.pytest.ini_options]` is present in `pyproject.toml`.
- `testpaths = ["test"]` is set.
- `pythonpath = ["src"]` is set.
- `addopts` includes `-ra -q --strict-markers` for strict marker enforcement and summary output.
- `test/conftest.py` exists with placeholder fixtures.
- Running `pytest` from the repository root succeeds with 0 tests collected (no test files yet, but no configuration errors).

**Gotchas:**
- `pythonpath = ["src"]` is required so that `import pyarchi` resolves during test runs without requiring `pip install -e .` first. Both mechanisms should work.
- `--strict-markers` means any test decorated with an unregistered `@pytest.mark.xxx` will fail. Register custom markers in `[tool.pytest.ini_options]` under `markers` as the test suite grows.
- The `test/__init__.py` file should be empty. Its purpose is solely to allow pytest to resolve relative imports within the test suite.

---

### STORY-00.1.4: Configure Ruff

**Configuration in `pyproject.toml`:** See `[tool.ruff]` and `[tool.ruff.lint]` in Section 3.

**Acceptance Criteria:**
- `[tool.ruff]` section sets `target-version = "py312"` and `src = ["src", "test"]`.
- `[tool.ruff.lint]` section enables rule sets: `select = ["E", "W", "I", "ANN", "B"]`.
- ANN101 and ANN102 are ignored (deprecated rules for `self` and `cls` annotations, removed in modern Ruff but listed for safety).
- `[tool.ruff.lint.per-file-ignores]` relaxes ANN rules for test files (`test/**` ignores `ANN`).
- `ruff check src/ test/` passes with zero violations.
- `ruff format --check src/ test/` passes with zero violations.

**Gotchas:**
- Ruff v0.4+ uses `[tool.ruff.lint]` for `select`, `ignore`, and `per-file-ignores`. Placing these under `[tool.ruff]` directly is a configuration error in current Ruff versions.
- ANN rules on test files create excessive friction (fixtures, parametrize callbacks). Suppress them via per-file-ignores.
- The `src = ["src", "test"]` setting tells Ruff where first-party imports live, which is critical for correct import sorting (I rules).

---

### STORY-00.1.5: Add mypy configuration

**Configuration in `pyproject.toml`:** See `[tool.mypy]` in Section 3.

**Acceptance Criteria:**
- `[tool.mypy]` section sets `strict = true`.
- `plugins = ["pydantic.mypy"]` is configured.
- `warn_return_any = true` and `warn_unreachable = true` are set.
- `mypy src/` passes with zero errors.
- `mypy test/` passes with zero errors (once test files exist).

**Gotchas:**
- The `pydantic.mypy` plugin requires `pydantic` to be installed. The editable install (`pip install -e .`) must be done before running mypy.
- `strict = true` enables `disallow_untyped_defs`, `disallow_any_generics`, `no_implicit_optional`, and many other flags. Every function signature in `src/pyarchi/` must have full type annotations from day one.
- Add `[[tool.mypy.overrides]]` for test files to relax `disallow_untyped_defs` since test functions commonly lack return type annotations.

---

## 3. `pyproject.toml` -- Complete Reference

This is the full, working file after all five stories are complete.

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "pyarchi"
version = "0.1.0"
description = "A Python library implementing the ArchiMate 3.2 metamodel"
readme = "README.md"
license = "MIT"
requires-python = ">=3.12"
authors = [
    { name = "pyarchi contributors" },
]
classifiers = [
    "Development Status :: 2 - Pre-Alpha",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.12",
    "Typing :: Typed",
]
dependencies = [
    "pydantic>=2.0,<3.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "mypy>=1.10",
    "pydantic>=2.0,<3.0",
    "ruff>=0.4",
]

[tool.hatch.build.targets.wheel]
packages = ["src/pyarchi"]

# ---------------------------------------------------------------------------
# pytest
# ---------------------------------------------------------------------------
[tool.pytest.ini_options]
testpaths = ["test"]
pythonpath = ["src"]
addopts = "-ra -q --strict-markers"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks integration tests requiring external resources",
]

# ---------------------------------------------------------------------------
# Ruff
# ---------------------------------------------------------------------------
[tool.ruff]
target-version = "py312"
src = ["src", "test"]
line-length = 100

[tool.ruff.lint]
select = ["E", "W", "I", "ANN", "B"]
ignore = [
    "ANN101",  # Missing type annotation for `self` in method (deprecated)
    "ANN102",  # Missing type annotation for `cls` in classmethod (deprecated)
]

[tool.ruff.lint.per-file-ignores]
"test/**" = ["ANN"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

# ---------------------------------------------------------------------------
# mypy
# ---------------------------------------------------------------------------
[tool.mypy]
strict = true
plugins = ["pydantic.mypy"]
warn_return_any = true
warn_unreachable = true

[[tool.mypy.overrides]]
module = "test.*"
disallow_untyped_defs = false
disallow_untyped_decorators = false
```

---

## 4. `src/pyarchi/__init__.py` -- Initial Skeleton

```python
"""pyarchi -- Python implementation of the ArchiMate 3.2 metamodel."""

SPEC_VERSION: str = "3.2"
"""The ArchiMate specification version implemented by this library."""

__all__: list[str] = [
    "SPEC_VERSION",
    # EPIC-001: Scope and Conformance
    # - ConformanceProfile
    #
    # EPIC-002: Root Type Hierarchy
    # - Concept, Element, Relationship, RelationshipConnector
    # - AttributeMixin
    # - Model
    #
    # EPIC-003: Language Structure and Classification
    # - Layer, Aspect, NotationMetadata
    #
    # EPIC-004: Generic Metamodel -- Abstract Element Hierarchy
    # - StructureElement, ActiveStructureElement, PassiveStructureElement
    # - BehaviorElement, MotivationElement, CompositeElement
    # - Grouping, Location
    #
    # EPIC-005: Relationships and Relationship Connectors
    # - Composition, Aggregation, Assignment, Realization
    # - Serving, Access, Influence, Association
    # - Triggering, Flow, Specialization
    # - Junction
    # - DerivationEngine
]
```

---

## 5. `test/conftest.py` -- Initial Skeleton

```python
"""Shared pytest fixtures for the pyarchi test suite.

Fixture Strategy
----------------
Fixtures are organized in layers to support composable test scenarios:

1. **Atomic fixtures** -- Return a single element or relationship instance.
   These are the building blocks used by most unit tests.
   Examples: `sample_element`, `sample_relationship`

2. **Container fixtures** -- Return a pre-populated `Model` with a known
   set of elements and relationships. Used by integration tests and
   derivation engine tests.
   Examples: `empty_model`, `populated_model`

3. **Factory fixtures** -- Return callables that produce instances with
   configurable attributes. Used by parametrized tests that need many
   variations of the same type.
   Examples: `element_factory`, `relationship_factory`

All fixtures are defined with explicit scope. Default scope is "function"
(a fresh instance per test). Fixtures that are expensive to construct and
are read-only should use "module" or "session" scope.

As concrete metamodel classes are implemented in later epics, fixtures
will be added here incrementally. Each epic's technical brief will
specify which fixtures to add.
"""

from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture()
def empty_model() -> dict[str, Any]:
    """Return a minimal model container with no elements or relationships.

    This fixture will be updated to return a `Model` instance once
    EPIC-002 (FEAT-02.6) implements the Model container class.
    Current return type is a plain dict as a placeholder.
    """
    return {"elements": [], "relationships": []}


@pytest.fixture()
def sample_element() -> dict[str, Any]:
    """Return a sample element with default attributes.

    This fixture will be updated to return a concrete `Element` subclass
    instance once EPIC-002 (FEAT-02.1, FEAT-02.2) implements the element
    hierarchy. Current return type is a plain dict as a placeholder.
    """
    return {
        "id": "id-placeholder-element-001",
        "name": "Sample Element",
        "description": None,
        "documentation_url": None,
    }
```

---

## 6. Verification Checklist

Run these commands sequentially from the repository root after completing all five stories. Every command must exit with code 0 and produce no errors.

```bash
# 0. Activate the virtual environment
source .venv/bin/activate

# 1. Install the package in editable mode with dev dependencies
pip install -e ".[dev]"

# 2. Verify the package is importable and SPEC_VERSION is correct
python -c "import pyarchi; assert pyarchi.SPEC_VERSION == '3.2'; print('OK: import and SPEC_VERSION')"

# 3. Verify py.typed marker exists
python -c "from pathlib import Path; import pyarchi; p = Path(pyarchi.__file__).parent / 'py.typed'; assert p.exists(); print('OK: py.typed')"

# 4. Run ruff linter
ruff check src/ test/

# 5. Run ruff formatter check
ruff format --check src/ test/

# 6. Run mypy strict type checking
mypy src/

# 7. Run pytest (expects 0 collected, 0 errors)
pytest

# 8. Verify no stray configuration files exist
test ! -f setup.py && test ! -f setup.cfg && test ! -f requirements.txt && echo "OK: no legacy config files"
```

---

## 7. CLAUDE.md Update

After all five stories are complete, replace the **Development Setup** section in `CLAUDE.md` with the following:

```markdown
## Development Setup

Activate the virtual environment and install in editable mode with dev dependencies:

```bash
source .venv/bin/activate
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest                    # Run all tests
pytest -x                 # Stop on first failure
pytest -m "not slow"      # Skip slow tests
```

### Linting and Formatting

```bash
ruff check src/ test/           # Lint
ruff check src/ test/ --fix     # Lint and auto-fix
ruff format src/ test/          # Format in place
ruff format --check src/ test/  # Check formatting without changing files
```

### Type Checking

```bash
mypy src/         # Type-check library source
mypy src/ test/   # Type-check library and tests
```

### Build

```bash
pip install -e ".[dev]"   # Editable install with dev dependencies
pip install -e .          # Editable install, runtime deps only
```
