"""Tests for FEAT-16.1: Declarative permission table and cached lookup."""

from __future__ import annotations

import warnings

import pytest

from pyarchi.metamodel.concepts import Element, Relationship
from pyarchi.metamodel.relationships import (
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
from pyarchi.validation.permissions import (
    _PERMISSION_TABLE,
    _UNIVERSAL_SAME_TYPE,
    PermissionRule,
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
