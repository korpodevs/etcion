# Technical Brief: FEAT-05.4 Dependency Relationships -- Access

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-017-epic005-relationships.md` ss2, ss4
**Epic:** EPIC-005

---

## Feature Summary

Define `Access(DependencyRelationship)` with an `access_mode: AccessMode` field. `AccessMode` enum already exists in `enums.py` (ratified ADR-017 ss2). Validation stories (05.4.3-05.4.4) are deferred to model-level.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-05.3 (`DependencyRelationship` in `relationships.py`) | Must be done first |
| `AccessMode` in `enums.py` | Done (ratified ADR-017 ss2) |

## Stories -> Acceptance

| Story | Testable Now? | Acceptance |
|---|---|---|
| 05.4.1 | Tests only | `AccessMode` exists with `READ`, `WRITE`, `READ_WRITE`, `UNSPECIFIED` |
| 05.4.2 | Yes | `Access` instantiates; `access_mode` defaults to `UNSPECIFIED` |
| 05.4.3 | No -- xfail | Direction validation deferred to model-level |
| 05.4.4 | No -- xfail | Direction validation deferred to model-level |
| 05.4.5 | Yes | `Access` accepts all four `AccessMode` values |

## Implementation

### Additions to `src/pyarchi/metamodel/relationships.py`

```python
from pyarchi.enums import AccessMode

# ... existing classes ...


class Access(DependencyRelationship):
    access_mode: AccessMode = AccessMode.UNSPECIFIED

    @property
    def _type_name(self) -> str:
        return "Access"
```

## Test File: `test/test_feat054_access.py`

```python
"""Tests for FEAT-05.4 -- Access Relationship and AccessMode enum."""
from __future__ import annotations

from typing import ClassVar

import pytest

from pyarchi.enums import AccessMode, Aspect, Layer, RelationshipCategory
from pyarchi.metamodel.elements import ActiveStructureElement
from pyarchi.metamodel.relationships import Access, DependencyRelationship


# ---------------------------------------------------------------------------
# Test-local concrete element stub
# ---------------------------------------------------------------------------


class _ConcreteElement(ActiveStructureElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE

    @property
    def _type_name(self) -> str:
        return "Stub"


# ---------------------------------------------------------------------------
# AccessMode enum ratification
# ---------------------------------------------------------------------------


class TestAccessModeEnum:
    def test_read(self) -> None:
        assert AccessMode.READ.value == "Read"

    def test_write(self) -> None:
        assert AccessMode.WRITE.value == "Write"

    def test_read_write(self) -> None:
        assert AccessMode.READ_WRITE.value == "ReadWrite"

    def test_unspecified(self) -> None:
        assert AccessMode.UNSPECIFIED.value == "Unspecified"

    def test_exactly_four_members(self) -> None:
        assert len(AccessMode) == 4


# ---------------------------------------------------------------------------
# Access relationship
# ---------------------------------------------------------------------------


class TestAccess:
    @pytest.fixture()
    def pair(self) -> tuple[_ConcreteElement, _ConcreteElement]:
        return _ConcreteElement(name="a"), _ConcreteElement(name="b")

    def test_instantiation(self, pair: tuple[_ConcreteElement, _ConcreteElement]) -> None:
        a, b = pair
        r = Access(name="acc", source=a, target=b)
        assert r._type_name == "Access"

    def test_access_mode_defaults_to_unspecified(
        self, pair: tuple[_ConcreteElement, _ConcreteElement]
    ) -> None:
        a, b = pair
        r = Access(name="acc", source=a, target=b)
        assert r.access_mode is AccessMode.UNSPECIFIED

    @pytest.mark.parametrize("mode", list(AccessMode))
    def test_accepts_all_access_modes(
        self,
        pair: tuple[_ConcreteElement, _ConcreteElement],
        mode: AccessMode,
    ) -> None:
        a, b = pair
        r = Access(name="acc", source=a, target=b, access_mode=mode)
        assert r.access_mode is mode

    def test_is_dependency_relationship(self) -> None:
        assert issubclass(Access, DependencyRelationship)

    def test_category_inherited(self) -> None:
        assert Access.category is RelationshipCategory.DEPENDENCY

    def test_invalid_access_mode_raises(
        self, pair: tuple[_ConcreteElement, _ConcreteElement]
    ) -> None:
        a, b = pair
        with pytest.raises(Exception):
            Access(name="acc", source=a, target=b, access_mode="invalid")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Validation xfails
# ---------------------------------------------------------------------------


class TestDeferredValidation:
    @pytest.mark.xfail(
        strict=False,
        reason="Access direction validation deferred to model-level (ADR-017 ss6)",
    )
    def test_access_wrong_direction_raises(self) -> None:
        pytest.fail("Model-level validation not yet implemented")
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/relationships.py test/test_feat054_access.py
ruff format --check src/pyarchi/metamodel/relationships.py test/test_feat054_access.py
mypy src/pyarchi/metamodel/relationships.py test/test_feat054_access.py
pytest test/test_feat054_access.py -v
pytest  # full suite, no regressions
```
