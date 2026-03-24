"""Tests for FEAT-05.11 -- Appendix B Permission Table and exports."""

from __future__ import annotations

from typing import ClassVar

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import ActiveStructureElement, BehaviorElement
from pyarchi.metamodel.relationships import (
    Aggregation,
    Association,
    Composition,
    Serving,
    Specialization,
)
from pyarchi.validation.permissions import is_permitted

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
        import pyarchi

        assert hasattr(pyarchi, name), f"{name} not exported from pyarchi"
