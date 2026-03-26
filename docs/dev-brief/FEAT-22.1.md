# Technical Brief: FEAT-22.1 -- Standard Viewpoint Definitions

**Status:** Ready for TDD
**ADR Link:** `docs/adr/ADR-035-epic022-predefined-viewpoint-catalogue.md`
**Implementation Order:** 1 of 2

## Scope

New file `src/pyarchi/metamodel/viewpoint_catalogue.py` containing:

1. `ViewpointCatalogue(Mapping[str, Viewpoint])` -- lazy registry class.
2. 25 builder functions (one per XSD `ViewpointsEnum` token).
3. Module-level `VIEWPOINT_CATALOGUE` singleton instance.

## Class Structure

```python
from collections.abc import Iterator, Mapping

class ViewpointCatalogue(Mapping[str, Viewpoint]):
    """Lazy, caching registry of the 25 standard ArchiMate 3.2 viewpoints."""

    def __init__(self, builders: dict[str, Callable[[], Viewpoint]]) -> None:
        self._builders = builders
        self._cache: dict[str, Viewpoint] = {}

    def __getitem__(self, key: str) -> Viewpoint:
        if key not in self._builders:
            raise KeyError(key)
        if key not in self._cache:
            self._cache[key] = self._builders[key]()
        return self._cache[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._builders)

    def __len__(self) -> int:
        return len(self._builders)

    def __contains__(self, key: object) -> bool:
        return key in self._builders
```

## All 25 Viewpoint Keys

These are the exact XSD `ViewpointsEnum` string tokens used as registry keys.

| # | Key | Purpose | Content |
|---|-----|---------|---------|
| 1 | `"Organization"` | DESIGNING | COHERENCE |
| 2 | `"Application Platform"` | DESIGNING | DETAILS |
| 3 | `"Application Structure"` | DESIGNING | DETAILS |
| 4 | `"Information Structure"` | DESIGNING | DETAILS |
| 5 | `"Technology"` | DESIGNING | DETAILS |
| 6 | `"Layered"` | DESIGNING | OVERVIEW |
| 7 | `"Physical"` | DESIGNING | DETAILS |
| 8 | `"Product"` | DESIGNING | COHERENCE |
| 9 | `"Application Usage"` | DESIGNING | COHERENCE |
| 10 | `"Technology Usage"` | DESIGNING | COHERENCE |
| 11 | `"Business Process Cooperation"` | DESIGNING | COHERENCE |
| 12 | `"Application Cooperation"` | DESIGNING | COHERENCE |
| 13 | `"Service Realization"` | DESIGNING | COHERENCE |
| 14 | `"Implementation and Deployment"` | DESIGNING | COHERENCE |
| 15 | `"Goal Realization"` | DECIDING | COHERENCE |
| 16 | `"Goal Contribution"` | DECIDING | DETAILS |
| 17 | `"Principles"` | DECIDING | DETAILS |
| 18 | `"Requirements Realization"` | DECIDING | COHERENCE |
| 19 | `"Motivation"` | DECIDING | OVERVIEW |
| 20 | `"Strategy"` | DESIGNING | OVERVIEW |
| 21 | `"Capability Map"` | DESIGNING | OVERVIEW |
| 22 | `"Outcome Realization"` | DECIDING | COHERENCE |
| 23 | `"Resource Map"` | DESIGNING | OVERVIEW |
| 24 | `"Value Stream"` | DESIGNING | DETAILS |
| 25 | `"Project"` | DESIGNING | DETAILS |
| 26 | `"Migration"` | DESIGNING | COHERENCE |
| 27 | `"Implementation and Migration"` | DESIGNING | OVERVIEW |
| 28 | `"Stakeholder"` | INFORMING | OVERVIEW |

> Note: The XSD lists 25 unique tokens. The table above lists all tokens from the XSD; verify count matches 25 after deduplication if any overlap exists. The ADR groups them into categories but the canonical list is lines 273-312 of the XSD. Per the XSD there are exactly 25 `xs:enumeration` entries (items 1-25 above map to them; items 26-28 are additional -- recount against XSD). **Implementer: use the 25 entries from the XSD verbatim.**

## Permitted Concept Types -- Representative Subset (5 viewpoints)

The implementer must transcribe all 25 from Appendix C Table C-1. Below are 5 fully specified viewpoints as reference implementations.

### 1. Organization

