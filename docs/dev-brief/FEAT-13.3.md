# Technical Brief: FEAT-13.3 Cross-Layer Realization Permissions

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-025-epic013-cross-layer-rules.md`
**Epic:** EPIC-013

---

## Feature Summary

Add rule-based `is_permitted()` checks for cross-layer Realization (lower layer realizes upper layer). **FEAT-13.4 (prohibitions) MUST be implemented before this feature** -- the prohibition block must appear above the permission block in `is_permitted()` so that prohibited targets are rejected before the broader ABC rules match. No changes to element classes.

## Dependencies

| Dependency | Status |
|---|---|
| **FEAT-13.4 (Realization prohibitions)** | **Must be done first** |
| EPIC-007 (Business layer elements) | Done |
| EPIC-008 (Application layer elements) | Done |
| EPIC-009 (Technology layer elements) | Done |
| EPIC-005 (`permissions.py`, `Realization`) | Done |
| ADR-025 Decision 6 | Accepted |

## Stories -> Acceptance

| Story | Rule | Acceptance |
|---|---|---|
| 13.3.1 | `Realization` from `ApplicationInternalBehaviorElement` to `BusinessInternalBehaviorElement` | `is_permitted(Realization, ApplicationProcess, BusinessProcess)` returns `True` |
| 13.3.2 | `Realization` from `DataObject` to `BusinessObject` | `is_permitted(Realization, DataObject, BusinessObject)` returns `True` |
| 13.3.3 | `Realization` from `TechnologyInternalBehaviorElement` to `ApplicationInternalBehaviorElement` | `is_permitted(Realization, TechnologyProcess, ApplicationProcess)` returns `True` |
| 13.3.4 | `Realization` from `Artifact` to `DataObject` | `is_permitted(Realization, Artifact, DataObject)` returns `True` |
| 13.3.5 | `Realization` from `Artifact` to `ApplicationComponent` | `is_permitted(Realization, Artifact, ApplicationComponent)` returns `True` |
| 13.3.6 | Test forbidden -- skip layer | `is_permitted(Realization, TechnologyProcess, BusinessProcess)` returns `False` |

## Implementation

### Changes to `src/pyarchi/validation/permissions.py`

Extend the existing `if rel_type is Realization:` block. Insert **after** the FEAT-13.4 prohibition check and **after** the existing Deliverable/WorkPackage rules.

**Permission rules (5 `issubclass` checks):**

| Source ABC/Class | Target ABC/Class | Semantic |
|---|---|---|
| `ApplicationInternalBehaviorElement` | `BusinessInternalBehaviorElement` | App behavior -> Business behavior |
| `DataObject` | `BusinessObject` | App data -> Business object |
| `TechnologyInternalBehaviorElement` | `ApplicationInternalBehaviorElement` | Tech behavior -> App behavior |
| `Artifact` | `DataObject` | Tech artifact -> App data |
| `Artifact` | `ApplicationComponent` | Tech artifact -> App component |

**Imports to add (lazy, inside function body):**

```python
from pyarchi.metamodel.application import (
    ApplicationComponent,
    ApplicationInternalBehaviorElement,
    DataObject,
)
from pyarchi.metamodel.business import (
    BusinessInternalBehaviorElement,
    BusinessObject,
)
from pyarchi.metamodel.technology import (
    Artifact,
    TechnologyInternalBehaviorElement,
)
```

**Ordering within `is_permitted()`** (the Realization block after FEAT-13.3+13.4):

```
1. Existing: Realization(WorkPackage, Deliverable) -- DeprecationWarning
2. Existing: Deliverable realizes core
3. FEAT-13.4: prohibition -- target is BusinessInternalActiveStructureElement -> False
4. FEAT-13.3: permission -- five issubclass rules -> True
```

## Test File: `test/test_feat133_cross_layer_realization.py`

```python
"""Tests for FEAT-13.3 -- Cross-layer Realization permission rules."""
from __future__ import annotations

import pytest

from pyarchi.metamodel.application import (
    ApplicationComponent,
    ApplicationFunction,
    ApplicationInteraction,
    ApplicationProcess,
    DataObject,
)
from pyarchi.metamodel.business import (
    BusinessFunction,
    BusinessInteraction,
    BusinessObject,
    BusinessProcess,
    Contract,
)
from pyarchi.metamodel.technology import (
    Artifact,
    TechnologyFunction,
    TechnologyProcess,
)
from pyarchi.metamodel.relationships import Realization
from pyarchi.validation.permissions import is_permitted


class TestAppRealizesBusinessBehavior:
    """Application behavior elements realize Business behavior elements."""

    @pytest.mark.parametrize(
        ("source", "target"),
        [
            (ApplicationProcess, BusinessProcess),
            (ApplicationFunction, BusinessFunction),
            (ApplicationInteraction, BusinessInteraction),
            (ApplicationProcess, BusinessFunction),
            (ApplicationFunction, BusinessProcess),
        ],
    )
    def test_permitted(self, source: type, target: type) -> None:
        assert is_permitted(Realization, source, target) is True


class TestDataObjectRealizesBusinessObject:
    """DataObject realizes BusinessObject (and subclasses)."""

    @pytest.mark.parametrize("target", [BusinessObject, Contract])
    def test_permitted(self, target: type) -> None:
        assert is_permitted(Realization, DataObject, target) is True


class TestTechRealizesAppBehavior:
    """Technology behavior elements realize Application behavior elements."""

    @pytest.mark.parametrize(
        ("source", "target"),
        [
            (TechnologyProcess, ApplicationProcess),
            (TechnologyFunction, ApplicationFunction),
            (TechnologyProcess, ApplicationFunction),
        ],
    )
    def test_permitted(self, source: type, target: type) -> None:
        assert is_permitted(Realization, source, target) is True


class TestArtifactRealizesAppElements:
    """Artifact realizes DataObject and ApplicationComponent."""

    @pytest.mark.parametrize(
        "target", [DataObject, ApplicationComponent],
    )
    def test_permitted(self, target: type) -> None:
        assert is_permitted(Realization, Artifact, target) is True


class TestCrossLayerRealizationForbidden:
    """Realization that skips a layer or goes wrong direction is forbidden."""

    @pytest.mark.parametrize(
        ("source", "target"),
        [
            (TechnologyProcess, BusinessProcess),
            (Artifact, BusinessObject),
            (BusinessProcess, ApplicationProcess),
        ],
    )
    def test_forbidden(self, source: type, target: type) -> None:
        assert is_permitted(Realization, source, target) is False
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/validation/permissions.py test/test_feat133_cross_layer_realization.py
ruff format --check src/pyarchi/validation/permissions.py test/test_feat133_cross_layer_realization.py
mypy src/pyarchi/validation/permissions.py test/test_feat133_cross_layer_realization.py
pytest test/test_feat133_cross_layer_realization.py -v
pytest  # full suite, no regressions
```
