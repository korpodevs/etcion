# Technical Brief: FEAT-16.3 -- Permission Table Completeness Audit

**Status:** Ready for TDD (depends on FEAT-16.1, FEAT-16.2)
**ADR:** `docs/adr/ADR-028-epic016-declarative-permissions.md` (Decision 6)
**Backlog:** STORY-16.3.1, STORY-16.3.2, STORY-16.3.3

## Scope

Parametrized tests that systematically verify `is_permitted()` against Appendix B for representative concrete type pairs. Three test classes:

1. **Positive audit** -- every permitted concrete pair returns `True`
2. **Negative audit** -- every explicitly prohibited pair returns `False`
3. **Default-deny** -- triples not in the table and not covered by universal rules return `False`

No production code changes. This feature is test-only.

## Concrete Type Universe

All concrete element types in the library, grouped by layer:

| Layer | Concrete Types |
|---|---|
| Strategy | `Resource`, `Capability`, `ValueStream`, `CourseOfAction` |
| Business | `BusinessActor`, `BusinessRole`, `BusinessCollaboration`, `BusinessInterface`, `BusinessProcess`, `BusinessFunction`, `BusinessInteraction`, `BusinessEvent`, `BusinessService`, `BusinessObject`, `Contract`, `Representation`, `Product` |
| Application | `ApplicationComponent`, `ApplicationCollaboration`, `ApplicationInterface`, `ApplicationFunction`, `ApplicationInteraction`, `ApplicationProcess`, `ApplicationEvent`, `ApplicationService`, `DataObject` |
| Technology | `Node`, `Device`, `SystemSoftware`, `TechnologyCollaboration`, `TechnologyInterface`, `Path`, `CommunicationNetwork`, `TechnologyFunction`, `TechnologyProcess`, `TechnologyInteraction`, `TechnologyEvent`, `TechnologyService`, `Artifact` |
| Physical | `Equipment`, `Facility`, `DistributionNetwork`, `Material` |
| Motivation | `Stakeholder`, `Driver`, `Assessment`, `Goal`, `Outcome`, `Principle`, `Requirement`, `Constraint`, `Meaning`, `Value` |
| I&M | `WorkPackage`, `Deliverable`, `ImplementationEvent`, `Plateau`, `Gap` |
| Generic | `Grouping`, `Location` |

Concrete relationship types for non-universal rules: `Assignment`, `Access`, `Serving`, `Realization`, `Influence`, `Triggering`, `Flow`.

## Test File

