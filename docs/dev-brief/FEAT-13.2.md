# Technical Brief: FEAT-13.2 Application--Technology Cross-Layer Serving

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-025-epic013-cross-layer-rules.md`
**Epic:** EPIC-013

---

## Feature Summary

Add rule-based `is_permitted()` checks for Serving from Technology layer to Application layer (one direction only). No changes to element classes.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-13.1 (Business-Application Serving block exists) | Must be done first |
| EPIC-008 (Application layer elements) | Done |
| EPIC-009 (Technology layer elements) | Done |
| EPIC-005 (`permissions.py`, `Serving`) | Done |
| ADR-025 Decision 5 | Accepted |

## Stories -> Acceptance

| Story | Rule | Acceptance |
|---|---|---|
| 13.2.1 | `Serving` from `TechnologyService` to `ApplicationInternalBehaviorElement` | `is_permitted(Serving, TechnologyService, ApplicationFunction)` returns `True` |
| 13.2.2 | `Serving` from `TechnologyInterface` to `ApplicationInternalActiveStructureElement` | `is_permitted(Serving, TechnologyInterface, ApplicationComponent)` returns `True` |
| 13.2.3 | Test permitted + forbidden | Parametrized |

## Implementation

### Changes to `src/pyarchi/validation/permissions.py`

Extend the `if rel_type is Serving:` block added in FEAT-13.1 with two additional checks for Technology -> Application direction.

**Permission rules:**

| Source Type (concrete) | Target ABC |
|---|---|
| `TechnologyService` | `ApplicationInternalBehaviorElement` |
| `TechnologyInterface` | `ApplicationInternalActiveStructureElement` |

**Additional imports (lazy, inside function body):**

```python
from pyarchi.metamodel.technology import TechnologyInterface, TechnologyService
```

**Insertion point:** Immediately after the FEAT-13.1 Serving checks, within the same `if rel_type is Serving:` block.

## Test File: `test/test_feat132_app_tech_serving.py`

```python
"""Tests for FEAT-13.2 -- Application-Technology cross-layer Serving rules."""
from __future__ import annotations

import pytest

from pyarchi.metamodel.application import (
    ApplicationComponent,
    ApplicationFunction,
    ApplicationProcess,
)
from pyarchi.metamodel.technology import (
    Artifact,
    Node,
    TechnologyFunction,
    TechnologyInterface,
    TechnologyProcess,
    TechnologyService,
)
from pyarchi.metamodel.relationships import Serving
from pyarchi.validation.permissions import is_permitted


class TestTechnologyServingApplication:
    """Technology external elements serve Application internal elements."""

    @pytest.mark.parametrize(
        ("source", "target"),
        [
            (TechnologyService, ApplicationFunction),
            (TechnologyService, ApplicationProcess),
            (TechnologyInterface, ApplicationComponent),
        ],
    )
    def test_permitted(self, source: type, target: type) -> None:
        assert is_permitted(Serving, source, target) is True


class TestTechServingAppForbidden:
    """Non-service/interface Technology types cannot Serve Application."""

    @pytest.mark.parametrize(
        ("source", "target"),
        [
            (TechnologyProcess, ApplicationFunction),
            (Node, ApplicationComponent),
            (Artifact, ApplicationComponent),
            (TechnologyFunction, ApplicationProcess),
        ],
    )
    def test_forbidden(self, source: type, target: type) -> None:
        assert is_permitted(Serving, source, target) is False
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/validation/permissions.py test/test_feat132_app_tech_serving.py
ruff format --check src/pyarchi/validation/permissions.py test/test_feat132_app_tech_serving.py
mypy src/pyarchi/validation/permissions.py test/test_feat132_app_tech_serving.py
pytest test/test_feat132_app_tech_serving.py -v
pytest  # full suite, no regressions
```
