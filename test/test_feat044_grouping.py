"""Tests for FEAT-04.4 -- Grouping (Concrete)."""

from __future__ import annotations

from typing import ClassVar

import pytest

from pyarchi.enums import Aspect, Layer, RelationshipCategory
from pyarchi.metamodel.concepts import Concept, Element, Relationship
from pyarchi.metamodel.elements import CompositeElement, Grouping


class TestGroupingInstantiation:
    def test_can_instantiate(self) -> None:
        g = Grouping(name="g")
        assert g.name == "g"

    def test_members_defaults_to_empty_list(self) -> None:
        g = Grouping(name="g")
        assert g.members == []

    def test_type_name(self) -> None:
        g = Grouping(name="g")
        assert g._type_name == "Grouping"


class TestGroupingClassification:
    def test_layer(self) -> None:
        assert Grouping.layer is Layer.IMPLEMENTATION_MIGRATION

    def test_aspect(self) -> None:
        assert Grouping.aspect is Aspect.COMPOSITE


class TestGroupingInheritance:
    def test_is_composite_element(self) -> None:
        assert isinstance(Grouping(name="g"), CompositeElement)

    def test_is_element(self) -> None:
        assert isinstance(Grouping(name="g"), Element)

    def test_is_concept(self) -> None:
        assert isinstance(Grouping(name="g"), Concept)


class TestGroupingMembers:
    """Grouping accepts both Element and Relationship members."""

    class _StubElement(Element):
        layer: ClassVar[Layer] = Layer.BUSINESS
        aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE

        @property
        def _type_name(self) -> str:
            return "Stub"

    class _StubRelationship(Relationship):
        category: ClassVar[RelationshipCategory] = RelationshipCategory.OTHER

        @property
        def _type_name(self) -> str:
            return "StubRel"

    def test_accepts_element_member(self) -> None:
        elem = self._StubElement(name="e")
        g = Grouping(name="g", members=[elem])
        assert len(g.members) == 1

    def test_accepts_relationship_member(self) -> None:
        elem = self._StubElement(name="e")
        rel = self._StubRelationship(name="r", source=elem, target=elem)
        g = Grouping(name="g", members=[rel])
        assert len(g.members) == 1

    def test_accepts_mixed_members(self) -> None:
        elem = self._StubElement(name="e")
        rel = self._StubRelationship(name="r", source=elem, target=elem)
        g = Grouping(name="g", members=[elem, rel])
        assert len(g.members) == 2
