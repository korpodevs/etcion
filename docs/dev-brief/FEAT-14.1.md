# Technical Brief: FEAT-14.1 -- Phase 2 Public API Exports

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-026-epic014-public-api-exports.md`
**Epic:** EPIC-014
**Backlog:** STORY-14.1.1 through STORY-14.1.10

---

## Scope

Modify `src/pyarchi/__init__.py` to re-export all Phase 2 types. Add a parametrized test. No new modules.

## Import Blocks to Add

Append after the existing `from pyarchi.validation.permissions import is_permitted` line:

```python
# Phase 2: Strategy layer (EPIC-006)
from pyarchi.metamodel.strategy import (
    StrategyBehaviorElement,
    StrategyStructureElement,
    Capability,
    CourseOfAction,
    Resource,
    ValueStream,
)
# Phase 2: Business layer (EPIC-007)
from pyarchi.metamodel.business import (
    BusinessInternalActiveStructureElement,
    BusinessInternalBehaviorElement,
    BusinessPassiveStructureElement,
    BusinessActor,
    BusinessCollaboration,
    BusinessEvent,
    BusinessFunction,
    BusinessInteraction,
    BusinessInterface,
    BusinessObject,
    BusinessProcess,
    BusinessRole,
    BusinessService,
    Contract,
    Product,
    Representation,
)
# Phase 2: Application layer (EPIC-008)
from pyarchi.metamodel.application import (
    ApplicationInternalActiveStructureElement,
    ApplicationInternalBehaviorElement,
    ApplicationCollaboration,
    ApplicationComponent,
    ApplicationEvent,
    ApplicationFunction,
    ApplicationInteraction,
    ApplicationInterface,
    ApplicationProcess,
    ApplicationService,
    DataObject,
)
# Phase 2: Technology layer (EPIC-009)
from pyarchi.metamodel.technology import (
    TechnologyInternalActiveStructureElement,
    TechnologyInternalBehaviorElement,
    Artifact,
    CommunicationNetwork,
    Device,
    Node,
    Path,
    SystemSoftware,
    TechnologyCollaboration,
    TechnologyEvent,
    TechnologyFunction,
    TechnologyInteraction,
    TechnologyInterface,
    TechnologyProcess,
    TechnologyService,
)
# Phase 2: Physical layer (EPIC-010)
from pyarchi.metamodel.physical import (
    PhysicalActiveStructureElement,
    PhysicalPassiveStructureElement,
    DistributionNetwork,
    Equipment,
    Facility,
    Material,
)
# Phase 2: Motivation layer (EPIC-011)
from pyarchi.metamodel.motivation import (
    Assessment,
    Constraint,
    Driver,
    Goal,
    Meaning,
    Outcome,
    Principle,
    Requirement,
    Stakeholder,
    Value,
)
# Phase 2: Implementation & Migration layer (EPIC-012)
from pyarchi.metamodel.implementation_migration import (
    Deliverable,
    Gap,
    ImplementationEvent,
    Plateau,
    WorkPackage,
)
```

## Names to Append to `__all__`

Append after the existing `"is_permitted",` entry, preserving the closing `]`:

```python
    # Strategy layer (EPIC-006)
    "StrategyStructureElement",
    "StrategyBehaviorElement",
    "Resource",
    "Capability",
    "ValueStream",
    "CourseOfAction",
    # Business layer (EPIC-007)
    "BusinessInternalActiveStructureElement",
    "BusinessInternalBehaviorElement",
    "BusinessPassiveStructureElement",
    "BusinessActor",
    "BusinessRole",
    "BusinessCollaboration",
    "BusinessInterface",
    "BusinessProcess",
    "BusinessFunction",
    "BusinessInteraction",
    "BusinessEvent",
    "BusinessService",
    "BusinessObject",
    "Contract",
    "Representation",
    "Product",
    # Application layer (EPIC-008)
    "ApplicationInternalActiveStructureElement",
    "ApplicationInternalBehaviorElement",
    "ApplicationComponent",
    "ApplicationCollaboration",
    "ApplicationInterface",
    "ApplicationFunction",
    "ApplicationInteraction",
    "ApplicationProcess",
    "ApplicationEvent",
    "ApplicationService",
    "DataObject",
    # Technology layer (EPIC-009)
    "TechnologyInternalActiveStructureElement",
    "TechnologyInternalBehaviorElement",
    "Node",
    "Device",
    "SystemSoftware",
    "TechnologyCollaboration",
    "TechnologyInterface",
    "Path",
    "CommunicationNetwork",
    "TechnologyFunction",
    "TechnologyProcess",
    "TechnologyInteraction",
    "TechnologyEvent",
    "TechnologyService",
    "Artifact",
    # Physical layer (EPIC-010)
    "PhysicalActiveStructureElement",
    "PhysicalPassiveStructureElement",
    "Equipment",
    "Facility",
    "DistributionNetwork",
    "Material",
    # Motivation layer (EPIC-011)
    "Stakeholder",
    "Driver",
    "Assessment",
    "Goal",
    "Outcome",
    "Principle",
    "Requirement",
    "Constraint",
    "Meaning",
    "Value",
    # Implementation & Migration layer (EPIC-012)
    "WorkPackage",
    "Deliverable",
    "ImplementationEvent",
    "Plateau",
    "Gap",
