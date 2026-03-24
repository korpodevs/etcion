"""Tests for FEAT-05.6 -- Association Relationship and AssociationDirection enum."""

from __future__ import annotations

from typing import ClassVar

import pytest

from pyarchi.enums import Aspect, AssociationDirection, Layer, RelationshipCategory
from pyarchi.metamodel.concepts import Relationship
from pyarchi.metamodel.elements import ActiveStructureElement, BehaviorElement
from pyarchi.metamodel.relationships import Association, DependencyRelationship

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
# AssociationDirection enum ratification
# ---------------------------------------------------------------------------


class TestAssociationDirectionEnum:
    def test_undirected(self) -> None:
        assert AssociationDirection.UNDIRECTED.value == "Undirected"

    def test_directed(self) -> None:
        assert AssociationDirection.DIRECTED.value == "Directed"

    def test_exactly_two_members(self) -> None:
        assert len(AssociationDirection) == 2


# ---------------------------------------------------------------------------
# Association relationship
# ---------------------------------------------------------------------------


class TestAssociation:
    @pytest.fixture()
    def pair(self) -> tuple[_ConcreteActive, _ConcreteActive]:
        return _ConcreteActive(name="a"), _ConcreteActive(name="b")

    def test_instantiation(self, pair: tuple[_ConcreteActive, _ConcreteActive]) -> None:
        a, b = pair
        r = Association(name="assoc", source=a, target=b)
        assert r._type_name == "Association"

    def test_direction_defaults_to_undirected(
        self, pair: tuple[_ConcreteActive, _ConcreteActive]
    ) -> None:
        a, b = pair
        r = Association(name="assoc", source=a, target=b)
        assert r.direction is AssociationDirection.UNDIRECTED

    def test_directed_association(self, pair: tuple[_ConcreteActive, _ConcreteActive]) -> None:
        a, b = pair
        r = Association(name="assoc", source=a, target=b, direction=AssociationDirection.DIRECTED)
        assert r.direction is AssociationDirection.DIRECTED

    def test_is_dependency_relationship(self) -> None:
        assert issubclass(Association, DependencyRelationship)

    def test_category_inherited(self) -> None:
        assert Association.category is RelationshipCategory.DEPENDENCY

    def test_accepts_cross_type_source_target(self) -> None:
        """Association is universally permitted -- construction accepts any concepts."""
        a = _ConcreteActive(name="a")
        b = _ConcreteBehavior(name="b")
        r = Association(name="assoc", source=a, target=b)
        assert r.source is a
        assert r.target is b

    def test_accepts_relationship_as_target(self) -> None:
        """Association can target a Relationship (per spec, any two concepts)."""

        class _StubRel(Relationship):
            category: ClassVar[RelationshipCategory] = RelationshipCategory.OTHER

            @property
            def _type_name(self) -> str:
                return "StubRel"

        a = _ConcreteActive(name="a")
        b = _ConcreteActive(name="b")
        rel = _StubRel(name="r", source=a, target=b)
        assoc = Association(name="assoc", source=a, target=rel)
        assert assoc.target is rel
