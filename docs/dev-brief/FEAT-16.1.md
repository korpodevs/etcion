# Technical Brief: FEAT-16.1 -- Declarative Permission Table and Cached Lookup

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-028-epic016-declarative-permissions.md` (Decisions 1--5, 8)
**Backlog:** STORY-16.1.1, STORY-16.1.2, STORY-16.1.3, STORY-16.1.4

## Scope

Replace the procedural `if`/`issubclass` cascade in `is_permitted()` with:

1. A `PermissionRule` NamedTuple
2. A module-level `_PERMISSION_TABLE: tuple[PermissionRule, ...]`
3. A lazy-initialized concrete-type cache `_cache: dict[tuple, bool]`
4. A rewritten `is_permitted()` that checks universal short-circuits, the deprecation special case, then the cache

The universal short-circuits (Composition/Aggregation same-type + CompositeElement->Relationship, Specialization same-type, Association always-true) and the `Realization(WorkPackage, Deliverable)` deprecation warning remain as hand-coded paths per ADR-028 Decisions 1 and 8.

## Data Structure

**File:** `src/pyarchi/validation/permissions.py`

```python
from typing import NamedTuple

class PermissionRule(NamedTuple):
    rel_type: type[Relationship]
    source_type: type[Element]
    target_type: type[Element]
    permitted: bool
