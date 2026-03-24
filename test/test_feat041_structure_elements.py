"""Tests for FEAT-04.1 -- StructureElement Hierarchy."""

from __future__ import annotations

import pytest

from pyarchi.metamodel.concepts import Element
from pyarchi.metamodel.elements import (
    ActiveStructureElement,
    ExternalActiveStructureElement,
    InternalActiveStructureElement,
    PassiveStructureElement,
    StructureElement,
)


class TestStructureElementHierarchyABC:
    """Each ABC raises TypeError on direct instantiation."""

    @pytest.mark.parametrize(
        "cls",
        [
            StructureElement,
            ActiveStructureElement,
            InternalActiveStructureElement,
            ExternalActiveStructureElement,
            PassiveStructureElement,
        ],
    )
    def test_cannot_instantiate(self, cls: type) -> None:
        with pytest.raises(TypeError):
            cls(name="test")


class TestStructureElementInheritance:
    """Verify issubclass relationships."""

    def test_structure_element_is_element(self) -> None:
        assert issubclass(StructureElement, Element)

    def test_active_structure_is_structure(self) -> None:
        assert issubclass(ActiveStructureElement, StructureElement)

    def test_internal_active_is_active(self) -> None:
        assert issubclass(InternalActiveStructureElement, ActiveStructureElement)

    def test_external_active_is_active(self) -> None:
        assert issubclass(ExternalActiveStructureElement, ActiveStructureElement)

    def test_passive_is_structure(self) -> None:
        assert issubclass(PassiveStructureElement, StructureElement)

    def test_passive_is_not_active(self) -> None:
        assert not issubclass(PassiveStructureElement, ActiveStructureElement)
