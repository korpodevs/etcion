"""Tests for FEAT-16.2: Hierarchical type matching and Appendix B completeness."""

from __future__ import annotations

import pytest

import pyarchi.validation.permissions as _perm_mod
from pyarchi.metamodel.relationships import (
    Access,
    Assignment,
    Flow,
    Realization,
    Serving,
    Triggering,
)
from pyarchi.validation.permissions import is_permitted


@pytest.fixture(autouse=True, scope="module")
def reset_permissions_cache() -> None:
    """Reset the lazy concrete-type cache before this module's tests run.

    Ensures that any entries added to ``_PERMISSION_TABLE`` for FEAT-16.2 are
    included in the cache even when a prior test module has already triggered
    a cache build.
    """
    _perm_mod._cache = None


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
        import pyarchi.metamodel.business as biz
        from pyarchi.metamodel.business import BusinessActor

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

    # St1: Resource -> Capability via Assignment
    def test_resource_assigned_to_capability(self) -> None:
        from pyarchi.metamodel.strategy import Capability, Resource

        assert is_permitted(Assignment, Resource, Capability) is True

    # St2: Resource -> ValueStream via Assignment
    def test_resource_assigned_to_value_stream(self) -> None:
        from pyarchi.metamodel.strategy import Resource, ValueStream

        assert is_permitted(Assignment, Resource, ValueStream) is True

    # St3: Resource -> CourseOfAction via Assignment
    def test_resource_assigned_to_course_of_action(self) -> None:
        from pyarchi.metamodel.strategy import CourseOfAction, Resource

        assert is_permitted(Assignment, Resource, CourseOfAction) is True

    # St4: Capability -> Capability via Serving
    def test_capability_serves_capability(self) -> None:
        from pyarchi.metamodel.strategy import Capability

        assert is_permitted(Serving, Capability, Capability) is True

    # St5: ValueStream -> Capability via Serving
    def test_value_stream_serves_capability(self) -> None:
        from pyarchi.metamodel.strategy import Capability, ValueStream

        assert is_permitted(Serving, ValueStream, Capability) is True

    # St6: Capability -> Capability via Triggering
    def test_capability_triggers_capability(self) -> None:
        from pyarchi.metamodel.strategy import Capability

        assert is_permitted(Triggering, Capability, Capability) is True

    # St7: ValueStream -> ValueStream via Triggering
    def test_value_stream_triggers_value_stream(self) -> None:
        from pyarchi.metamodel.strategy import ValueStream

        assert is_permitted(Triggering, ValueStream, ValueStream) is True

    # St8: ValueStream -> ValueStream via Flow
    def test_value_stream_flow(self) -> None:
        from pyarchi.metamodel.strategy import ValueStream

        assert is_permitted(Flow, ValueStream, ValueStream) is True

    # St9: CourseOfAction -> MotivationElement via Realization
    def test_course_of_action_realizes_motivation(self) -> None:
        from pyarchi.metamodel.motivation import Goal
        from pyarchi.metamodel.strategy import CourseOfAction

        assert is_permitted(Realization, CourseOfAction, Goal) is True


class TestPhysicalLayerRules:
    # Ph2: PhysicalActiveStructureElement -> Material via Access
    def test_equipment_access_material(self) -> None:
        from pyarchi.metamodel.physical import Equipment, Material

        assert is_permitted(Access, Equipment, Material) is True

    def test_facility_access_material(self) -> None:
        from pyarchi.metamodel.physical import Facility, Material

        assert is_permitted(Access, Facility, Material) is True

    def test_distribution_network_access_material(self) -> None:
        from pyarchi.metamodel.physical import DistributionNetwork, Material

        assert is_permitted(Access, DistributionNetwork, Material) is True

    # Ph3: Equipment -> Equipment via Serving
    def test_equipment_serves_equipment(self) -> None:
        from pyarchi.metamodel.physical import Equipment

        assert is_permitted(Serving, Equipment, Equipment) is True

    # Ph4: Facility -> Facility via Serving
    def test_facility_serves_facility(self) -> None:
        from pyarchi.metamodel.physical import Facility

        assert is_permitted(Serving, Facility, Facility) is True


class TestCrossLayerStrategyRules:
    """Cross-layer Strategy -> Core rules (X1-X4)."""

    # X1: BehaviorElement -> Capability via Realization
    def test_behavior_realizes_capability(self) -> None:
        from pyarchi.metamodel.business import BusinessProcess
        from pyarchi.metamodel.strategy import Capability

        assert is_permitted(Realization, BusinessProcess, Capability) is True

    # X2: BehaviorElement -> ValueStream via Realization
    def test_behavior_realizes_value_stream(self) -> None:
        from pyarchi.metamodel.business import BusinessProcess
        from pyarchi.metamodel.strategy import ValueStream

        assert is_permitted(Realization, BusinessProcess, ValueStream) is True

    # X3: StructureElement -> Resource via Realization
    def test_structure_realizes_resource(self) -> None:
        from pyarchi.metamodel.business import BusinessActor
        from pyarchi.metamodel.strategy import Resource

        assert is_permitted(Realization, BusinessActor, Resource) is True

    # X4: CourseOfAction -> MotivationElement via Realization (same as St9,
    # verified here in the cross-layer context)
    def test_course_of_action_cross_layer_realization(self) -> None:
        from pyarchi.metamodel.motivation import Principle
        from pyarchi.metamodel.strategy import CourseOfAction

        assert is_permitted(Realization, CourseOfAction, Principle) is True


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
