"""Tests for FEAT-04.3 -- MotivationElement and CompositeElement."""

from __future__ import annotations

import pytest

from pyarchi.metamodel.concepts import Element
from pyarchi.metamodel.elements import CompositeElement, MotivationElement


class TestMotivationCompositeABC:
    """Each ABC raises TypeError on direct instantiation."""

    @pytest.mark.parametrize("cls", [MotivationElement, CompositeElement])
    def test_cannot_instantiate(self, cls: type) -> None:
        with pytest.raises(TypeError):
            cls(name="test")


class TestMotivationCompositeInheritance:
    def test_motivation_is_element(self) -> None:
        assert issubclass(MotivationElement, Element)

    def test_composite_is_element(self) -> None:
        assert issubclass(CompositeElement, Element)

    def test_motivation_is_not_composite(self) -> None:
        assert not issubclass(MotivationElement, CompositeElement)

    def test_composite_is_not_motivation(self) -> None:
        assert not issubclass(CompositeElement, MotivationElement)
