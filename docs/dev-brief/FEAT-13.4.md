# Technical Brief: FEAT-13.4 Cross-Layer Realization Prohibitions

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-025-epic013-cross-layer-rules.md`
**Epic:** EPIC-013

---

## Feature Summary

Add a prohibition rule in `is_permitted()` that rejects Realization targeting `BusinessInternalActiveStructureElement` (covers `BusinessActor`, `BusinessRole`, `BusinessCollaboration`). **This feature MUST be implemented before FEAT-13.3** because the prohibition block must appear above the broader Realization permission rules in `is_permitted()`. No changes to element classes.

## Dependencies

| Dependency | Status |
|---|---|
| EPIC-007 (`BusinessInternalActiveStructureElement` ABC) | Done |
| EPIC-008 (Application layer elements) | Done |
| EPIC-005 (`permissions.py`, `Realization`) | Done |
| ADR-025 Decision 7 | Accepted |

## Stories -> Acceptance

| Story | Rule | Acceptance |
|---|---|---|
| 13.4.1 | `Realization` targeting `BusinessInternalActiveStructureElement` returns `False` | Single `issubclass` check |
| 13.4.2 | Test | `is_permitted(Realization, ApplicationProcess, BusinessActor)` returns `False` |
| 13.4.3 | Test | `is_permitted(Realization, ApplicationComponent, BusinessRole)` returns `False` |
| 13.4.4 | Test | `is_permitted(Realization, ApplicationComponent, BusinessCollaboration)` returns `False` |

## Implementation

### Changes to `src/pyarchi/validation/permissions.py`

Insert a single prohibition check within the `if rel_type is Realization:` block, **after** the existing Deliverable rules and **before** any FEAT-13.3 permission rules.

**Prohibition rule (1 check):**

```python
# FEAT-13.4: Realization targeting Business active structure is forbidden.
from pyarchi.metamodel.business import BusinessInternalActiveStructureElement
if issubclass(target_type, BusinessInternalActiveStructureElement):
    return False
```

This single `issubclass` check covers all three prohibited targets (`BusinessActor`, `BusinessRole`, `BusinessCollaboration`) plus any future subclasses of `BusinessInternalActiveStructureElement`.

**Insertion point:** Inside the existing `if rel_type is Realization:` block, after the `Deliverable` rules (lines ~119-122), before the triple lookup fallthrough. The `BusinessInternalActiveStructureElement` import already exists (used by Assignment rules) -- reuse it.

**Code ordering within the Realization block after FEAT-13.4:**

```
1. Existing: Realization(WorkPackage, Deliverable) -- DeprecationWarning
2. Existing: Deliverable realizes core
3. NEW: prohibition -- target is BusinessInternalActiveStructureElement -> return False
4. (future FEAT-13.3 permission rules go here)
```

## Test File: `test/test_feat134_realization_prohibitions.py`

```python
"""Tests for FEAT-13.4 -- Cross-layer Realization prohibition rules."""
from __future__ import annotations

import pytest

from pyarchi.metamodel.application import (
    ApplicationComponent,
    ApplicationFunction,
    ApplicationProcess,
    DataObject,
)
from pyarchi.metamodel.business import (
    BusinessActor,
    BusinessCollaboration,
    BusinessRole,
)
from pyarchi.metamodel.technology import (
    Artifact,
    TechnologyProcess,
)
from pyarchi.metamodel.relationships import Realization
from pyarchi.validation.permissions import is_permitted


class TestRealizationProhibitedTargets:
    """Realization targeting BusinessInternalActiveStructureElement is forbidden."""

    @pytest.mark.parametrize(
        ("source", "target"),
        [
            (ApplicationProcess, BusinessActor),
            (ApplicationFunction, BusinessActor),
            (ApplicationComponent, BusinessRole),
            (ApplicationComponent, BusinessCollaboration),
            (DataObject, BusinessActor),
            (DataObject, BusinessRole),
            (Artifact, BusinessActor),
            (TechnologyProcess, BusinessRole),
        ],
    )
    def test_prohibited(self, source: type, target: type) -> None:
        assert is_permitted(Realization, source, target) is False
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/validation/permissions.py test/test_feat134_realization_prohibitions.py
ruff format --check src/pyarchi/validation/permissions.py test/test_feat134_realization_prohibitions.py
mypy src/pyarchi/validation/permissions.py test/test_feat134_realization_prohibitions.py
pytest test/test_feat134_realization_prohibitions.py -v
pytest  # full suite, no regressions
```