```python
# test/test_feat163_completeness_audit.py
"""Tests for FEAT-16.3: Permission table completeness audit against Appendix B."""
from __future__ import annotations

import pytest

from pyarchi.metamodel.application import (
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
from pyarchi.metamodel.business import (
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
from pyarchi.metamodel.implementation_migration import (
    Deliverable,
    Gap,
    ImplementationEvent,
    Plateau,
    WorkPackage,
)
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
from pyarchi.metamodel.physical import (
    DistributionNetwork,
    Equipment,
    Facility,
    Material,
)
from pyarchi.metamodel.relationships import (
    Access,
    Assignment,
    Flow,
    Influence,
    Realization,
    Serving,
    Triggering,
)
from pyarchi.metamodel.strategy import (
    Capability,
    CourseOfAction,
    Resource,
    ValueStream,
)
from pyarchi.metamodel.technology import (
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
from pyarchi.validation.permissions import is_permitted


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MOTIVATION_TYPES = [
    Stakeholder, Driver, Assessment, Goal, Outcome,
    Principle, Requirement, Constraint, Meaning, Value,
]

BUSINESS_ACTIVE = [BusinessActor, BusinessRole, BusinessCollaboration]
BUSINESS_BEHAVIOR = [BusinessProcess, BusinessFunction, BusinessInteraction]
BUSINESS_PASSIVE = [BusinessObject, Contract, Representation]

APP_ACTIVE = [ApplicationComponent, ApplicationCollaboration]
APP_BEHAVIOR = [ApplicationFunction, ApplicationProcess, ApplicationInteraction]

TECH_ACTIVE = [
    Node, Device, SystemSoftware, TechnologyCollaboration,
    Path, CommunicationNetwork,
]
TECH_BEHAVIOR = [TechnologyFunction, TechnologyProcess, TechnologyInteraction]

PHYSICAL_ACTIVE = [Equipment, Facility, DistributionNetwork]


# ---------------------------------------------------------------------------
# STORY-16.3.1: Positive audit -- permitted pairs
# ---------------------------------------------------------------------------

class TestPositiveAuditAssignment:
    """Every Assignment pair that Appendix B permits returns True."""

    @pytest.mark.parametrize("src", BUSINESS_ACTIVE)
    @pytest.mark.parametrize("tgt", BUSINESS_BEHAVIOR)
    def test_business_active_to_behavior(self, src: type, tgt: type) -> None:
        assert is_permitted(Assignment, src, tgt) is True

    @pytest.mark.parametrize("src", BUSINESS_ACTIVE)
    def test_business_active_to_service(self, src: type) -> None:
        assert is_permitted(Assignment, src, BusinessService) is True

    @pytest.mark.parametrize("src", BUSINESS_ACTIVE)
    def test_business_active_to_event(self, src: type) -> None:
        assert is_permitted(Assignment, src, BusinessEvent) is True

    def test_business_interface_to_service(self) -> None:
        assert is_permitted(Assignment, BusinessInterface, BusinessService) is True

    @pytest.mark.parametrize("src", APP_ACTIVE)
    @pytest.mark.parametrize("tgt", APP_BEHAVIOR)
    def test_app_active_to_behavior(self, src: type, tgt: type) -> None:
        assert is_permitted(Assignment, src, tgt) is True

    @pytest.mark.parametrize("src", APP_ACTIVE)
    def test_app_active_to_service(self, src: type) -> None:
        assert is_permitted(Assignment, src, ApplicationService) is True

    @pytest.mark.parametrize("src", APP_ACTIVE)
    def test_app_active_to_event(self, src: type) -> None:
        assert is_permitted(Assignment, src, ApplicationEvent) is True

    def test_app_interface_to_service(self) -> None:
        assert is_permitted(Assignment, ApplicationInterface, ApplicationService) is True

    @pytest.mark.parametrize("src", TECH_ACTIVE)
    @pytest.mark.parametrize("tgt", TECH_BEHAVIOR)
    def test_tech_active_to_behavior(self, src: type, tgt: type) -> None:
        assert is_permitted(Assignment, src, tgt) is True

    @pytest.mark.parametrize("src", TECH_ACTIVE)
    def test_tech_active_to_service(self, src: type) -> None:
        assert is_permitted(Assignment, src, TechnologyService) is True

    @pytest.mark.parametrize("src", TECH_ACTIVE)
    def test_tech_active_to_event(self, src: type) -> None:
        assert is_permitted(Assignment, src, TechnologyEvent) is True

    def test_tech_interface_to_service(self) -> None:
        assert is_permitted(Assignment, TechnologyInterface, TechnologyService) is True

    @pytest.mark.parametrize("src", BUSINESS_ACTIVE)
    def test_business_active_to_work_package(self, src: type) -> None:
        assert is_permitted(Assignment, src, WorkPackage) is True

    @pytest.mark.parametrize("src", BUSINESS_ACTIVE)
    @pytest.mark.parametrize("tgt", MOTIVATION_TYPES)
    def test_business_active_to_motivation(self, src: type, tgt: type) -> None:
        assert is_permitted(Assignment, src, tgt) is True

    def test_resource_to_capability(self) -> None:
        assert is_permitted(Assignment, Resource, Capability) is True

    def test_resource_to_value_stream(self) -> None:
        assert is_permitted(Assignment, Resource, ValueStream) is True


class TestPositiveAuditAccess:
    @pytest.mark.parametrize("src", BUSINESS_ACTIVE)
    @pytest.mark.parametrize("tgt", BUSINESS_PASSIVE)
    def test_business_active_accesses_passive(self, src: type, tgt: type) -> None:
        assert is_permitted(Access, src, tgt) is True

    @pytest.mark.parametrize("src", BUSINESS_BEHAVIOR)
    @pytest.mark.parametrize("tgt", BUSINESS_PASSIVE)
    def test_business_behavior_accesses_passive(self, src: type, tgt: type) -> None:
        assert is_permitted(Access, src, tgt) is True

    @pytest.mark.parametrize("src", APP_ACTIVE)
    def test_app_active_accesses_data_object(self, src: type) -> None:
        assert is_permitted(Access, src, DataObject) is True

    @pytest.mark.parametrize("src", APP_BEHAVIOR)
    def test_app_behavior_accesses_data_object(self, src: type) -> None:
        assert is_permitted(Access, src, DataObject) is True

    @pytest.mark.parametrize("src", TECH_ACTIVE)
    def test_tech_active_accesses_artifact(self, src: type) -> None:
        assert is_permitted(Access, src, Artifact) is True

    @pytest.mark.parametrize("src", TECH_BEHAVIOR)
    def test_tech_behavior_accesses_artifact(self, src: type) -> None:
        assert is_permitted(Access, src, Artifact) is True

    def test_implementation_event_accesses_deliverable(self) -> None:
        assert is_permitted(Access, ImplementationEvent, Deliverable) is True


class TestPositiveAuditServing:
    def test_app_service_to_business_behavior(self) -> None:
        assert is_permitted(Serving, ApplicationService, BusinessProcess) is True

    def test_tech_service_to_app_behavior(self) -> None:
        assert is_permitted(Serving, TechnologyService, ApplicationFunction) is True

    def test_business_service_to_business_behavior(self) -> None:
        assert is_permitted(Serving, BusinessService, BusinessProcess) is True

    def test_app_service_to_app_behavior(self) -> None:
        assert is_permitted(Serving, ApplicationService, ApplicationFunction) is True

    def test_tech_service_to_tech_behavior(self) -> None:
        assert is_permitted(Serving, TechnologyService, TechnologyFunction) is True


class TestPositiveAuditRealization:
    def test_app_behavior_realizes_business_behavior(self) -> None:
        assert is_permitted(Realization, ApplicationFunction, BusinessProcess) is True

    def test_data_object_realizes_business_object(self) -> None:
        assert is_permitted(Realization, DataObject, BusinessObject) is True

    def test_tech_behavior_realizes_app_behavior(self) -> None:
        assert is_permitted(Realization, TechnologyFunction, ApplicationFunction) is True

    def test_artifact_realizes_data_object(self) -> None:
        assert is_permitted(Realization, Artifact, DataObject) is True

    def test_artifact_realizes_app_component(self) -> None:
        assert is_permitted(Realization, Artifact, ApplicationComponent) is True

    def test_deliverable_realizes_structure(self) -> None:
        assert is_permitted(Realization, Deliverable, BusinessObject) is True

    def test_deliverable_realizes_behavior(self) -> None:
        assert is_permitted(Realization, Deliverable, BusinessProcess) is True

    @pytest.mark.parametrize("tgt", MOTIVATION_TYPES)
    def test_structure_realizes_motivation(self, tgt: type) -> None:
        assert is_permitted(Realization, BusinessActor, tgt) is True

    @pytest.mark.parametrize("tgt", MOTIVATION_TYPES)
    def test_behavior_realizes_motivation(self, tgt: type) -> None:
        assert is_permitted(Realization, BusinessProcess, tgt) is True


class TestPositiveAuditInfluence:
    @pytest.mark.parametrize("src", MOTIVATION_TYPES)
    @pytest.mark.parametrize("tgt", MOTIVATION_TYPES)
    def test_motivation_to_motivation(self, src: type, tgt: type) -> None:
        assert is_permitted(Influence, src, tgt) is True

    @pytest.mark.parametrize("mot", MOTIVATION_TYPES[:3])
    def test_motivation_to_core(self, mot: type) -> None:
        assert is_permitted(Influence, mot, BusinessActor) is True

    @pytest.mark.parametrize("mot", MOTIVATION_TYPES[:3])
    def test_core_to_motivation(self, mot: type) -> None:
        assert is_permitted(Influence, BusinessActor, mot) is True


class TestPositiveAuditTriggering:
    @pytest.mark.parametrize("src", BUSINESS_BEHAVIOR)
    @pytest.mark.parametrize("tgt", BUSINESS_BEHAVIOR)
    def test_business_intra_layer(self, src: type, tgt: type) -> None:
        assert is_permitted(Triggering, src, tgt) is True

    @pytest.mark.parametrize("src", APP_BEHAVIOR)
    @pytest.mark.parametrize("tgt", APP_BEHAVIOR)
    def test_app_intra_layer(self, src: type, tgt: type) -> None:
        assert is_permitted(Triggering, src, tgt) is True

    @pytest.mark.parametrize("src", TECH_BEHAVIOR)
    @pytest.mark.parametrize("tgt", TECH_BEHAVIOR)
    def test_tech_intra_layer(self, src: type, tgt: type) -> None:
        assert is_permitted(Triggering, src, tgt) is True

    def test_business_event_triggers_behavior(self) -> None:
        assert is_permitted(Triggering, BusinessEvent, BusinessProcess) is True

    def test_behavior_triggers_business_event(self) -> None:
        assert is_permitted(Triggering, BusinessProcess, BusinessEvent) is True

    def test_implementation_event_triggers_work_package(self) -> None:
        assert is_permitted(Triggering, ImplementationEvent, WorkPackage) is True

    def test_implementation_event_triggers_plateau(self) -> None:
        assert is_permitted(Triggering, ImplementationEvent, Plateau) is True

    def test_work_package_triggers_implementation_event(self) -> None:
        assert is_permitted(Triggering, WorkPackage, ImplementationEvent) is True


class TestPositiveAuditFlow:
    @pytest.mark.parametrize("src", BUSINESS_BEHAVIOR)
    @pytest.mark.parametrize("tgt", BUSINESS_BEHAVIOR)
    def test_business_intra_layer(self, src: type, tgt: type) -> None:
        assert is_permitted(Flow, src, tgt) is True

    @pytest.mark.parametrize("src", APP_BEHAVIOR)
    @pytest.mark.parametrize("tgt", APP_BEHAVIOR)
    def test_app_intra_layer(self, src: type, tgt: type) -> None:
        assert is_permitted(Flow, src, tgt) is True

    @pytest.mark.parametrize("src", TECH_BEHAVIOR)
    @pytest.mark.parametrize("tgt", TECH_BEHAVIOR)
    def test_tech_intra_layer(self, src: type, tgt: type) -> None:
        assert is_permitted(Flow, src, tgt) is True


# ---------------------------------------------------------------------------
# STORY-16.3.2: Negative audit -- explicitly prohibited pairs
# ---------------------------------------------------------------------------

class TestProhibitedPairs:
    """Triples that must return False per Appendix B or pyarchi prohibitions."""

    @pytest.mark.parametrize("passive", BUSINESS_PASSIVE)
    def test_passive_cannot_assign_behavior(self, passive: type) -> None:
        assert is_permitted(Assignment, passive, BusinessProcess) is False

    @pytest.mark.parametrize("passive", [DataObject, Artifact, Material, Deliverable])
    def test_passive_cannot_access_as_source(self, passive: type) -> None:
        assert is_permitted(Access, passive, BusinessObject) is False

    @pytest.mark.parametrize("passive", [DataObject, Artifact, Material, Deliverable])
    def test_passive_cannot_serve_as_source(self, passive: type) -> None:
        assert is_permitted(Serving, passive, BusinessProcess) is False

    @pytest.mark.parametrize("src", [ApplicationFunction, TechnologyFunction, Artifact])
    def test_realization_target_business_active_prohibited(self, src: type) -> None:
        assert is_permitted(Realization, src, BusinessActor) is False

    @pytest.mark.parametrize("src", [ApplicationFunction, TechnologyFunction, Artifact])
    def test_realization_target_business_role_prohibited(self, src: type) -> None:
        assert is_permitted(Realization, src, BusinessRole) is False


# ---------------------------------------------------------------------------
# STORY-16.3.3: Default-deny -- unknown triples return False
# ---------------------------------------------------------------------------

class TestDefaultDeny:
    """Triples not in the table and not covered by universal rules return False."""

    def test_triggering_motivation_to_tech(self) -> None:
        assert is_permitted(Triggering, Goal, Artifact) is False

    def test_flow_motivation_to_motivation(self) -> None:
        assert is_permitted(Flow, Goal, Driver) is False

    def test_assignment_motivation_to_behavior(self) -> None:
        assert is_permitted(Assignment, Goal, BusinessProcess) is False

    def test_access_motivation_to_passive(self) -> None:
        assert is_permitted(Access, Goal, BusinessObject) is False

    def test_serving_motivation_to_behavior(self) -> None:
        assert is_permitted(Serving, Goal, BusinessProcess) is False

    def test_realization_passive_to_passive(self) -> None:
        """DataObject realizing Artifact -- not in Appendix B."""
        assert is_permitted(Realization, DataObject, Artifact) is False

    def test_triggering_active_to_passive(self) -> None:
        assert is_permitted(Triggering, BusinessActor, BusinessObject) is False

    def test_flow_active_to_active(self) -> None:
        assert is_permitted(Flow, BusinessActor, BusinessRole) is False
```

