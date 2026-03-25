# Technical Brief: FEAT-16.2 -- Remaining Appendix B Entries and Hierarchical Matching Verification

**Status:** Ready for TDD (depends on FEAT-16.1)
**ADR:** `docs/adr/ADR-028-epic016-declarative-permissions.md` (Decisions 4, 6, 7)
**Backlog:** STORY-16.2.1, STORY-16.2.2, STORY-16.2.3

## Scope

1. Add any Appendix B entries not captured in FEAT-16.1 (Strategy layer, Physical layer intra-layer rules, cross-layer rules beyond those already implemented).
2. Verify that hierarchical `issubclass` matching via the cache correctly resolves concrete subclasses.
3. Run the dual-path compatibility test confirming no regressions from the old procedural implementation.

## Additional Table Entries

The implementer MUST cross-reference Appendix B exhaustively. The entries below are known gaps not covered by FEAT-16.1. FEAT-16.1 covers cross-layer rules migrated from existing procedural code plus the most common intra-layer rules. This feature fills the remainder.

### Strategy Layer (Appendix B, Section 12)

| # | `rel_type` | `source_type` | `target_type` | `permitted` |
|---|---|---|---|---|
| St1 | `Assignment` | `Resource` | `Capability` | `True` |
| St2 | `Assignment` | `Resource` | `ValueStream` | `True` |
| St3 | `Assignment` | `Resource` | `CourseOfAction` | `True` |
| St4 | `Serving` | `Capability` | `Capability` | `True` |
| St5 | `Serving` | `ValueStream` | `Capability` | `True` |
| St6 | `Triggering` | `Capability` | `Capability` | `True` |
| St7 | `Triggering` | `ValueStream` | `ValueStream` | `True` |
| St8 | `Flow` | `ValueStream` | `ValueStream` | `True` |
| St9 | `Realization` | `CourseOfAction` | `MotivationElement` | `True` |

> Note: `Resource` is a `StrategyStructureElement` (which is a `StructureElement`, NOT `ActiveStructureElement`). It does NOT inherit from `InternalActiveStructureElement`. Entries must reference `Resource` directly.

### Physical Layer Intra-Layer

| # | `rel_type` | `source_type` | `target_type` | `permitted` |
|---|---|---|---|---|
| Ph1 | `Assignment` | `PhysicalActiveStructureElement` | `TechnologyInternalBehaviorElement` | `True` |
| Ph2 | `Access` | `PhysicalActiveStructureElement` | `Material` | `True` |
| Ph3 | `Serving` | `Equipment` | `Equipment` | `True` |
| Ph4 | `Serving` | `Facility` | `Facility` | `True` |

> Note: Ph1 may overlap with FEAT-16.1 entry A14. The implementer should deduplicate.

### Cross-Layer: Strategy to Core Layers

| # | `rel_type` | `source_type` | `target_type` | `permitted` |
|---|---|---|---|---|
| X1 | `Realization` | `BehaviorElement` | `Capability` | `True` |
| X2 | `Realization` | `BehaviorElement` | `ValueStream` | `True` |
| X3 | `Realization` | `StructureElement` | `Resource` | `True` |
| X4 | `Realization` | `CourseOfAction` | `MotivationElement` | `True` |

> Note: The implementer must verify these against Appendix B. The table in FEAT-16.1 already has `Realization(StructureElement, MotivationElement)` and `Realization(BehaviorElement, MotivationElement)`. Strategy cross-layer realization may require additional entries.

### Residual Cross-Layer Rules

The implementer must audit Appendix B for:

- `Serving` from Technology layer to Business layer (direct, not just via Application)
- `Realization` from Physical layer elements
- `Access` cross-layer rules
- `Triggering` cross-layer (e.g., Business event triggers Application behavior)
- `Flow` cross-layer

Each discovered rule becomes one `PermissionRule` entry appended to the appropriate `rel_type` group in `_PERMISSION_TABLE`, respecting prohibition-before-permission ordering.

## Hierarchical Matching Verification

The cache expansion must demonstrate that an ABC-level entry correctly covers all concrete descendants.

Key inheritance chains to verify:

| ABC | Concrete subclasses |
|---|---|
| `BusinessInternalActiveStructureElement` | `BusinessActor`, `BusinessRole`, `BusinessCollaboration` |
| `BusinessInternalBehaviorElement` | `BusinessProcess`, `BusinessFunction`, `BusinessInteraction` |
| `BusinessPassiveStructureElement` | `BusinessObject`, `Contract`, `Representation` |
| `ApplicationInternalActiveStructureElement` | `ApplicationComponent`, `ApplicationCollaboration` |
| `ApplicationInternalBehaviorElement` | `ApplicationFunction`, `ApplicationProcess`, `ApplicationInteraction` |
| `TechnologyInternalActiveStructureElement` | `Node`, `Device`, `SystemSoftware`, `TechnologyCollaboration`, `Path`, `CommunicationNetwork` |
| `TechnologyInternalBehaviorElement` | `TechnologyFunction`, `TechnologyProcess`, `TechnologyInteraction` |
| `PhysicalActiveStructureElement` | `Equipment`, `Facility`, `DistributionNetwork` |

> `Device` and `SystemSoftware` are subclasses of `Node`, which is a subclass of `TechnologyInternalActiveStructureElement`. The recursive `__subclasses__()` traversal must reach them.

## Dual-Path Compatibility Test

**File:** `test/test_feat162_migration.py`

This is a one-time migration test. It:

