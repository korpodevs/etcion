"""Tests for FEAT-05.2 -- Structural Relationships."""

from __future__ import annotations

from typing import ClassVar

import pytest

from pyarchi.enums import Aspect, Layer, RelationshipCategory
from pyarchi.metamodel.concepts import Concept, Relationship
from pyarchi.metamodel.elements import ActiveStructureElement
from pyarchi.metamodel.relationships import (
    Aggregation,
    Assignment,
    Composition,
    Realization,
    StructuralRelationship,
)

# ---------------------------------------------------------------------------
# Test-local concrete element stub
# ---------------------------------------------------------------------------


class _ConcreteElement(ActiveStructureElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE

    @property
    def _type_name(self) -> str:
        return "Stub"


# ---------------------------------------------------------------------------
# ABC
# ---------------------------------------------------------------------------


class TestStructuralRelationshipABC:
    def test_cannot_instantiate(self) -> None:
        e = _ConcreteElement(name="e")
        with pytest.raises(TypeError):
            StructuralRelationship(name="r", source=e, target=e)  # type: ignore[abstract, call-arg]

    def test_category_is_structural(self) -> None:
        assert StructuralRelationship.category is RelationshipCategory.STRUCTURAL

    def test_is_subclass_of_relationship(self) -> None:
        assert issubclass(StructuralRelationship, Relationship)


# ---------------------------------------------------------------------------
# Concrete types
# ---------------------------------------------------------------------------


class TestConcreteStructuralTypes:
    @pytest.fixture()
    def pair(self) -> tuple[_ConcreteElement, _ConcreteElement]:
        return _ConcreteElement(name="a"), _ConcreteElement(name="b")

    @pytest.mark.parametrize(
        ("cls", "expected_name"),
        [
            (Composition, "Composition"),
            (Aggregation, "Aggregation"),
            (Assignment, "Assignment"),
            (Realization, "Realization"),
        ],
    )
    def test_instantiation_and_type_name(
        self,
        pair: tuple[_ConcreteElement, _ConcreteElement],
        cls: type,
        expected_name: str,
    ) -> None:
        a, b = pair
        r = cls(name="r", source=a, target=b)
        assert r._type_name == expected_name

    @pytest.mark.parametrize("cls", [Composition, Aggregation, Assignment, Realization])
    def test_is_structural_relationship(self, cls: type) -> None:
        assert issubclass(cls, StructuralRelationship)

    @pytest.mark.parametrize("cls", [Composition, Aggregation, Assignment, Realization])
    def test_category_inherited(self, cls: type) -> None:
        assert cls.category is RelationshipCategory.STRUCTURAL

    @pytest.mark.parametrize("cls", [Composition, Aggregation, Assignment, Realization])
    def test_is_concept(self, cls: type) -> None:
        assert issubclass(cls, Concept)


# ---------------------------------------------------------------------------
# is_nested
# ---------------------------------------------------------------------------


class TestIsNested:
    def test_defaults_to_false(self) -> None:
        a, b = _ConcreteElement(name="a"), _ConcreteElement(name="b")
        c = Composition(name="c", source=a, target=b)
        assert c.is_nested is False

    def test_set_to_true(self) -> None:
        a, b = _ConcreteElement(name="a"), _ConcreteElement(name="b")
        c = Composition(name="c", source=a, target=b, is_nested=True)
        assert c.is_nested is True