```

## Phase 2 Type Count

| Layer | ABCs | Concrete | Subtotal |
|---|---|---|---|
| Strategy | 2 | 4 | 6 |
| Business | 3 | 13 | 16 |
| Application | 2 | 9 | 11 |
| Technology | 2 | 13 | 15 |
| Physical | 2 | 4 | 6 |
| Motivation | 0 | 10 | 10 |
| Impl & Migration | 0 | 5 | 5 |
| **Total** | **11** | **58** | **69** |

## Test File: `test/test_feat141_phase2_exports.py`

```python
"""Tests for FEAT-14.1 -- Phase 2 public API exports."""
from __future__ import annotations

import pytest


_PHASE2_TYPES: list[str] = [
    # Strategy layer (EPIC-006)
    "StrategyStructureElement",
    "StrategyBehaviorElement",
    "Resource",
    "Capability",
    "ValueStream",
    "CourseOfAction",
    # Business layer (EPIC-007)
    "BusinessInternalActiveStructureElement",
    "BusinessInternalBehaviorElement",
    "BusinessPassiveStructureElement",
    "BusinessActor",
    "BusinessRole",
    "BusinessCollaboration",
    "BusinessInterface",
    "BusinessProcess",
    "BusinessFunction",
    "BusinessInteraction",
    "BusinessEvent",
    "BusinessService",
    "BusinessObject",
    "Contract",
    "Representation",
    "Product",
    # Application layer (EPIC-008)
    "ApplicationInternalActiveStructureElement",
    "ApplicationInternalBehaviorElement",
    "ApplicationComponent",
    "ApplicationCollaboration",
    "ApplicationInterface",
    "ApplicationFunction",
    "ApplicationInteraction",
    "ApplicationProcess",
    "ApplicationEvent",
    "ApplicationService",
    "DataObject",
    # Technology layer (EPIC-009)
    "TechnologyInternalActiveStructureElement",
    "TechnologyInternalBehaviorElement",
    "Node",
    "Device",
    "SystemSoftware",
    "TechnologyCollaboration",
    "TechnologyInterface",
    "Path",
    "CommunicationNetwork",
    "TechnologyFunction",
    "TechnologyProcess",
    "TechnologyInteraction",
    "TechnologyEvent",
    "TechnologyService",
    "Artifact",
    # Physical layer (EPIC-010)
    "PhysicalActiveStructureElement",
    "PhysicalPassiveStructureElement",
    "Equipment",
    "Facility",
    "DistributionNetwork",
    "Material",
    # Motivation layer (EPIC-011)
    "Stakeholder",
    "Driver",
    "Assessment",
    "Goal",
    "Outcome",
    "Principle",
    "Requirement",
    "Constraint",
    "Meaning",
    "Value",
    # Implementation & Migration layer (EPIC-012)
    "WorkPackage",
    "Deliverable",
    "ImplementationEvent",
    "Plateau",
    "Gap",
]


class TestPhase2Exports:
    @pytest.mark.parametrize("name", _PHASE2_TYPES)
    def test_public_api_export(self, name: str) -> None:
        import pyarchi

        attr = getattr(pyarchi, name, None)
        assert attr is not None, f"{name} not exported from pyarchi"

    @pytest.mark.parametrize("name", _PHASE2_TYPES)
    def test_in_all(self, name: str) -> None:
        import pyarchi

        assert name in pyarchi.__all__, f"{name} missing from pyarchi.__all__"

    def test_phase2_count(self) -> None:
        assert len(_PHASE2_TYPES) == 69
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/__init__.py test/test_feat141_phase2_exports.py
ruff format --check src/pyarchi/__init__.py test/test_feat141_phase2_exports.py
mypy src/pyarchi/__init__.py test/test_feat141_phase2_exports.py
pytest test/test_feat141_phase2_exports.py -v
pytest  # full suite, no regressions
```
