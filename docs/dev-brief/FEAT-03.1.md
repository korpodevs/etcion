# Technical Brief: FEAT-03.1 Layer Enum

**Status:** Ready for TDD
**ADR Link:** `docs/adr/ADR-011-layer-enum.md`
**Epic:** EPIC-003 -- Language Structure and Classification
**Date:** 2026-03-24

---

## 1. Feature Summary

FEAT-03.1 ratifies the `Layer` enum that was pre-implemented in `src/pyarchi/enums.py` during FEAT-00.2. The enum is complete and correct (seven members, `enum.Enum` base, string values via `.value`). The remaining work is twofold: (1) close the public-API gap by adding `Layer` to the `from pyarchi.enums import ...` line and `__all__` list in `src/pyarchi/__init__.py`, and (2) write the STORY-03.1.2 test suite confirming all seven members, their values, importability from the top-level package, and the `enum.Enum`-not-`StrEnum` invariant.

---

## 2. Dependencies

| Dependency | Status | Reason |
|---|---|---|
| **FEAT-00.2** (Module Layout / `enums.py`) | Done | `Layer` is already defined in `src/pyarchi/enums.py`. |

No dependencies on other FEAT-03.x briefs.

---

## 3. Story-by-Story Implementation Guide

### STORY-03.1.1: Define `Layer` enum in `src/pyarchi/enums.py` with seven members

**Status:** Pre-implemented in `src/pyarchi/enums.py` (FEAT-00.2).

**Remaining work:** Add `Layer` to the public API surface in `src/pyarchi/__init__.py`.

**Files to modify:**
- `/home/kiera/dev/pyarchi/src/pyarchi/__init__.py`

**Diff -- new import line (add after existing imports):**

```python
# ADD this line after the Model import:
from pyarchi.enums import Layer
```

**Diff -- updated `__all__` (replace the EPIC-003 comment block):**

```python
    # language structure (EPIC-003)
    "Layer",
    # EPIC-003 (remaining):
    # - Aspect, NotationMetadata
```

**Acceptance Criteria:**
- `from pyarchi import Layer` succeeds.
- `hasattr(pyarchi, "Layer")` is `True`.
- `"Layer"` appears in `pyarchi.__all__`.
- `ruff check src/pyarchi/__init__.py` reports zero violations.
- `mypy src/pyarchi/__init__.py` reports zero errors.

**Gotchas:**
- Do NOT add `Aspect` or `NotationMetadata` to `__init__.py` yet. Those are FEAT-03.2 and FEAT-03.3 respectively.
- The import must be `from pyarchi.enums import Layer`, not `from pyarchi.enums import *`. Explicit imports prevent namespace pollution and satisfy ruff's `F403` rule.

---

### STORY-03.1.2: Write test asserting all seven values are present and accessible

**Files to create:**
- `/home/kiera/dev/pyarchi/test/test_feat031_layer.py`

**Acceptance Criteria:**
- All 12 test methods pass.
- `ruff check test/test_feat031_layer.py` reports zero violations.
- `mypy test/test_feat031_layer.py` reports zero errors.

**Full test file:**

```python
"""Tests for FEAT-03.1 -- Layer Enum."""

from __future__ import annotations

import pyarchi
from pyarchi.enums import Layer


class TestLayerEnum:
    def test_layer_has_seven_members(self) -> None:
        """Layer enum contains exactly seven members."""
        assert len(Layer) == 7

    def test_all_member_names_present(self) -> None:
        """All seven ArchiMate layer names are accessible as Layer.<NAME>."""
        expected = {
            "STRATEGY",
            "MOTIVATION",
            "BUSINESS",
            "APPLICATION",
            "TECHNOLOGY",
            "PHYSICAL",
            "IMPLEMENTATION_MIGRATION",
        }
        assert {m.name for m in Layer} == expected

    def test_strategy_value(self) -> None:
        assert Layer.STRATEGY.value == "Strategy"

    def test_motivation_value(self) -> None:
        assert Layer.MOTIVATION.value == "Motivation"

    def test_business_value(self) -> None:
        assert Layer.BUSINESS.value == "Business"

    def test_application_value(self) -> None:
        assert Layer.APPLICATION.value == "Application"

    def test_technology_value(self) -> None:
        assert Layer.TECHNOLOGY.value == "Technology"

    def test_physical_value(self) -> None:
        assert Layer.PHYSICAL.value == "Physical"

    def test_implementation_migration_value(self) -> None:
        assert Layer.IMPLEMENTATION_MIGRATION.value == "Implementation and Migration"

    def test_layer_importable_from_pyarchi(self) -> None:
        """Layer is re-exported from the top-level pyarchi package."""
        from pyarchi import Layer as TopLevelLayer

        assert TopLevelLayer is Layer

    def test_layer_in_pyarchi_all(self) -> None:
        """Layer appears in pyarchi.__all__."""
        assert "Layer" in pyarchi.__all__

    def test_enum_not_str_equal(self) -> None:
        """Layer uses enum.Enum, not StrEnum -- members do not equal plain strings."""
        assert Layer.BUSINESS != "Business"
```

**Gotchas:**
- `test_enum_not_str_equal` is the key invariant test. If someone accidentally changes the base class to `StrEnum`, this test will catch it because `StrEnum` members compare equal to their string value.
- `test_layer_importable_from_pyarchi` imports inside the test body to isolate the assertion. It also verifies identity (`is`) not just equality, confirming the re-export points to the same object.

---

## 4. Conformance Test `xfail` Removal Notice

The `TestShallFeatures::test_language_structure` test in `test/test_conformance.py` is currently marked `xfail`:

```python
@pytest.mark.xfail(
    strict=False,
    reason="EPIC-003: Language structure enums not yet re-exported",
)
def test_language_structure(self) -> None:
    assert hasattr(pyarchi, "Layer")
    assert hasattr(pyarchi, "Aspect")
```

This test checks for **both** `Layer` and `Aspect`. After FEAT-03.1, only `Layer` will be in `__init__.py`; `Aspect` is added by FEAT-03.2. The `xfail` marker must remain until **both** FEAT-03.1 and FEAT-03.2 are complete. Once FEAT-03.2 adds `Aspect` to `__init__.py`, remove the `@pytest.mark.xfail` decorator entirely so the test runs as a normal `PASSED` result.

**Do NOT remove the xfail in FEAT-03.1 alone.**

---

## 5. Updated `__init__.py` Snippet

Only the changed lines are shown. Full file context is omitted for brevity.

**New import line (add after the `from pyarchi.metamodel.model import Model` line):**

```python
from pyarchi.enums import Layer
```

**Updated `__all__` section (replace the EPIC-003 comment block):**

```python
    "Model",
    # language structure (EPIC-003)
    "Layer",
    # EPIC-003 (remaining):
    # - Aspect, NotationMetadata
    #
    # EPIC-004: Generic Metamodel -- Abstract Element Hierarchy
```

---

## 6. Verification Checklist

```bash
source .venv/bin/activate

# 1. Top-level import
python -c "from pyarchi import Layer; print('OK')"

# 2. __all__ membership
python -c "import pyarchi; assert 'Layer' in pyarchi.__all__; print('OK')"

# 3. Ruff linter
ruff check src/ test/

# 4. Ruff formatter
ruff format --check src/ test/

# 5. mypy
mypy src/

# 6. FEAT-03.1 tests
pytest test/test_feat031_layer.py -v

# 7. Full test suite (no regressions)
pytest
```
