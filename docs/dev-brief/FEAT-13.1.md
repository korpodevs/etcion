# Technical Brief: FEAT-13.1 Business--Application Cross-Layer Serving

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-025-epic013-cross-layer-rules.md`
**Epic:** EPIC-013

---

## Feature Summary

Add rule-based `is_permitted()` checks for bidirectional Serving between Business and Application layers. No changes to element classes.

## Dependencies

| Dependency | Status |
|---|---|
| EPIC-007 (Business layer elements) | Done |
| EPIC-008 (Application layer elements) | Done |
| EPIC-005 (`permissions.py`, `is_permitted()`, `Serving`) | Done |
| ADR-025 Decision 4 | Accepted |

## Stories -> Acceptance

| Story | Rule | Acceptance |
|---|---|---|
| 13.1.1 | `Serving` from `ApplicationService` to `BusinessInternalBehaviorElement` | `is_permitted(Serving, ApplicationService, BusinessProcess)` returns `True` |
| 13.1.2 | `Serving` from `ApplicationInterface` to `BusinessInternalActiveStructureElement` | `is_permitted(Serving, ApplicationInterface, BusinessRole)` returns `True` |
| 13.1.3 | `Serving` from `BusinessService` to `ApplicationInternalBehaviorElement` | `is_permitted(Serving, BusinessService, ApplicationFunction)` returns `True` |
| 13.1.4 | `Serving` from `BusinessInterface` to `ApplicationInternalActiveStructureElement` | `is_permitted(Serving, BusinessInterface, ApplicationComponent)` returns `True` |
| 13.1.5 | Test permitted | Parametrized across all valid pairs |
| 13.1.6 | Test forbidden | Cross-layer Serving from non-service/interface types returns `False` |

## Implementation

### Changes to `src/pyarchi/validation/permissions.py`

Insert a new rule block **after** the I&M rules, **before** the triple lookup. Uses concrete types (not ABC + layer ClassVar) per ADR-025 Decision 4.

**Permission rules (4 checks under `if rel_type is Serving:`):**

| Source Type (concrete) | Target ABC | Direction |
|---|---|---|
| `ApplicationService` | `BusinessInternalBehaviorElement` | App -> Business |
| `ApplicationInterface` | `BusinessInternalActiveStructureElement` | App -> Business |
| `BusinessService` | `ApplicationInternalBehaviorElement` | Business -> App |
| `BusinessInterface` | `ApplicationInternalActiveStructureElement` | Business -> App |

**Imports to add (lazy, inside function body):**

```python
from pyarchi.metamodel.application import ApplicationInterface, ApplicationService
from pyarchi.metamodel.application import ApplicationInternalActiveStructureElement, ApplicationInternalBehaviorElement
from pyarchi.metamodel.business import BusinessInterface, BusinessService
from pyarchi.metamodel.business import BusinessInternalActiveStructureElement, BusinessInternalBehaviorElement
```

**Insertion point:** After the `Access: ImplementationEvent -> Deliverable` block, before `return (rel_type, source_type, target_type) in _PERMITTED_TRIPLES`.

## Test File: `test/test_feat131_biz_app_serving.py`

```python
"""Tests for FEAT-13.1 -- Business-Application cross-layer Serving rules."""
from __future__ import annotations

import pytest

from pyarchi.metamodel.application import (
    ApplicationComponent,
    ApplicationFunction,
    ApplicationInterface,
    ApplicationProcess,
    ApplicationService,
)
from pyarchi.metamodel.business import (
    BusinessActor,
    BusinessFunction,
    BusinessInterface,
    BusinessInteraction,
    BusinessProcess,
    BusinessRole,
    BusinessService,
)
from pyarchi.metamodel.relationships import Serving
from pyarchi.validation.permissions import is_permitted


class TestApplicationServingBusiness:
    """Application external elements serve Business internal elements."""

    @pytest.mark.parametrize(
        ("source", "target"),
        [
            (ApplicationService, BusinessProcess),
            (ApplicationService, BusinessFunction),
            (ApplicationService, BusinessInteraction),
            (ApplicationInterface, BusinessActor),
            (ApplicationInterface, BusinessRole),
        ],
    )
    def test_permitted(self, source: type, target: type) -> None:
        assert is_permitted(Serving, source, target) is True


class TestBusinessServingApplication:
    """Business external elements serve Application internal elements."""

    @pytest.mark.parametrize(
        ("source", "target"),
        [
            (BusinessService, ApplicationProcess),
            (BusinessService, ApplicationFunction),
            (BusinessInterface, ApplicationComponent),
        ],
    )
    def test_permitted(self, source: type, target: type) -> None:
        assert is_permitted(Serving, source, target) is True


class TestCrossLayerServingForbidden:
    """Non-service/interface types cannot Serve cross-layer."""

    @pytest.mark.parametrize(
        ("source", "target"),
        [
            (BusinessProcess, ApplicationFunction),
            (ApplicationProcess, BusinessFunction),
            (BusinessActor, ApplicationComponent),
            (ApplicationComponent, BusinessRole),
        ],
    )
    def test_forbidden(self, source: type, target: type) -> None:
        assert is_permitted(Serving, source, target) is False
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/validation/permissions.py test/test_feat131_biz_app_serving.py
ruff format --check src/pyarchi/validation/permissions.py test/test_feat131_biz_app_serving.py
mypy src/pyarchi/validation/permissions.py test/test_feat131_biz_app_serving.py
pytest test/test_feat131_biz_app_serving.py -v
pytest  # full suite, no regressions
```
