"""Tests for FEAT-05.7 -- Dynamic Relationships (Triggering, Flow)."""

from __future__ import annotations

from typing import ClassVar

import pytest

from pyarchi.enums import Aspect, Layer, RelationshipCategory
from pyarchi.metamodel.concepts import Concept, Relationship
from pyarchi.metamodel.elements import ActiveStructureElement
from pyarchi.metamodel.relationships import (
    DynamicRelationship,
    Flow,
    StructuralRelationship,
    Triggering,
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


class TestDynamicRelationshipABC:
    def test_cannot_instantiate(self) -> None:
        e = _ConcreteElement(name="e")
        with pytest.raises(TypeError):
            DynamicRelationship(name="r", source=e, target=e)

    def test_category_is_dynamic(self) -> None:
        assert DynamicRelationship.category is RelationshipCategory.DYNAMIC

    def test_is_subclass_of_relationship(self) -> None:
        assert issubclass(DynamicRelationship, Relationship)

    def test_is_not_structural(self) -> None:
        assert not issubclass(DynamicRelationship, StructuralRelationship)


# ---------------------------------------------------------------------------
# Triggering
# ---------------------------------------------------------------------------


class TestTriggering:
    @pytest.fixture()
    def pair(self) -> tuple[_ConcreteElement, _ConcreteElement]:
        return _ConcreteElement(name="a"), _ConcreteElement(name="b")

    def test_instantiation(self, pair: tuple[_ConcreteElement, _ConcreteElement]) -> None:
        a, b = pair
        r = Triggering(name="t", source=a, target=b)
        assert r._type_name == "Triggering"

    def test_category_inherited(self) -> None:
        assert Triggering.category is RelationshipCategory.DYNAMIC

    def test_is_concept(self) -> None:
        assert issubclass(Triggering, Concept)


# ---------------------------------------------------------------------------
# Flow
# ---------------------------------------------------------------------------


class TestFlow:
    @pytest.fixture()
    def pair(self) -> tuple[_ConcreteElement, _ConcreteElement]:
        return _ConcreteElement(name="a"), _ConcreteElement(name="b")

    def test_instantiation(self, pair: tuple[_ConcreteElement, _ConcreteElement]) -> None:
        a, b = pair
        r = Flow(name="f", source=a, target=b)
        assert r._type_name == "Flow"

    def test_flow_type_defaults_to_none(
        self, pair: tuple[_ConcreteElement, _ConcreteElement]
    ) -> None:
        a, b = pair
        r = Flow(name="f", source=a, target=b)
        assert r.flow_type is None

    def test_flow_type_accepts_string(
        self, pair: tuple[_ConcreteElement, _ConcreteElement]
    ) -> None:
        a, b = pair
        r = Flow(name="f", source=a, target=b, flow_type="data")
        assert r.flow_type == "data"

    def test_category_inherited(self) -> None:
        assert Flow.category is RelationshipCategory.DYNAMIC


# ---------------------------------------------------------------------------
# is_nested rejection (STORY-05.7.4, 05.7.7)
# ---------------------------------------------------------------------------


class TestIsNestedRejection:
    def test_triggering_rejects_is_nested(self) -> None:
        a, b = _ConcreteElement(name="a"), _ConcreteElement(name="b")
        with pytest.raises(Exception):  # noqa: B017
            Triggering(name="t", source=a, target=b, is_nested=True)  # type: ignore[call-arg]

    def test_flow_rejects_is_nested(self) -> None:
        a, b = _ConcreteElement(name="a"), _ConcreteElement(name="b")
        with pytest.raises(Exception):  # noqa: B017
            Flow(name="f", source=a, target=b, is_nested=True)  # type: ignore[call-arg]
