"""Tests for FEAT-05.8 -- OtherRelationship ABC and Specialization."""

from __future__ import annotations

from typing import ClassVar

import pytest

from pyarchi.enums import Aspect, Layer, RelationshipCategory
from pyarchi.metamodel.concepts import Concept, Relationship
from pyarchi.metamodel.elements import ActiveStructureElement, BehaviorElement
from pyarchi.metamodel.relationships import (
    DependencyRelationship,
    OtherRelationship,
    Specialization,
    StructuralRelationship,
)

# ---------------------------------------------------------------------------
# Test-local concrete element stubs
# ---------------------------------------------------------------------------


class _ConcreteActive(ActiveStructureElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE

    @property
    def _type_name(self) -> str:
        return "StubActive"


class _ConcreteBehavior(BehaviorElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR

    @property
    def _type_name(self) -> str:
        return "StubBehavior"


# ---------------------------------------------------------------------------
# ABC
# ---------------------------------------------------------------------------


class TestOtherRelationshipABC:
    def test_cannot_instantiate(self) -> None:
        e = _ConcreteActive(name="e")
        with pytest.raises(TypeError):
            OtherRelationship(name="r", source=e, target=e)

    def test_category_is_other(self) -> None:
        assert OtherRelationship.category is RelationshipCategory.OTHER

    def test_is_subclass_of_relationship(self) -> None:
        assert issubclass(OtherRelationship, Relationship)

    def test_is_not_structural(self) -> None:
        assert not issubclass(OtherRelationship, StructuralRelationship)

    def test_is_not_dependency(self) -> None:
        assert not issubclass(OtherRelationship, DependencyRelationship)


# ---------------------------------------------------------------------------
# Specialization
# ---------------------------------------------------------------------------


class TestSpecialization:
    @pytest.fixture()
    def pair(self) -> tuple[_ConcreteActive, _ConcreteActive]:
        return _ConcreteActive(name="a"), _ConcreteActive(name="b")

    def test_instantiation(self, pair: tuple[_ConcreteActive, _ConcreteActive]) -> None:
        a, b = pair
        r = Specialization(name="spec", source=a, target=b)
        assert r._type_name == "Specialization"

    def test_category_inherited(self) -> None:
        assert Specialization.category is RelationshipCategory.OTHER

    def test_is_other_relationship(self) -> None:
        assert issubclass(Specialization, OtherRelationship)

    def test_is_concept(self) -> None:
        assert issubclass(Specialization, Concept)

    def test_same_type_construction_succeeds(self) -> None:
        a = _ConcreteActive(name="a")
        b = _ConcreteActive(name="b")
        r = Specialization(name="spec", source=a, target=b)
        assert r.source is a
        assert r.target is b

