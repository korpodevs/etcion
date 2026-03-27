"""Merged tests for test_permissions."""

from __future__ import annotations

import warnings
from typing import ClassVar

import pytest

import etcion.validation.permissions as _perm_mod
import etcion.validation.permissions as _perm_module
from etcion import BusinessActor, BusinessRole, Serving, warm_cache
from etcion.enums import Aspect, Layer
from etcion.metamodel.application import (
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
from etcion.metamodel.business import (
    BusinessCollaboration,
    BusinessEvent,
    BusinessFunction,
    BusinessInteraction,
    BusinessInterface,
    BusinessObject,
    BusinessProcess,
    BusinessService,
    Contract,
    Product,
    Representation,
)
from etcion.metamodel.concepts import Element, Relationship
from etcion.metamodel.elements import ActiveStructureElement, BehaviorElement
from etcion.metamodel.implementation_migration import (
    Deliverable,
    Gap,
    ImplementationEvent,
    Plateau,
    WorkPackage,
)
from etcion.metamodel.motivation import (
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
from etcion.metamodel.physical import (
    DistributionNetwork,
    Equipment,
    Facility,
    Material,
)
from etcion.metamodel.relationships import (
    Access,
    Aggregation,
    Assignment,
    Association,
    Composition,
    Flow,
    Influence,
    Realization,
    Serving,
    Specialization,
    Triggering,
)
from etcion.metamodel.strategy import (
    Capability,
    CourseOfAction,
    Resource,
    ValueStream,
)
from etcion.metamodel.technology import (
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
from etcion.validation.permissions import (
    _PERMISSION_TABLE,
    _UNIVERSAL_SAME_TYPE,
    PermissionRule,
    is_permitted,
)

# ---------------------------------------------------------------------------
# Test-local concrete element stubs
# ---------------------------------------------------------------------------


class _ConcreteActiveA(ActiveStructureElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE

    @property
    def _type_name(self) -> str:
        return "StubActiveA"


class _ConcreteActiveB(ActiveStructureElement):
    layer: ClassVar[Layer] = Layer.APPLICATION
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE

    @property
    def _type_name(self) -> str:
        return "StubActiveB"


class _ConcreteBehavior(BehaviorElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR

    @property
    def _type_name(self) -> str:
        return "StubBehavior"


# ---------------------------------------------------------------------------
# Universal rules
# ---------------------------------------------------------------------------


class TestUniversalRules:
    def test_composition_same_type_permitted(self) -> None:
        assert is_permitted(Composition, _ConcreteActiveA, _ConcreteActiveA) is True

    def test_aggregation_same_type_permitted(self) -> None:
        assert is_permitted(Aggregation, _ConcreteActiveA, _ConcreteActiveA) is True

    def test_specialization_same_type_permitted(self) -> None:
        assert is_permitted(Specialization, _ConcreteActiveA, _ConcreteActiveA) is True

    def test_specialization_cross_type_forbidden(self) -> None:
        assert is_permitted(Specialization, _ConcreteActiveA, _ConcreteBehavior) is False

    def test_association_always_permitted(self) -> None:
        assert is_permitted(Association, _ConcreteActiveA, _ConcreteBehavior) is True

    def test_association_same_type_permitted(self) -> None:
        assert is_permitted(Association, _ConcreteActiveA, _ConcreteActiveA) is True


# ---------------------------------------------------------------------------
# Representative Appendix B triples
# ---------------------------------------------------------------------------


class TestRepresentativeTriples:
    def test_is_permitted_returns_bool(self) -> None:
        result = is_permitted(Serving, _ConcreteActiveA, _ConcreteBehavior)
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# __init__.py exports
# ---------------------------------------------------------------------------


class TestExports:
    @pytest.mark.parametrize(
        "name",
        [
            "RelationshipCategory",
            "AccessMode",
            "AssociationDirection",
            "InfluenceSign",
            "JunctionType",
            "StructuralRelationship",
            "DependencyRelationship",
            "DynamicRelationship",
            "OtherRelationship",
            "Composition",
            "Aggregation",
            "Assignment",
            "Realization",
            "Serving",
            "Access",
            "Influence",
            "Association",
            "Triggering",
            "Flow",
            "Specialization",
            "Junction",
            "DerivationEngine",
            "is_permitted",
        ],
    )
    def test_public_api_export(self, name: str) -> None:
        import etcion

        assert hasattr(etcion, name), f"{name} not exported from etcion"


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

    def test_table_is_list(self) -> None:
        assert isinstance(_PERMISSION_TABLE, list)

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
        from etcion.metamodel.business import BusinessActor

        assert is_permitted(Composition, BusinessActor, BusinessActor) is True

    def test_composition_different_type(self) -> None:
        from etcion.metamodel.business import BusinessActor, BusinessRole

        assert is_permitted(Composition, BusinessActor, BusinessRole) is False

    def test_aggregation_same_type(self) -> None:
        from etcion.metamodel.business import BusinessRole

        assert is_permitted(Aggregation, BusinessRole, BusinessRole) is True

    def test_specialization_same_type(self) -> None:
        from etcion.metamodel.business import BusinessActor

        assert is_permitted(Specialization, BusinessActor, BusinessActor) is True

    def test_specialization_different_type(self) -> None:
        from etcion.metamodel.business import BusinessActor, BusinessRole

        assert is_permitted(Specialization, BusinessActor, BusinessRole) is False

    def test_association_always_true(self) -> None:
        from etcion.metamodel.business import BusinessActor
        from etcion.metamodel.technology import Artifact

        assert is_permitted(Association, BusinessActor, Artifact) is True

    def test_composite_element_to_relationship(self) -> None:
        from etcion.metamodel.elements import Grouping

        assert is_permitted(Composition, Grouping, Assignment) is True


class TestDeprecationSpecialCase:
    """Realization(WorkPackage, Deliverable) returns True with DeprecationWarning."""

    def test_permitted_with_warning(self) -> None:
        from etcion.metamodel.implementation_migration import Deliverable, WorkPackage

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = is_permitted(Realization, WorkPackage, Deliverable)
        assert result is True
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)


class TestCachedLookup:
    """Table-based rules resolve correctly via the cache."""

    def test_assignment_business_active_to_behavior(self) -> None:
        from etcion.metamodel.business import BusinessActor, BusinessProcess

        assert is_permitted(Assignment, BusinessActor, BusinessProcess) is True

    def test_assignment_passive_to_behavior_prohibited(self) -> None:
        from etcion.metamodel.business import BusinessObject, BusinessProcess

        assert is_permitted(Assignment, BusinessObject, BusinessProcess) is False

    def test_serving_app_to_business(self) -> None:
        from etcion.metamodel.application import ApplicationService
        from etcion.metamodel.business import BusinessProcess

        assert is_permitted(Serving, ApplicationService, BusinessProcess) is True

    def test_serving_passive_source_prohibited(self) -> None:
        from etcion.metamodel.application import DataObject
        from etcion.metamodel.business import BusinessProcess

        assert is_permitted(Serving, DataObject, BusinessProcess) is False

    def test_realization_app_behavior_to_business_behavior(self) -> None:
        from etcion.metamodel.application import ApplicationFunction
        from etcion.metamodel.business import BusinessProcess

        assert is_permitted(Realization, ApplicationFunction, BusinessProcess) is True

    def test_realization_target_business_active_prohibited(self) -> None:
        from etcion.metamodel.application import ApplicationFunction
        from etcion.metamodel.business import BusinessActor

        assert is_permitted(Realization, ApplicationFunction, BusinessActor) is False

    def test_influence_motivation_to_motivation(self) -> None:
        from etcion.metamodel.motivation import Driver, Goal

        assert is_permitted(Influence, Driver, Goal) is True

    def test_triggering_business_intra_layer(self) -> None:
        from etcion.metamodel.business import BusinessFunction, BusinessProcess

        assert is_permitted(Triggering, BusinessProcess, BusinessFunction) is True

    def test_flow_app_intra_layer(self) -> None:
        from etcion.metamodel.application import ApplicationFunction, ApplicationProcess

        assert is_permitted(Flow, ApplicationProcess, ApplicationFunction) is True

    def test_access_active_to_passive(self) -> None:
        from etcion.metamodel.business import BusinessActor, BusinessObject

        assert is_permitted(Access, BusinessActor, BusinessObject) is True

    def test_unknown_triple_returns_false(self) -> None:
        from etcion.metamodel.motivation import Goal
        from etcion.metamodel.technology import Artifact

        assert is_permitted(Triggering, Goal, Artifact) is False


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
        import etcion.metamodel.business as biz

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
        import etcion.metamodel.business as biz
        from etcion.metamodel.business import BusinessActor

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
        import etcion.metamodel.technology as tech

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
        import etcion.metamodel.business as biz

        src_cls = getattr(biz, passive)
        assert is_permitted(Access, src_cls, biz.BusinessObject) is False

    def test_business_event_not_matched_by_internal_behavior(self) -> None:
        """BusinessEvent is NOT a BusinessInternalBehaviorElement subclass."""
        from etcion.metamodel.business import BusinessEvent, BusinessInternalBehaviorElement

        assert not issubclass(BusinessEvent, BusinessInternalBehaviorElement)

    def test_business_event_triggering_explicit_entry(self) -> None:
        from etcion.metamodel.business import BusinessEvent, BusinessProcess

        assert is_permitted(Triggering, BusinessEvent, BusinessProcess) is True


class TestStrategyLayerRules:
    """Strategy layer entries from FEAT-16.2."""

    # St1: Resource -> Capability via Assignment
    def test_resource_assigned_to_capability(self) -> None:
        from etcion.metamodel.strategy import Capability, Resource

        assert is_permitted(Assignment, Resource, Capability) is True

    # St2: Resource -> ValueStream via Assignment
    def test_resource_assigned_to_value_stream(self) -> None:
        from etcion.metamodel.strategy import Resource, ValueStream

        assert is_permitted(Assignment, Resource, ValueStream) is True

    # St3: Resource -> CourseOfAction via Assignment
    def test_resource_assigned_to_course_of_action(self) -> None:
        from etcion.metamodel.strategy import CourseOfAction, Resource

        assert is_permitted(Assignment, Resource, CourseOfAction) is True

    # St4: Capability -> Capability via Serving
    def test_capability_serves_capability(self) -> None:
        from etcion.metamodel.strategy import Capability

        assert is_permitted(Serving, Capability, Capability) is True

    # St5: ValueStream -> Capability via Serving
    def test_value_stream_serves_capability(self) -> None:
        from etcion.metamodel.strategy import Capability, ValueStream

        assert is_permitted(Serving, ValueStream, Capability) is True

    # St6: Capability -> Capability via Triggering
    def test_capability_triggers_capability(self) -> None:
        from etcion.metamodel.strategy import Capability

        assert is_permitted(Triggering, Capability, Capability) is True

    # St7: ValueStream -> ValueStream via Triggering
    def test_value_stream_triggers_value_stream(self) -> None:
        from etcion.metamodel.strategy import ValueStream

        assert is_permitted(Triggering, ValueStream, ValueStream) is True

    # St8: ValueStream -> ValueStream via Flow
    def test_value_stream_flow(self) -> None:
        from etcion.metamodel.strategy import ValueStream

        assert is_permitted(Flow, ValueStream, ValueStream) is True

    # St9: CourseOfAction -> MotivationElement via Realization
    def test_course_of_action_realizes_motivation(self) -> None:
        from etcion.metamodel.motivation import Goal
        from etcion.metamodel.strategy import CourseOfAction

        assert is_permitted(Realization, CourseOfAction, Goal) is True


class TestPhysicalLayerRules:
    # Ph2: PhysicalActiveStructureElement -> Material via Access
    def test_equipment_access_material(self) -> None:
        from etcion.metamodel.physical import Equipment, Material

        assert is_permitted(Access, Equipment, Material) is True

    def test_facility_access_material(self) -> None:
        from etcion.metamodel.physical import Facility, Material

        assert is_permitted(Access, Facility, Material) is True

    def test_distribution_network_access_material(self) -> None:
        from etcion.metamodel.physical import DistributionNetwork, Material

        assert is_permitted(Access, DistributionNetwork, Material) is True

    # Ph3: Equipment -> Equipment via Serving
    def test_equipment_serves_equipment(self) -> None:
        from etcion.metamodel.physical import Equipment

        assert is_permitted(Serving, Equipment, Equipment) is True

    # Ph4: Facility -> Facility via Serving
    def test_facility_serves_facility(self) -> None:
        from etcion.metamodel.physical import Facility

        assert is_permitted(Serving, Facility, Facility) is True


class TestCrossLayerStrategyRules:
    """Cross-layer Strategy -> Core rules (X1-X4)."""

    # X1: BehaviorElement -> Capability via Realization
    def test_behavior_realizes_capability(self) -> None:
        from etcion.metamodel.business import BusinessProcess
        from etcion.metamodel.strategy import Capability

        assert is_permitted(Realization, BusinessProcess, Capability) is True

    # X2: BehaviorElement -> ValueStream via Realization
    def test_behavior_realizes_value_stream(self) -> None:
        from etcion.metamodel.business import BusinessProcess
        from etcion.metamodel.strategy import ValueStream

        assert is_permitted(Realization, BusinessProcess, ValueStream) is True

    # X3: StructureElement -> Resource via Realization
    def test_structure_realizes_resource(self) -> None:
        from etcion.metamodel.business import BusinessActor
        from etcion.metamodel.strategy import Resource

        assert is_permitted(Realization, BusinessActor, Resource) is True

    # X4: CourseOfAction -> MotivationElement via Realization (same as St9,
    # verified here in the cross-layer context)
    def test_course_of_action_cross_layer_realization(self) -> None:
        from etcion.metamodel.motivation import Principle
        from etcion.metamodel.strategy import CourseOfAction

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


# ---------------------------------------------------------------------------
# FEAT-16.3 Completeness Audit -- Helpers
# ---------------------------------------------------------------------------

MOTIVATION_TYPES = [
    Stakeholder,
    Driver,
    Assessment,
    Goal,
    Outcome,
    Principle,
    Requirement,
    Constraint,
    Meaning,
    Value,
]

BUSINESS_ACTIVE = [BusinessActor, BusinessRole, BusinessCollaboration]
BUSINESS_BEHAVIOR = [BusinessProcess, BusinessFunction, BusinessInteraction]
BUSINESS_PASSIVE = [BusinessObject, Contract, Representation]

APP_ACTIVE = [ApplicationComponent, ApplicationCollaboration]
APP_BEHAVIOR = [ApplicationFunction, ApplicationProcess, ApplicationInteraction]

TECH_ACTIVE = [
    Node,
    Device,
    SystemSoftware,
    TechnologyCollaboration,
    Path,
    CommunicationNetwork,
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
    """Triples that must return False per Appendix B or etcion prohibitions."""

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


class TestWarmCacheCallable:
    """warm_cache() is callable and produces a correct subsequent lookup."""

    def setup_method(self):
        # Ensure the cache starts cold so each test is isolated.
        _perm_module._cache = None

    def test_warm_cache_callable_without_error(self):
        """warm_cache() must not raise on a cold (None) cache."""
        warm_cache()  # must not raise

    def test_warm_cache_populates_cache(self):
        """After warm_cache(), _cache must be a non-empty dict."""
        warm_cache()
        assert isinstance(_perm_module._cache, dict)
        assert len(_perm_module._cache) > 0

    def test_is_permitted_succeeds_after_warm_cache(self):
        """is_permitted() must return a correct bool after warm_cache()."""
        warm_cache()
        result = is_permitted(Serving, BusinessActor, BusinessRole)
        assert isinstance(result, bool)

    def test_is_permitted_correct_true_result_after_warm_cache(self):
        """Serving(BusinessActor -> BusinessRole) is NOT permitted per Appendix B.

        BusinessActor is an active structure element, not a behavior or
        interface that serves. is_permitted must return False.
        """
        warm_cache()
        # BusinessActor -> BusinessRole via Serving is not in the table, so False.
        assert is_permitted(Serving, BusinessActor, BusinessRole) is False


class TestWarmCacheIdempotent:
    """warm_cache() is idempotent: calling it twice is safe."""

    def setup_method(self):
        _perm_module._cache = None

    def test_warm_cache_twice_does_not_raise(self):
        """Calling warm_cache() twice must not raise."""
        warm_cache()
        warm_cache()  # must not raise

    def test_warm_cache_twice_does_not_rebuild(self):
        """The same dict object is retained on the second call (no rebuild)."""
        warm_cache()
        first_cache = _perm_module._cache
        warm_cache()
        # Identity check: the same object in memory means no rebuild occurred.
        assert _perm_module._cache is first_cache

    def test_warm_cache_on_already_warm_cache_is_noop(self):
        """warm_cache() on an already-built cache leaves the cache unchanged."""
        # Warm the cache via is_permitted (lazy path).
        is_permitted(Serving, BusinessActor, BusinessRole)
        populated_cache = _perm_module._cache

        warm_cache()  # should be a no-op since cache is already set

        assert _perm_module._cache is populated_cache


class TestWarmCacheRebuildAfterReset:
    """After resetting _cache = None, warm_cache() rebuilds correctly."""

    def setup_method(self):
        _perm_module._cache = None

    def test_warm_cache_rebuilds_after_reset(self):
        """warm_cache() rebuilds cache after _cache is manually set to None."""
        # First warm.
        warm_cache()
        assert _perm_module._cache is not None

        # Simulate reset (e.g. by a test that modifies the module state).
        _perm_module._cache = None

        # Second warm should rebuild.
        warm_cache()
        assert isinstance(_perm_module._cache, dict)
        assert len(_perm_module._cache) > 0

    def test_is_permitted_correct_after_rebuild(self):
        """is_permitted() returns the correct answer after a reset + rebuild."""
        warm_cache()
        _perm_module._cache = None
        warm_cache()

        # Serving(BusinessActor -> BusinessRole) should be False.
        assert is_permitted(Serving, BusinessActor, BusinessRole) is False

    def test_warm_cache_exported_from_etcion(self):
        """warm_cache must be importable directly from etcion top-level."""
        # The import at the top of this module already validates this, but we
        # add an explicit assertion for test-report clarity.
        import etcion

        assert hasattr(etcion, "warm_cache")
        assert callable(etcion.warm_cache)

    def test_warm_cache_in_dunder_all(self):
        """warm_cache must appear in etcion.__all__."""
        import etcion

        assert "warm_cache" in etcion.__all__
