# Technical Brief: FEAT-12.4 Implementation & Migration Cross-Layer Validation

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-024-epic012-implementation-migration.md`
**Epic:** EPIC-012

---

## Feature Summary

Add cross-layer permission rules to `src/pyarchi/validation/permissions.py` for Implementation and Migration elements. Emit `DeprecationWarning` when `Realization(WorkPackage, Deliverable)` is checked. Add rule-based `is_permitted` entries for Assignment, Triggering, and Access involving I&M types. No changes to element classes.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-12.1, 12.2, 12.3 (all five I&M concrete classes) | Must be done first |
| EPIC-005 (`permissions.py`, `is_permitted()`) | Done |
| EPIC-005 (`Assignment`, `Realization`, `Triggering`, `Access`) | Done |
| EPIC-007 (`BusinessRole`, `BusinessActor`, `BusinessCollaboration`) | Done |
| ADR-024 Decision 9 | Accepted |

## Stories -> Acceptance

| Story | Rule | Acceptance |
|---|---|---|
| 12.4.1 | `Realization(WorkPackage, Deliverable)` | Returns `True` but emits `DeprecationWarning` |
| 12.4.2 | Assignment to `WorkPackage` | `BusinessActor`, `BusinessRole`, `BusinessCollaboration` permitted as source |
| 12.4.3 | Triggering with `ImplementationEvent` | `ImplementationEvent` may trigger `WorkPackage` or `Plateau` |
| 12.4.4 | Access to `Deliverable` | `ImplementationEvent` may access `Deliverable` |
| 12.4.5 | Deliverable realizes core | `Deliverable` may realize any core concept |
| 12.4.6 | Test | `Realization(WorkPackage, Deliverable)` emits `DeprecationWarning` |
| 12.4.7 | Test | `Assignment(BusinessRole, WorkPackage)` is `True` |
| 12.4.8 | Test | `Triggering(ImplementationEvent, WorkPackage)` is `True` |

## Implementation

### Changes to `src/pyarchi/validation/permissions.py`

Add rule-based checks in `is_permitted()` **before** the triple lookup, following the existing pattern for Motivation rules. The new rules use `issubclass` checks against I&M types via lazy imports.

**Pseudocode insertion points** (after the existing Influence block, before the triple lookup):

```python
import warnings

from pyarchi.metamodel.implementation_migration import (
    Deliverable,
    Gap,
    ImplementationEvent,
    Plateau,
    WorkPackage,
)

# 1. DeprecationWarning on Realization(WorkPackage, Deliverable)
if rel_type is Realization:
    if issubclass(source_type, WorkPackage) and issubclass(target_type, Deliverable):
        warnings.warn(
            "Realization from WorkPackage to Deliverable is deprecated in "
            "ArchiMate 3.2. Use Assignment instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return True

# 2. Assignment to WorkPackage -- Business internal active structure sources
if rel_type is Assignment and issubclass(target_type, WorkPackage):
    from pyarchi.metamodel.business import BusinessInternalActiveStructureElement
    return issubclass(source_type, BusinessInternalActiveStructureElement)

# 3. Triggering: ImplementationEvent <-> WorkPackage, Plateau
if rel_type is Triggering:
    if issubclass(source_type, ImplementationEvent) and issubclass(
        target_type, (WorkPackage, Plateau)
    ):
        return True
    if issubclass(source_type, (WorkPackage, Plateau)) and issubclass(
        target_type, ImplementationEvent
    ):
        return True

# 4. Access: ImplementationEvent -> Deliverable
if rel_type is Access and issubclass(source_type, ImplementationEvent):
    if issubclass(target_type, Deliverable):
        return True

# 5. Realization: Deliverable realizes any StructureElement or BehaviorElement
if rel_type is Realization and issubclass(source_type, Deliverable):
    if issubclass(target_type, (StructureElement, BehaviorElement)):
        return True
```

**Import additions at top of file:**

```python
from pyarchi.metamodel.relationships import (
    ...
    Access,
    Triggering,
)
```

Use lazy imports inside the function body for I&M types to avoid circular imports, matching the existing `BusinessInternalActiveStructureElement` pattern.

## Test File: `test/test_feat124_impl_cross_layer.py`

```python
"""Tests for FEAT-12.4 -- Implementation & Migration cross-layer validation rules."""
from __future__ import annotations

import warnings

import pytest

from pyarchi.metamodel.business import (
    BusinessActor,
    BusinessCollaboration,
    BusinessRole,
)
from pyarchi.metamodel.implementation_migration import (
    Deliverable,
    ImplementationEvent,
    Plateau,
    WorkPackage,
)
from pyarchi.metamodel.relationships import (
    Access,
    Assignment,
    Realization,
    Triggering,
)
from pyarchi.validation.permissions import is_permitted


class TestRealizationDeprecation:
    """Realization(WorkPackage, Deliverable) is permitted but deprecated."""

    def test_returns_true(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            assert is_permitted(Realization, WorkPackage, Deliverable) is True

    def test_emits_deprecation_warning(self) -> None:
        with pytest.warns(DeprecationWarning, match="deprecated"):
            is_permitted(Realization, WorkPackage, Deliverable)


class TestAssignmentToWorkPackage:
    """Business internal active structure sources may assign to WorkPackage."""

    @pytest.mark.parametrize(
        "source_type",
        [BusinessActor, BusinessRole, BusinessCollaboration],
    )
    def test_permitted_sources(self, source_type: type) -> None:
        assert is_permitted(Assignment, source_type, WorkPackage) is True

    @pytest.mark.parametrize(
        "source_type",
        [Deliverable, ImplementationEvent, Plateau],
    )
    def test_forbidden_sources(self, source_type: type) -> None:
        assert is_permitted(Assignment, source_type, WorkPackage) is False


class TestTriggering:
    """ImplementationEvent may trigger/be triggered by WorkPackage or Plateau."""

    @pytest.mark.parametrize(
        ("source", "target"),
        [
            (ImplementationEvent, WorkPackage),
            (ImplementationEvent, Plateau),
            (WorkPackage, ImplementationEvent),
            (Plateau, ImplementationEvent),
        ],
    )
    def test_permitted_triggering(self, source: type, target: type) -> None:
        assert is_permitted(Triggering, source, target) is True


class TestAccess:
    """ImplementationEvent may access Deliverable."""

    def test_impl_event_accesses_deliverable(self) -> None:
        assert is_permitted(Access, ImplementationEvent, Deliverable) is True


class TestDeliverableRealization:
    """Deliverable may realize core structure/behavior elements."""

    def test_deliverable_realizes_work_package(self) -> None:
        assert is_permitted(Realization, Deliverable, WorkPackage) is True
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/validation/permissions.py test/test_feat124_impl_cross_layer.py
ruff format --check src/pyarchi/validation/permissions.py test/test_feat124_impl_cross_layer.py
mypy src/pyarchi/validation/permissions.py test/test_feat124_impl_cross_layer.py
pytest test/test_feat124_impl_cross_layer.py -v
pytest  # full suite, no regressions
```