```

## Permission Table Entries

All entries below are grouped by `rel_type`. Within each group, prohibitions (`permitted=False`) precede permissions (`permitted=True`). This ordering is load-bearing per ADR-028 Decision 3.

The implementer MUST reference ArchiMate 3.2 Specification Appendix B to verify completeness. The `assets/archimate-spec-3.2/` directory does not contain the appendix; use the published spec directly.

### Assignment

| # | `source_type` | `target_type` | `permitted` | Origin |
|---|---|---|---|---|
| A1 | `PassiveStructureElement` | `BehaviorElement` | `False` | FEAT-15.6, spec: passive cannot perform |
| A2 | `BusinessInternalActiveStructureElement` | `BusinessInternalBehaviorElement` | `True` | Appendix B: Business intra-layer |
| A3 | `BusinessInternalActiveStructureElement` | `BusinessService` | `True` | Appendix B: active -> service |
| A4 | `BusinessInternalActiveStructureElement` | `BusinessEvent` | `True` | Appendix B: active -> event |
| A5 | `BusinessInterface` | `BusinessService` | `True` | Appendix B: interface -> service |
| A6 | `ApplicationInternalActiveStructureElement` | `ApplicationInternalBehaviorElement` | `True` | Appendix B: App intra-layer |
| A7 | `ApplicationInternalActiveStructureElement` | `ApplicationService` | `True` | Appendix B |
| A8 | `ApplicationInternalActiveStructureElement` | `ApplicationEvent` | `True` | Appendix B |
| A9 | `ApplicationInterface` | `ApplicationService` | `True` | Appendix B |
| A10 | `TechnologyInternalActiveStructureElement` | `TechnologyInternalBehaviorElement` | `True` | Appendix B: Tech intra-layer |
| A11 | `TechnologyInternalActiveStructureElement` | `TechnologyService` | `True` | Appendix B |
| A12 | `TechnologyInternalActiveStructureElement` | `TechnologyEvent` | `True` | Appendix B |
| A13 | `TechnologyInterface` | `TechnologyService` | `True` | Appendix B |
| A14 | `PhysicalActiveStructureElement` | `TechnologyInternalBehaviorElement` | `True` | Appendix B: Physical->Tech |
| A15 | `PhysicalActiveStructureElement` | `TechnologyService` | `True` | Appendix B |
| A16 | `BusinessInternalActiveStructureElement` | `MotivationElement` | `True` | FEAT-11.4 (Stakeholder) |
| A17 | `BusinessInternalActiveStructureElement` | `WorkPackage` | `True` | FEAT-12.4 |

### Access

| # | `source_type` | `target_type` | `permitted` | Origin |
|---|---|---|---|---|
| Ac1 | `PassiveStructureElement` | `Element` | `False` | FEAT-15.1: passive source prohibited |
| Ac2 | `BusinessInternalActiveStructureElement` | `BusinessPassiveStructureElement` | `True` | Appendix B: Business |
| Ac3 | `BusinessInternalBehaviorElement` | `BusinessPassiveStructureElement` | `True` | Appendix B |
| Ac4 | `BusinessService` | `BusinessPassiveStructureElement` | `True` | Appendix B |
| Ac5 | `BusinessEvent` | `BusinessPassiveStructureElement` | `True` | Appendix B |
| Ac6 | `BusinessInterface` | `BusinessPassiveStructureElement` | `True` | Appendix B |
| Ac7 | `ApplicationInternalActiveStructureElement` | `DataObject` | `True` | Appendix B: App |
| Ac8 | `ApplicationInternalBehaviorElement` | `DataObject` | `True` | Appendix B |
| Ac9 | `ApplicationService` | `DataObject` | `True` | Appendix B |
| Ac10 | `ApplicationEvent` | `DataObject` | `True` | Appendix B |
| Ac11 | `ApplicationInterface` | `DataObject` | `True` | Appendix B |
| Ac12 | `TechnologyInternalActiveStructureElement` | `Artifact` | `True` | Appendix B: Tech |
| Ac13 | `TechnologyInternalBehaviorElement` | `Artifact` | `True` | Appendix B |
| Ac14 | `TechnologyService` | `Artifact` | `True` | Appendix B |
| Ac15 | `TechnologyEvent` | `Artifact` | `True` | Appendix B |
| Ac16 | `TechnologyInterface` | `Artifact` | `True` | Appendix B |
| Ac17 | `ImplementationEvent` | `Deliverable` | `True` | FEAT-12.4 |

### Serving

| # | `source_type` | `target_type` | `permitted` | Origin |
|---|---|---|---|---|
| S1 | `PassiveStructureElement` | `Element` | `False` | FEAT-15.1: passive source prohibited |
| S2 | `BusinessService` | `BusinessInternalBehaviorElement` | `True` | Appendix B: Business intra-layer |
| S3 | `BusinessService` | `BusinessService` | `True` | Appendix B |
| S4 | `BusinessInterface` | `BusinessInternalActiveStructureElement` | `True` | Appendix B |
| S5 | `ApplicationService` | `ApplicationInternalBehaviorElement` | `True` | Appendix B: App intra-layer |
| S6 | `ApplicationService` | `ApplicationService` | `True` | Appendix B |
| S7 | `ApplicationInterface` | `ApplicationInternalActiveStructureElement` | `True` | Appendix B |
| S8 | `TechnologyService` | `TechnologyInternalBehaviorElement` | `True` | Appendix B: Tech intra-layer |
| S9 | `TechnologyService` | `TechnologyService` | `True` | Appendix B |
| S10 | `TechnologyInterface` | `TechnologyInternalActiveStructureElement` | `True` | Appendix B |
| S11 | `ApplicationService` | `BusinessInternalBehaviorElement` | `True` | FEAT-13.1: App->Business |
| S12 | `ApplicationInterface` | `BusinessInternalActiveStructureElement` | `True` | FEAT-13.1 |
| S13 | `BusinessService` | `ApplicationInternalBehaviorElement` | `True` | FEAT-13.1: Business->App |
| S14 | `BusinessInterface` | `ApplicationInternalActiveStructureElement` | `True` | FEAT-13.1 |
| S15 | `TechnologyService` | `ApplicationInternalBehaviorElement` | `True` | FEAT-13.2: Tech->App |
| S16 | `TechnologyInterface` | `ApplicationInternalActiveStructureElement` | `True` | FEAT-13.2 |

### Realization

| # | `source_type` | `target_type` | `permitted` | Origin |
|---|---|---|---|---|
| R1 | `Element` | `BusinessInternalActiveStructureElement` | `False` | FEAT-13.4: prohibition |
| R2 | `Deliverable` | `StructureElement` | `True` | FEAT-12.4 |
| R3 | `Deliverable` | `BehaviorElement` | `True` | FEAT-12.4 |
| R4 | `ApplicationInternalBehaviorElement` | `BusinessInternalBehaviorElement` | `True` | FEAT-13.3 |
| R5 | `DataObject` | `BusinessObject` | `True` | FEAT-13.3 |
| R6 | `TechnologyInternalBehaviorElement` | `ApplicationInternalBehaviorElement` | `True` | FEAT-13.3 |
| R7 | `Artifact` | `DataObject` | `True` | FEAT-13.3 |
| R8 | `Artifact` | `ApplicationComponent` | `True` | FEAT-13.3 |
| R9 | `StructureElement` | `MotivationElement` | `True` | FEAT-11.4 |
| R10 | `BehaviorElement` | `MotivationElement` | `True` | FEAT-11.4 |

> Note: `Realization(WorkPackage, Deliverable)` is NOT in the table. It is a hand-coded special case with `DeprecationWarning` per ADR-028 Decision 8, placed after universal short-circuits and before table lookup.

### Influence

| # | `source_type` | `target_type` | `permitted` | Origin |
|---|---|---|---|---|
| I1 | `MotivationElement` | `MotivationElement` | `True` | FEAT-11.4: motivation<->motivation |
| I2 | `MotivationElement` | `Element` | `True` | FEAT-11.4: motivation->core |
| I3 | `Element` | `MotivationElement` | `True` | FEAT-11.4: core->motivation |

### Triggering

| # | `source_type` | `target_type` | `permitted` | Origin |
|---|---|---|---|---|
| T1 | `BusinessInternalBehaviorElement` | `BusinessInternalBehaviorElement` | `True` | Appendix B: Business intra-layer |
| T2 | `BusinessEvent` | `BusinessInternalBehaviorElement` | `True` | Appendix B |
| T3 | `BusinessInternalBehaviorElement` | `BusinessEvent` | `True` | Appendix B |
| T4 | `BusinessEvent` | `BusinessEvent` | `True` | Appendix B |
| T5 | `ApplicationInternalBehaviorElement` | `ApplicationInternalBehaviorElement` | `True` | Appendix B: App intra-layer |
| T6 | `ApplicationEvent` | `ApplicationInternalBehaviorElement` | `True` | Appendix B |
| T7 | `ApplicationInternalBehaviorElement` | `ApplicationEvent` | `True` | Appendix B |
| T8 | `ApplicationEvent` | `ApplicationEvent` | `True` | Appendix B |
| T9 | `TechnologyInternalBehaviorElement` | `TechnologyInternalBehaviorElement` | `True` | Appendix B: Tech intra-layer |
| T10 | `TechnologyEvent` | `TechnologyInternalBehaviorElement` | `True` | Appendix B |
| T11 | `TechnologyInternalBehaviorElement` | `TechnologyEvent` | `True` | Appendix B |
| T12 | `TechnologyEvent` | `TechnologyEvent` | `True` | Appendix B |
| T13 | `ImplementationEvent` | `WorkPackage` | `True` | FEAT-12.4 |
| T14 | `ImplementationEvent` | `Plateau` | `True` | FEAT-12.4 |
| T15 | `WorkPackage` | `ImplementationEvent` | `True` | FEAT-12.4 |
| T16 | `Plateau` | `ImplementationEvent` | `True` | FEAT-12.4 |

### Flow

| # | `source_type` | `target_type` | `permitted` | Origin |
|---|---|---|---|---|
| F1 | `BusinessInternalBehaviorElement` | `BusinessInternalBehaviorElement` | `True` | Appendix B: Business |
| F2 | `BusinessEvent` | `BusinessInternalBehaviorElement` | `True` | Appendix B |
| F3 | `BusinessInternalBehaviorElement` | `BusinessEvent` | `True` | Appendix B |
| F4 | `BusinessEvent` | `BusinessEvent` | `True` | Appendix B |
| F5 | `ApplicationInternalBehaviorElement` | `ApplicationInternalBehaviorElement` | `True` | Appendix B: App |
| F6 | `ApplicationEvent` | `ApplicationInternalBehaviorElement` | `True` | Appendix B |
| F7 | `ApplicationInternalBehaviorElement` | `ApplicationEvent` | `True` | Appendix B |
| F8 | `ApplicationEvent` | `ApplicationEvent` | `True` | Appendix B |
| F9 | `TechnologyInternalBehaviorElement` | `TechnologyInternalBehaviorElement` | `True` | Appendix B: Tech |
| F10 | `TechnologyEvent` | `TechnologyInternalBehaviorElement` | `True` | Appendix B |
| F11 | `TechnologyInternalBehaviorElement` | `TechnologyEvent` | `True` | Appendix B |
| F12 | `TechnologyEvent` | `TechnologyEvent` | `True` | Appendix B |

## Cache Building Logic

**Lazy initialization** on first `is_permitted()` call:

```python
_cache: dict[tuple[type[Relationship], type[Element], type[Element]], bool] | None = None