1. Imports all concrete element types
2. Imports all concrete relationship types (excluding Composition, Aggregation, Specialization, Association which are universal)
3. For every `(rel_type, src, tgt)` triple, calls `is_permitted()` and records the result
4. Compares against a known-good snapshot of the OLD implementation's results (captured before replacement)
5. Any triple that was `True` under old code but `False` under new code is a **regression** (test failure)
6. Any triple that was `False` under old code but `True` under new code is an **expansion** (logged, not failure)

Since the old code is already replaced in FEAT-16.1, the compatibility test should be written as part of FEAT-16.1 BEFORE the replacement. Practically, the implementer should:

1. Copy the old `is_permitted()` function body into a `_is_permitted_legacy()` function
2. Run both in the test
3. Delete `_is_permitted_legacy()` after the test passes

## Test File

```python
# test/test_feat162_hierarchical_matching.py
"""Tests for FEAT-16.2: Hierarchical type matching and Appendix B completeness."""
from __future__ import annotations

import pytest

from pyarchi.metamodel.relationships import (
    Access, Assignment, Flow, Realization, Serving, Triggering,
)
from pyarchi.validation.permissions import is_permitted


class TestHierarchicalResolution:
    """An ABC-level table entry covers all concrete descendants."""

    @pytest.mark.parametrize(
        "src",
        [
            "BusinessActor",
            "BusinessRole",
            "BusinessCollaboration",
        ],
    )
    def test_assignment_business_active_covers_all_concrete(self, src: str) -> None:
        import pyarchi.metamodel.business as biz
        src_cls = getattr(biz, src)
        assert is_permitted(Assignment, src_cls, biz.BusinessProcess) is True

    @pytest.mark.parametrize(
        "tgt",
        [
            "BusinessProcess",
            "BusinessFunction",
            "BusinessInteraction",
        ],
    )
    def test_assignment_targets_all_business_behaviors(self, tgt: str) -> None:
        from pyarchi.metamodel.business import BusinessActor
        import pyarchi.metamodel.business as biz
        tgt_cls = getattr(biz, tgt)
        assert is_permitted(Assignment, BusinessActor, tgt_cls) is True

    @pytest.mark.parametrize(
        "src",
        [
            "Node",
            "Device",
            "SystemSoftware",
            "TechnologyCollaboration",
            "Path",
            "CommunicationNetwork",
        ],
    )
    def test_tech_active_deep_hierarchy(self, src: str) -> None:
        """Device/SystemSoftware -> Node -> TechInternalActive must all match."""
        import pyarchi.metamodel.technology as tech
        src_cls = getattr(tech, src)
        assert is_permitted(Assignment, src_cls, tech.TechnologyFunction) is True

    @pytest.mark.parametrize(
        "passive",
        [
            "BusinessObject",
            "Contract",
            "Representation",
        ],
    )
    def test_access_passive_prohibition_covers_descendants(self, passive: str) -> None:
        """PassiveStructureElement prohibition covers BusinessObject, Contract, etc."""
        import pyarchi.metamodel.business as biz
        src_cls = getattr(biz, passive)
        assert is_permitted(Access, src_cls, biz.BusinessObject) is False

    def test_business_event_not_matched_by_internal_behavior(self) -> None:
        """BusinessEvent is NOT a BusinessInternalBehaviorElement subclass."""
        from pyarchi.metamodel.business import BusinessEvent, BusinessInternalBehaviorElement
        assert not issubclass(BusinessEvent, BusinessInternalBehaviorElement)

    def test_business_event_triggering_explicit_entry(self) -> None:
        from pyarchi.metamodel.business import BusinessEvent, BusinessProcess
        assert is_permitted(Triggering, BusinessEvent, BusinessProcess) is True


class TestStrategyLayerRules:
    """Strategy layer entries from FEAT-16.2."""

    def test_resource_assigned_to_capability(self) -> None:
        from pyarchi.metamodel.strategy import Capability, Resource
        assert is_permitted(Assignment, Resource, Capability) is True

    def test_capability_triggers_capability(self) -> None:
        from pyarchi.metamodel.strategy import Capability
        assert is_permitted(Triggering, Capability, Capability) is True

    def test_value_stream_flow(self) -> None:
        from pyarchi.metamodel.strategy import ValueStream
        assert is_permitted(Flow, ValueStream, ValueStream) is True


class TestPhysicalLayerRules:
    def test_equipment_access_material(self) -> None:
        from pyarchi.metamodel.physical import Equipment, Material
        assert is_permitted(Access, Equipment, Material) is True


class TestDualPathMigration:
    """Placeholder structure for the dual-path compatibility test.

    The implementer must populate KNOWN_TRUE_TRIPLES from the old
    implementation before it is deleted. This is a migration artifact.
    """

    # KNOWN_TRUE_TRIPLES: set of (rel_type, src, tgt) that returned True
    # under the old procedural implementation. To be generated once.

    def test_no_regressions_placeholder(self) -> None:
        """Replace with actual parametrized regression check."""
        # The real test iterates KNOWN_TRUE_TRIPLES and asserts
        # is_permitted(rel, src, tgt) is True for each.
        pass
```

## Edge Cases

- `Resource` inherits from `StrategyStructureElement` -> `StructureElement`, NOT from `ActiveStructureElement`. It will NOT match `InternalActiveStructureElement` rules. The Assignment entries for Resource must be explicit.
- `CourseOfAction` inherits from `BehaviorElement` directly, not from `StrategyBehaviorElement`. It is NOT an `InternalBehaviorElement`. Rules targeting `InternalBehaviorElement` will NOT match `CourseOfAction`.
- `BusinessService` inherits from `ExternalBehaviorElement`, not `InternalBehaviorElement`. Same concern applies.
- The cache must be invalidated/rebuilt if new entries are appended to `_PERMISSION_TABLE` at runtime (not expected in normal usage, but the `_cache` global should be set to `None` if the table changes).
