"""Tests for FEAT-07.1 -- Business Abstract Bases."""

from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.business import (
    BusinessInternalActiveStructureElement,
    BusinessInternalBehaviorElement,
    BusinessPassiveStructureElement,
)
from pyarchi.metamodel.elements import (
    InternalActiveStructureElement,
    InternalBehaviorElement,
    PassiveStructureElement,
)


class TestBusinessABCsCannotInstantiate:
    """Each ABC raises TypeError on direct instantiation."""

    @pytest.mark.parametrize(
        "cls",
        [
            BusinessInternalActiveStructureElement,
            BusinessInternalBehaviorElement,
            BusinessPassiveStructureElement,
        ],
    )
    def test_cannot_instantiate(self, cls: type) -> None:
        with pytest.raises(TypeError):
            cls(name="test")


class TestBusinessInternalActiveStructureElementInheritance:
    def test_is_internal_active_structure_element(self) -> None:
        assert issubclass(BusinessInternalActiveStructureElement, InternalActiveStructureElement)

    def test_layer(self) -> None:
        assert BusinessInternalActiveStructureElement.layer is Layer.BUSINESS

    def test_aspect(self) -> None:
        assert BusinessInternalActiveStructureElement.aspect is Aspect.ACTIVE_STRUCTURE


class TestBusinessInternalBehaviorElementInheritance:
    def test_is_internal_behavior_element(self) -> None:
        assert issubclass(BusinessInternalBehaviorElement, InternalBehaviorElement)

    def test_layer(self) -> None:
        assert BusinessInternalBehaviorElement.layer is Layer.BUSINESS

    def test_aspect(self) -> None:
        assert BusinessInternalBehaviorElement.aspect is Aspect.BEHAVIOR


class TestBusinessPassiveStructureElementInheritance:
    def test_is_passive_structure_element(self) -> None:
        assert issubclass(BusinessPassiveStructureElement, PassiveStructureElement)

    def test_layer(self) -> None:
        assert BusinessPassiveStructureElement.layer is Layer.BUSINESS

    def test_aspect(self) -> None:
        assert BusinessPassiveStructureElement.aspect is Aspect.PASSIVE_STRUCTURE