def _build_cache() -> dict[tuple[type[Relationship], type[Element], type[Element]], bool]:
    """Expand ABC-level table into concrete-type triples for O(1) lookup."""
    cache: dict[tuple[type[Relationship], type[Element], type[Element]], bool] = {}
    for rule in _PERMISSION_TABLE:
        for src in _concrete_subclasses(rule.source_type):
            for tgt in _concrete_subclasses(rule.target_type):
                key = (rule.rel_type, src, tgt)
                if key not in cache:  # first match wins
                    cache[key] = rule.permitted
    return cache

def _concrete_subclasses(cls: type[Element]) -> list[type[Element]]:
    """Recursively collect all concrete subclasses (those with _type_name)."""
    result: list[type[Element]] = []
    if _is_concrete(cls):
        result.append(cls)
    for sub in cls.__subclasses__():
        result.extend(_concrete_subclasses(sub))
    return result
```

Concreteness test: a class is concrete if it implements `_type_name` as a property (not abstract). Simplest heuristic: try `hasattr` on an instance, or check `_type_name` in `cls.__dict__` or any non-abstract ancestor.

Practical approach: check if `cls` appears in `Element.__subclasses__()` recursion AND is not in a known set of ABCs. Or simply: `not cls.__abstractmethods__` if using ABC, but pyarchi uses Pydantic without `abc.ABC`. The implementer should use a reliable concreteness check -- the recommended approach is to check whether the class has `_type_name` as a non-abstract property in its own `__dict__` or any of its concrete MRO entries.

## Rewritten `is_permitted()`

```python
def is_permitted(
    rel_type: type[Relationship],
    source_type: type[Element],
    target_type: type[Element],
) -> bool:
    global _cache

    # 1. Universal: Composition/Aggregation same-type + CompositeElement->Relationship
    if rel_type in _UNIVERSAL_SAME_TYPE:
        if source_type == target_type:
            return True
        if issubclass(target_type, Relationship) and issubclass(source_type, CompositeElement):
            return True
        return False

    # 2. Universal: Specialization same-type
    if rel_type is Specialization:
        return source_type == target_type

    # 3. Universal: Association always permitted
    if rel_type is Association:
        return True

    # 4. Deprecation special case (ADR-028 Decision 8)
    if rel_type is Realization:
        if issubclass(source_type, WorkPackage) and issubclass(target_type, Deliverable):
            import warnings
            warnings.warn(
                "Realization from WorkPackage to Deliverable is deprecated in "
                "ArchiMate 3.2. Use Assignment instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            return True

    # 5. Cache lookup
    if _cache is None:
        _cache = _build_cache()
    return _cache.get((rel_type, source_type, target_type), False)
```

## Imports

All layer-specific imports move to module-level. No more inline `from pyarchi.metamodel.business import ...` inside the function body.

```python
from pyarchi.metamodel.business import (
    BusinessEvent, BusinessInternalActiveStructureElement,
    BusinessInternalBehaviorElement, BusinessInterface,
    BusinessObject, BusinessPassiveStructureElement, BusinessService,
)
from pyarchi.metamodel.application import (
    ApplicationComponent, ApplicationEvent,
    ApplicationInternalActiveStructureElement,
    ApplicationInternalBehaviorElement, ApplicationInterface,
    ApplicationService, DataObject,
)
from pyarchi.metamodel.technology import (
    Artifact, TechnologyEvent,
    TechnologyInternalActiveStructureElement,
    TechnologyInternalBehaviorElement, TechnologyInterface,
    TechnologyService,
)
from pyarchi.metamodel.physical import PhysicalActiveStructureElement
from pyarchi.metamodel.motivation import *  # already via MotivationElement ABC
from pyarchi.metamodel.implementation_migration import (
    Deliverable, ImplementationEvent, Plateau, WorkPackage,
)
```

## Dual-Path Compatibility Test

Before deleting old code, capture a snapshot. The test generates all `(rel_type, src_concrete, tgt_concrete)` triples for concrete types currently in the type universe, calls both old and new implementations, and asserts identical results for any triple where the old implementation returned `True`. Triples that were `False` under the old code and `True` under the new code are expected (intentional Appendix B expansion) and are logged but not failures.

This test is a one-time migration artifact. It lives in `test/test_feat161_migration.py` and is removed once FEAT-16.1 is merged.

## Test File

```python
# test/test_feat161_permission_table.py
"""Tests for FEAT-16.1: Declarative permission table and cached lookup."""
from __future__ import annotations

import warnings

import pytest

from pyarchi.metamodel.concepts import Element, Relationship
from pyarchi.metamodel.relationships import (
    Access, Aggregation, Assignment, Association, Composition,
    Flow, Influence, Realization, Serving, Specialization, Triggering,
)
from pyarchi.validation.permissions import (
    PermissionRule,
    _PERMISSION_TABLE,
    _UNIVERSAL_SAME_TYPE,
    is_permitted,
)


class TestPermissionRuleNamedTuple:
    """PermissionRule is a NamedTuple with the correct fields."""

    def test_fields(self) -> None:
        rule = PermissionRule(
            rel_type=Assignment,
            source_type=Element,
            target_type=Element,
            permitted=True,
        )
        assert rule.rel_type is Assignment
        assert rule.source_type is Element
        assert rule.target_type is Element
        assert rule.permitted is True

    def test_immutable(self) -> None:
        rule = PermissionRule(Assignment, Element, Element, True)
        with pytest.raises(AttributeError):
            rule.permitted = False  # type: ignore[misc]


class TestPermissionTableStructure:
    """Table is a tuple of PermissionRule; ordering invariants hold."""

    def test_table_is_tuple(self) -> None:
        assert isinstance(_PERMISSION_TABLE, tuple)

    def test_all_entries_are_permission_rules(self) -> None:
        for entry in _PERMISSION_TABLE:
            assert isinstance(entry, PermissionRule)

    def test_prohibitions_before_permissions_per_rel_type(self) -> None:
        """For each rel_type, all False entries precede all True entries."""
        from itertools import groupby

        for rel, group in groupby(_PERMISSION_TABLE, key=lambda r: r.rel_type):
            seen_true = False
            for rule in group:
                if rule.permitted:
                    seen_true = True
                else:
                    assert not seen_true, (
                        f"Prohibition after permission for {rel.__name__}: "
                        f"{rule.source_type.__name__} -> {rule.target_type.__name__}"
                    )

    def test_table_not_empty(self) -> None:
        assert len(_PERMISSION_TABLE) > 0

    def test_no_universal_rel_types_in_table(self) -> None:
        """Composition, Aggregation, Specialization, Association are NOT in the table."""
        universal = _UNIVERSAL_SAME_TYPE | {Specialization, Association}
        for rule in _PERMISSION_TABLE:
            assert rule.rel_type not in universal, (
                f"{rule.rel_type.__name__} should not be in the table"
            )


class TestUniversalShortCircuits:
    """Universal rules remain unchanged from pre-FEAT-16.1 behavior."""

    def test_composition_same_type(self) -> None:
        from pyarchi.metamodel.business import BusinessActor
        assert is_permitted(Composition, BusinessActor, BusinessActor) is True

    def test_composition_different_type(self) -> None:
        from pyarchi.metamodel.business import BusinessActor, BusinessRole
        assert is_permitted(Composition, BusinessActor, BusinessRole) is False

    def test_aggregation_same_type(self) -> None:
        from pyarchi.metamodel.business import BusinessRole
        assert is_permitted(Aggregation, BusinessRole, BusinessRole) is True

    def test_specialization_same_type(self) -> None:
        from pyarchi.metamodel.business import BusinessActor
        assert is_permitted(Specialization, BusinessActor, BusinessActor) is True

    def test_specialization_different_type(self) -> None:
        from pyarchi.metamodel.business import BusinessActor, BusinessRole
        assert is_permitted(Specialization, BusinessActor, BusinessRole) is False

    def test_association_always_true(self) -> None:
        from pyarchi.metamodel.business import BusinessActor
        from pyarchi.metamodel.technology import Artifact
        assert is_permitted(Association, BusinessActor, Artifact) is True

    def test_composite_element_to_relationship(self) -> None:
        from pyarchi.metamodel.elements import Grouping
        assert is_permitted(Composition, Grouping, Assignment) is True


class TestDeprecationSpecialCase:
    """Realization(WorkPackage, Deliverable) returns True with DeprecationWarning."""

    def test_permitted_with_warning(self) -> None:
        from pyarchi.metamodel.implementation_migration import Deliverable, WorkPackage
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = is_permitted(Realization, WorkPackage, Deliverable)
        assert result is True
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)