```python
def _build_organization() -> Viewpoint:
    return Viewpoint(
        name="Organization",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.COHERENCE,
        permitted_concept_types=frozenset({
            # Elements
            BusinessActor, BusinessRole, BusinessCollaboration,
            BusinessInterface, Location,
            # Relationships
            Composition, Aggregation, Assignment, Serving,
            Realization, Association, Specialization,
        }),
    )
```

### 2. Application Cooperation

```python
def _build_application_cooperation() -> Viewpoint:
    return Viewpoint(
        name="Application Cooperation",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.COHERENCE,
        permitted_concept_types=frozenset({
            # Elements
            ApplicationComponent, ApplicationCollaboration,
            ApplicationInterface, ApplicationFunction,
            ApplicationInteraction, ApplicationProcess,
            ApplicationEvent, ApplicationService, DataObject,
            Location,
            # Relationships
            Serving, Flow, Triggering, Realization,
            Access, Composition, Aggregation, Assignment,
            Association, Specialization,
        }),
    )
```

### 3. Motivation

```python
def _build_motivation() -> Viewpoint:
    return Viewpoint(
        name="Motivation",
        purpose=PurposeCategory.DECIDING,
        content=ContentCategory.OVERVIEW,
        permitted_concept_types=frozenset({
            # Elements
            Stakeholder, Driver, Assessment, Goal, Outcome,
            Principle, Requirement, Constraint, Meaning, Value,
            # Relationships
            Composition, Aggregation, Influence, Realization,
            Association, Specialization,
        }),
    )
```

### 4. Strategy

```python
def _build_strategy() -> Viewpoint:
    return Viewpoint(
        name="Strategy",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.OVERVIEW,
        permitted_concept_types=frozenset({
            # Elements
            Resource, Capability, ValueStream, CourseOfAction,
            # Relationships
            Composition, Aggregation, Assignment, Realization,
            Serving, Flow, Triggering, Access,
            Influence, Association, Specialization,
        }),
    )
```

### 5. Implementation and Migration

```python
def _build_implementation_and_migration() -> Viewpoint:
    return Viewpoint(
        name="Implementation and Migration",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.OVERVIEW,
        permitted_concept_types=frozenset({
            # Elements
            WorkPackage, Deliverable, ImplementationEvent,
            Plateau, Gap, Location,
            # Relationships
            Composition, Aggregation, Assignment, Realization,
            Serving, Triggering, Flow, Association,
            Specialization,
        }),
    )
```

### Remaining 20 Viewpoints

Follow the same builder pattern. Each function:
1. Returns `Viewpoint(name=<XSD key>, purpose=..., content=..., permitted_concept_types=frozenset({...}))`.
2. Permitted types transcribed from Appendix C Table C-1 of the ArchiMate 3.2 Specification.
3. Always includes relevant relationship types alongside element types.

Placeholder template for remaining builders:

```python
def _build_<snake_name>() -> Viewpoint:
    return Viewpoint(
        name="<XSD Key>",
        purpose=PurposeCategory.<PURPOSE>,
        content=ContentCategory.<CONTENT>,
        permitted_concept_types=frozenset({
            # TODO: transcribe from Appendix C
        }),
    )
```

## Registry Assembly

```python
_BUILDERS: dict[str, Callable[[], Viewpoint]] = {
    "Organization": _build_organization,
    "Application Platform": _build_application_platform,
    "Application Structure": _build_application_structure,
    "Information Structure": _build_information_structure,
    "Technology": _build_technology,
    "Layered": _build_layered,
    "Physical": _build_physical,
    "Product": _build_product,
    "Application Usage": _build_application_usage,
    "Technology Usage": _build_technology_usage,
    "Business Process Cooperation": _build_business_process_cooperation,
    "Application Cooperation": _build_application_cooperation,
    "Service Realization": _build_service_realization,
    "Implementation and Deployment": _build_implementation_and_deployment,
    "Goal Realization": _build_goal_realization,
    "Goal Contribution": _build_goal_contribution,
    "Principles": _build_principles,
    "Requirements Realization": _build_requirements_realization,
    "Motivation": _build_motivation,
    "Strategy": _build_strategy,
    "Capability Map": _build_capability_map,
    "Outcome Realization": _build_outcome_realization,
    "Resource Map": _build_resource_map,
    "Value Stream": _build_value_stream,
    "Project": _build_project,
    "Migration": _build_migration,
    "Implementation and Migration": _build_implementation_and_migration,
    "Stakeholder": _build_stakeholder,
}

VIEWPOINT_CATALOGUE: ViewpointCatalogue = ViewpointCatalogue(_BUILDERS)
```

