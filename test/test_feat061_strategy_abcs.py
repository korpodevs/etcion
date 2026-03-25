"""Tests for FEAT-06.1 -- Strategy Abstract Bases."""

from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import (
    ActiveStructureElement,
    BehaviorElement,
    StructureElement,
)
from pyarchi.metamodel.strategy import (
    StrategyBehaviorElement,
    StrategyStructureElement,
)


class TestStrategyABCsCannotInstantiate:
    """Each ABC raises TypeError on direct instantiation."""

    @pytest.mark.parametrize(
        "cls",
        [StrategyStructureElement, StrategyBehaviorElement],
    )
    def test_cannot_instantiate(self, cls: type) -> None:
        with pytest.raises(TypeError):
            cls(name="test")


class TestStrategyStructureElementInheritance:
    def test_is_structure_element(self) -> None:
        assert issubclass(StrategyStructureElement, StructureElement)

    def test_is_not_active_structure_element(self) -> None:
        assert not issubclass(StrategyStructureElement, ActiveStructureElement)

    def test_layer(self) -> None:
        assert StrategyStructureElement.layer is Layer.STRATEGY

    def test_aspect(self) -> None:
        assert StrategyStructureElement.aspect is Aspect.ACTIVE_STRUCTURE


class TestStrategyBehaviorElementInheritance:
    def test_is_behavior_element(self) -> None:
        assert issubclass(StrategyBehaviorElement, BehaviorElement)

    def test_layer(self) -> None:
        assert StrategyBehaviorElement.layer is Layer.STRATEGY

    def test_aspect(self) -> None:
        assert StrategyBehaviorElement.aspect is Aspect.BEHAVIOR
