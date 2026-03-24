"""Tests for FEAT-05.5 -- Influence Relationship and InfluenceSign enum."""

from __future__ import annotations

from typing import ClassVar

import pytest

from pyarchi.enums import Aspect, InfluenceSign, Layer, RelationshipCategory
from pyarchi.metamodel.elements import ActiveStructureElement
from pyarchi.metamodel.relationships import DependencyRelationship, Influence

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
# InfluenceSign enum ratification
# ---------------------------------------------------------------------------


class TestInfluenceSignEnum:
    def test_strong_positive(self) -> None:
        assert InfluenceSign.STRONG_POSITIVE.value == "++"

    def test_positive(self) -> None:
        assert InfluenceSign.POSITIVE.value == "+"

    def test_neutral(self) -> None:
        assert InfluenceSign.NEUTRAL.value == "0"

    def test_negative(self) -> None:
        assert InfluenceSign.NEGATIVE.value == "-"

    def test_strong_negative(self) -> None:
        assert InfluenceSign.STRONG_NEGATIVE.value == "--"

    def test_exactly_five_members(self) -> None:
        assert len(InfluenceSign) == 5


# ---------------------------------------------------------------------------
# Influence relationship
# ---------------------------------------------------------------------------


class TestInfluence:
    @pytest.fixture()
    def pair(self) -> tuple[_ConcreteElement, _ConcreteElement]:
        return _ConcreteElement(name="a"), _ConcreteElement(name="b")

    def test_instantiation(self, pair: tuple[_ConcreteElement, _ConcreteElement]) -> None:
        a, b = pair
        r = Influence(name="inf", source=a, target=b)
        assert r._type_name == "Influence"

    def test_sign_defaults_to_none(self, pair: tuple[_ConcreteElement, _ConcreteElement]) -> None:
        a, b = pair
        r = Influence(name="inf", source=a, target=b)
        assert r.sign is None

    def test_strength_defaults_to_none(
        self, pair: tuple[_ConcreteElement, _ConcreteElement]
    ) -> None:
        a, b = pair
        r = Influence(name="inf", source=a, target=b)
        assert r.strength is None

    @pytest.mark.parametrize("sign", list(InfluenceSign))
    def test_accepts_all_signs(
        self,
        pair: tuple[_ConcreteElement, _ConcreteElement],
        sign: InfluenceSign,
    ) -> None:
        a, b = pair
        r = Influence(name="inf", source=a, target=b, sign=sign)
        assert r.sign is sign

    def test_accepts_strength_string(self, pair: tuple[_ConcreteElement, _ConcreteElement]) -> None:
        a, b = pair
        r = Influence(name="inf", source=a, target=b, strength="high")
        assert r.strength == "high"

    def test_is_dependency_relationship(self) -> None:
        assert issubclass(Influence, DependencyRelationship)

    def test_category_inherited(self) -> None:
        assert Influence.category is RelationshipCategory.DEPENDENCY