## Coverage Notes

The test file above provides **representative** coverage. The parametrize combinatorics yield:

| Test class | Approximate test count |
|---|---|
| `TestPositiveAuditAssignment` | ~90 |
| `TestPositiveAuditAccess` | ~35 |
| `TestPositiveAuditServing` | ~5 |
| `TestPositiveAuditRealization` | ~25 |
| `TestPositiveAuditInfluence` | ~110 |
| `TestPositiveAuditTriggering` | ~30 |
| `TestPositiveAuditFlow` | ~27 |
| `TestProhibitedPairs` | ~15 |
| `TestDefaultDeny` | ~8 |
| **Total** | **~345** |

The implementer should extend parametrize lists if additional Appendix B entries are discovered during FEAT-16.2. The goal is that every row in `_PERMISSION_TABLE` is exercised by at least one concrete-type test case.

## Edge Cases

- `Product` is a `CompositeElement`, not a `PassiveStructureElement`. It should NOT match passive-source prohibitions. Add an explicit test if Appendix B has Product-specific rules.
- `Gap` is a plain `Element` subclass (not Structure, not Behavior, not Motivation). It matches very few table entries. Verify it returns `False` for most relationship types.
- `Grouping` and `Location` are `CompositeElement` subclasses. They primarily participate via Composition (universal rule). Verify non-universal relationships return `False`.
- `Plateau` is a `CompositeElement`. Its only non-universal permissions are Triggering with `ImplementationEvent`. Verify other relationships return `False`.
