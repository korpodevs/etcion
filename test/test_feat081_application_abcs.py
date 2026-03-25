"""Tests for FEAT-08.1 -- Application Abstract Bases."""

from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.application import (
    ApplicationInternalActiveStructureElement,
    ApplicationInternalBehaviorElement,
)
from pyarchi.metamodel.elements import (
    InternalActiveStructureElement,
    InternalBehaviorElement,
)


class TestApplicationABCsCannotInstantiate:
    """Each ABC raises TypeError on direct instantiation."""

    @pytest.mark.parametrize(
        "cls",
        [
            ApplicationInternalActiveStructureElement,
            ApplicationInternalBehaviorElement,
        ],
    )
    def test_cannot_instantiate(self, cls: type) -> None:
        with pytest.raises(TypeError):
            cls(name="test")


class TestApplicationInternalActiveStructureElementInheritance:
    def test_is_internal_active_structure_element(self) -> None:
        assert issubclass(ApplicationInternalActiveStructureElement, InternalActiveStructureElement)

    def test_layer(self) -> None:
        assert ApplicationInternalActiveStructureElement.layer is Layer.APPLICATION

    def test_aspect(self) -> None:
        assert ApplicationInternalActiveStructureElement.aspect is Aspect.ACTIVE_STRUCTURE


class TestApplicationInternalBehaviorElementInheritance:
    def test_is_internal_behavior_element(self) -> None:
        assert issubclass(ApplicationInternalBehaviorElement, InternalBehaviorElement)

    def test_layer(self) -> None:
        assert ApplicationInternalBehaviorElement.layer is Layer.APPLICATION

    def test_aspect(self) -> None:
        assert ApplicationInternalBehaviorElement.aspect is Aspect.BEHAVIOR