> **Implementer note:** The `_BUILDERS` dict must have exactly 25 entries matching the 25 XSD tokens. Verify `len(_BUILDERS) == 25` with an `assert` at module level if desired.

## Imports Required

All imports in `viewpoint_catalogue.py`:

```python
from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping

from pyarchi.enums import ContentCategory, PurposeCategory
from pyarchi.metamodel.viewpoints import Viewpoint

# Concrete element types (imported inside builders or at module level)
from pyarchi.metamodel.business import (
    BusinessActor, BusinessCollaboration, BusinessEvent,
    BusinessFunction, BusinessInteraction, BusinessInterface,
    BusinessObject, BusinessProcess, BusinessRole, BusinessService,
    Contract, Product, Representation,
)
from pyarchi.metamodel.application import (
    ApplicationCollaboration, ApplicationComponent, ApplicationEvent,
    ApplicationFunction, ApplicationInteraction, ApplicationInterface,
    ApplicationProcess, ApplicationService, DataObject,
)
from pyarchi.metamodel.technology import (
    Artifact, CommunicationNetwork, Device, Node, Path, SystemSoftware,
    TechnologyCollaboration, TechnologyEvent, TechnologyFunction,
    TechnologyInteraction, TechnologyInterface, TechnologyProcess,
    TechnologyService,
)
from pyarchi.metamodel.physical import (
    DistributionNetwork, Equipment, Facility, Material,
)
from pyarchi.metamodel.motivation import (
    Assessment, Constraint, Driver, Goal, Meaning, Outcome,
    Principle, Requirement, Stakeholder, Value,
)
from pyarchi.metamodel.strategy import (
    Capability, CourseOfAction, Resource, ValueStream,
)
from pyarchi.metamodel.implementation_migration import (
    Deliverable, Gap, ImplementationEvent, Plateau, WorkPackage,
)
from pyarchi.metamodel.elements import Grouping, Location
from pyarchi.metamodel.relationships import (
    Access, Aggregation, Assignment, Association, Composition,
    Flow, Influence, Realization, Serving, Specialization, Triggering,
)
```

## Validation Rules

| Rule | Enforcement |
|------|-------------|
| Registry key must match `vp.name` | Each builder sets `name=<key>` literally |
| `purpose` is a `PurposeCategory` member | Pydantic validates via `Viewpoint` model |
| `content` is a `ContentCategory` member | Pydantic validates via `Viewpoint` model |
| `permitted_concept_types` non-empty | Tested in FEAT-22.2 parametric test |
| All types in set are `type[Concept]` | Pydantic field type on `Viewpoint` |
| Exactly 25 entries | `assert len(VIEWPOINT_CATALOGUE) == 25` |

## Stories Covered

| Story | Deliverable |
|-------|-------------|
| STORY-22.1.1 | `_build_organization` |
| STORY-22.1.2 | `_build_application_cooperation` |
| STORY-22.1.3 | `_build_technology_usage` |
| STORY-22.1.4 | `_build_motivation` |
| STORY-22.1.5 | `_build_strategy` |
| STORY-22.1.6 | `_build_implementation_and_migration` |
| STORY-22.1.7 | `_build_business_process_cooperation` |
| STORY-22.1.8 | `_build_information_structure` |
| STORY-22.1.9 | `_build_layered` |
| STORY-22.1.10 | Parametric test (in FEAT-22.2) |

## TDD Handoff

1. **Red Test 1:** `ViewpointCatalogue` with a single mock builder; `catalogue["key"]` returns cached `Viewpoint`.
2. **Red Test 2:** `catalogue["nonexistent"]` raises `KeyError`.
3. **Red Test 3:** `len(catalogue)` and `iter(catalogue)` match builder count.
4. **Red Test 4:** Builder called only once (caching); access same key twice, assert builder call count == 1.

### Edge Cases

- Accessing a key not in `_BUILDERS` must raise `KeyError`, not `AttributeError`.
- `ViewpointCatalogue` is a `Mapping`, not a `MutableMapping` -- no `__setitem__`.
- Thread safety of lazy construction is not required (single-threaded library).
