"""Tests for FEAT-12.3 -- Gap associative element."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.concepts import Element
from pyarchi.metamodel.elements import CompositeElement
from pyarchi.metamodel.implementation_migration import Gap, Plateau


@pytest.fixture()
def plateau_a() -> Plateau:
    return Plateau(name="Baseline")


@pytest.fixture()
def plateau_b() -> Plateau:
    return Plateau(name="Target")


class TestInstantiation:
    def test_can_instantiate(self, plateau_a: Plateau, plateau_b: Plateau) -> None:
        g = Gap(name="Migration Gap", plateau_a=plateau_a, plateau_b=plateau_b)
        assert g.name == "Migration Gap"

    def test_type_name(self, plateau_a: Plateau, plateau_b: Plateau) -> None:
        g = Gap(name="x", plateau_a=plateau_a, plateau_b=plateau_b)
        assert g._type_name == "Gap"


class TestInheritance:
    def test_is_element(self) -> None:
        assert issubclass(Gap, Element)

    def test_is_not_composite_element(self) -> None:
        assert not issubclass(Gap, CompositeElement)


class TestClassVars:
    def test_layer(self) -> None:
        assert Gap.layer is Layer.IMPLEMENTATION_MIGRATION

    def test_aspect(self) -> None:
        assert Gap.aspect is Aspect.COMPOSITE


class TestNotation:
    def test_layer_color(self) -> None:
        assert Gap.notation.layer_color == "#FFE0E0"

    def test_badge_letter(self) -> None:
        assert Gap.notation.badge_letter == "I"

    def test_corner_shape(self) -> None:
        assert Gap.notation.corner_shape == "square"


class TestMandatoryPlateaus:
    def test_missing_both_raises(self) -> None:
        with pytest.raises(ValidationError):
            Gap(name="x")  # type: ignore[call-arg]

    def test_missing_plateau_a_raises(self, plateau_b: Plateau) -> None:
        with pytest.raises(ValidationError):
            Gap(name="x", plateau_b=plateau_b)  # type: ignore[call-arg]

    def test_missing_plateau_b_raises(self, plateau_a: Plateau) -> None:
        with pytest.raises(ValidationError):
            Gap(name="x", plateau_a=plateau_a)  # type: ignore[call-arg]

    def test_plateau_references_stored(self, plateau_a: Plateau, plateau_b: Plateau) -> None:
        g = Gap(name="x", plateau_a=plateau_a, plateau_b=plateau_b)
        assert g.plateau_a is plateau_a
        assert g.plateau_b is plateau_b

    def test_same_plateau_for_both_allowed(self, plateau_a: Plateau) -> None:
        """Spec does not forbid same plateau for both references."""
        g = Gap(name="x", plateau_a=plateau_a, plateau_b=plateau_a)
        assert g.plateau_a is g.plateau_b
