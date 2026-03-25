"""Tests for FEAT-09.1 -- Technology Abstract Bases."""

from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import (
    InternalActiveStructureElement,
    InternalBehaviorElement,
)
from pyarchi.metamodel.technology import (
    TechnologyInternalActiveStructureElement,
    TechnologyInternalBehaviorElement,
)


class TestTechnologyABCsCannotInstantiate:
    """Each ABC raises TypeError on direct instantiation."""

    @pytest.mark.parametrize(
        "cls",
        [
            TechnologyInternalActiveStructureElement,
            TechnologyInternalBehaviorElement,
        ],
    )
    def test_cannot_instantiate(self, cls: type) -> None:
        with pytest.raises(TypeError):
            cls(name="test")


class TestTechnologyInternalActiveStructureElementInheritance:
    def test_is_internal_active_structure_element(self) -> None:
        assert issubclass(TechnologyInternalActiveStructureElement, InternalActiveStructureElement)

    def test_layer(self) -> None:
        assert TechnologyInternalActiveStructureElement.layer is Layer.TECHNOLOGY

    def test_aspect(self) -> None:
        assert TechnologyInternalActiveStructureElement.aspect is Aspect.ACTIVE_STRUCTURE


class TestTechnologyInternalBehaviorElementInheritance:
    def test_is_internal_behavior_element(self) -> None:
        assert issubclass(TechnologyInternalBehaviorElement, InternalBehaviorElement)

    def test_layer(self) -> None:
        assert TechnologyInternalBehaviorElement.layer is Layer.TECHNOLOGY

    def test_aspect(self) -> None:
        assert TechnologyInternalBehaviorElement.aspect is Aspect.BEHAVIOR
