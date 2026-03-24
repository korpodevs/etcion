"""Tests for FEAT-05.3 -- DependencyRelationship ABC and Serving."""

from __future__ import annotations

from typing import ClassVar

import pytest
from pydantic import ValidationError

from pyarchi.enums import Aspect, Layer, RelationshipCategory
from pyarchi.metamodel.concepts import Concept, Relationship
from pyarchi.metamodel.elements import ActiveStructureElement
from pyarchi.metamodel.relationships import (
    DependencyRelationship,
    Serving,
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


class TestDependencyRelationshipABC:
    def test_cannot_instantiate(self) -> None:
        e = _ConcreteElement(name="e")
        with pytest.raises(TypeError):
            DependencyRelationship(name="r", source=e, target=e)

    def test_category_is_dependency(self) -> None:
        assert DependencyRelationship.category is RelationshipCategory.DEPENDENCY

    def test_is_subclass_of_relationship(self) -> None:
        assert issubclass(DependencyRelationship, Relationship)

    def test_is_not_structural(self) -> None:
        assert not issubclass(DependencyRelationship, StructuralRelationship)


# ---------------------------------------------------------------------------
# Serving
# ---------------------------------------------------------------------------


class TestServing:
    @pytest.fixture()
    def pair(self) -> tuple[_ConcreteElement, _ConcreteElement]:
        return _ConcreteElement(name="a"), _ConcreteElement(name="b")

    def test_instantiation(self, pair: tuple[_ConcreteElement, _ConcreteElement]) -> None:
        a, b = pair
        r = Serving(name="s", source=a, target=b)
        assert r._type_name == "Serving"

    def test_category_inherited(self) -> None:
        assert Serving.category is RelationshipCategory.DEPENDENCY

    def test_is_dependency_relationship(self) -> None:
        assert issubclass(Serving, DependencyRelationship)

    def test_is_concept(self) -> None:
        assert issubclass(Serving, Concept)

    def test_is_derived_defaults_false(
        self, pair: tuple[_ConcreteElement, _ConcreteElement]
    ) -> None:
        a, b = pair
        r = Serving(name="s", source=a, target=b)
        assert r.is_derived is False

    def test_rejects_is_nested(self, pair: tuple[_ConcreteElement, _ConcreteElement]) -> None:
        a, b = pair
        with pytest.raises(ValidationError):
            Serving(name="s", source=a, target=b, is_nested=True)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Validation xfails
# ---------------------------------------------------------------------------


class TestDeferredValidation:
    @pytest.mark.xfail(
        strict=False,
        reason="Serving direction validation deferred to model-level (ADR-017 ss6)",
    )
    def test_serving_wrong_direction_raises(self) -> None:
        pytest.fail("Model-level validation not yet implemented")
