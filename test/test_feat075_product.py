"""Tests for FEAT-07.5 -- Product composite element."""

from __future__ import annotations

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.business import (
    BusinessInternalActiveStructureElement,
    Product,
)
from pyarchi.metamodel.elements import CompositeElement


class TestProductInstantiation:
    def test_can_instantiate(self) -> None:
        p = Product(name="Insurance Product")
        assert p.name == "Insurance Product"

    def test_type_name(self) -> None:
        p = Product(name="x")
        assert p._type_name == "Product"


class TestProductInheritance:
    def test_is_composite_element(self) -> None:
        assert isinstance(Product(name="x"), CompositeElement)

    def test_is_not_business_internal_active_structure(self) -> None:
        assert not isinstance(Product(name="x"), BusinessInternalActiveStructureElement)


class TestProductClassVars:
    def test_layer(self) -> None:
        assert Product.layer is Layer.BUSINESS

    def test_aspect(self) -> None:
        assert Product.aspect is Aspect.COMPOSITE


class TestProductNotation:
    def test_corner_shape(self) -> None:
        assert Product.notation.corner_shape == "square"

    def test_layer_color(self) -> None:
        assert Product.notation.layer_color == "#FFFFB5"

    def test_badge_letter(self) -> None:
        assert Product.notation.badge_letter == "B"