class TestCachedLookup:
    """Table-based rules resolve correctly via the cache."""

    def test_assignment_business_active_to_behavior(self) -> None:
        from pyarchi.metamodel.business import BusinessActor, BusinessProcess
        assert is_permitted(Assignment, BusinessActor, BusinessProcess) is True

    def test_assignment_passive_to_behavior_prohibited(self) -> None:
        from pyarchi.metamodel.business import BusinessObject, BusinessProcess
        assert is_permitted(Assignment, BusinessObject, BusinessProcess) is False

    def test_serving_app_to_business(self) -> None:
        from pyarchi.metamodel.application import ApplicationService
        from pyarchi.metamodel.business import BusinessProcess
        assert is_permitted(Serving, ApplicationService, BusinessProcess) is True

    def test_serving_passive_source_prohibited(self) -> None:
        from pyarchi.metamodel.application import DataObject
        from pyarchi.metamodel.business import BusinessProcess
        assert is_permitted(Serving, DataObject, BusinessProcess) is False

    def test_realization_app_behavior_to_business_behavior(self) -> None:
        from pyarchi.metamodel.application import ApplicationFunction
        from pyarchi.metamodel.business import BusinessProcess
        assert is_permitted(Realization, ApplicationFunction, BusinessProcess) is True

    def test_realization_target_business_active_prohibited(self) -> None:
        from pyarchi.metamodel.application import ApplicationFunction
        from pyarchi.metamodel.business import BusinessActor
        assert is_permitted(Realization, ApplicationFunction, BusinessActor) is False

    def test_influence_motivation_to_motivation(self) -> None:
        from pyarchi.metamodel.motivation import Driver, Goal
        assert is_permitted(Influence, Driver, Goal) is True

    def test_triggering_business_intra_layer(self) -> None:
        from pyarchi.metamodel.business import BusinessFunction, BusinessProcess
        assert is_permitted(Triggering, BusinessProcess, BusinessFunction) is True

    def test_flow_app_intra_layer(self) -> None:
        from pyarchi.metamodel.application import ApplicationFunction, ApplicationProcess
        assert is_permitted(Flow, ApplicationProcess, ApplicationFunction) is True

    def test_access_active_to_passive(self) -> None:
        from pyarchi.metamodel.business import BusinessActor, BusinessObject
        assert is_permitted(Access, BusinessActor, BusinessObject) is True

    def test_unknown_triple_returns_false(self) -> None:
        from pyarchi.metamodel.motivation import Goal
        from pyarchi.metamodel.technology import Artifact
        assert is_permitted(Triggering, Goal, Artifact) is False
```

## Edge Cases

- Cache must handle the case where `Element.__subclasses__()` returns ABCs that have no concrete descendants. These should be skipped during expansion.
- `WorkPackage` is an `InternalBehaviorElement` subclass. Ensure it does not match broad behavior rules that should only apply to layer-specific behavior ABCs. Table ordering (prohibitions first, specific before general) handles this.
- `BusinessEvent` extends `Event` (not `BusinessInternalBehaviorElement`). Entries must reference `BusinessEvent` explicitly where the spec permits events; `BusinessInternalBehaviorElement` will NOT match `BusinessEvent`.
- `Contract` extends `BusinessObject`. A rule for `BusinessPassiveStructureElement` covers both.
- `Device` and `SystemSoftware` extend `Node` which extends `TechnologyInternalActiveStructureElement`. They are covered by `TechnologyInternalActiveStructureElement` entries.
