"""Tests for FEAT-05.4 -- Access Relationship and AccessMode enum."""

from __future__ import annotations

from typing import ClassVar

import pytest

from pyarchi.enums import AccessMode, Aspect, Layer, RelationshipCategory
from pyarchi.metamodel.elements import ActiveStructureElement
from pyarchi.metamodel.relationships import Access, DependencyRelationship

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
# AccessMode enum ratification
# ---------------------------------------------------------------------------


class TestAccessModeEnum:
    def test_read(self) -> None:
        assert AccessMode.READ.value == "Read"

    def test_write(self) -> None:
        assert AccessMode.WRITE.value == "Write"

    def test_read_write(self) -> None:
        assert AccessMode.READ_WRITE.value == "ReadWrite"

    def test_unspecified(self) -> None:
        assert AccessMode.UNSPECIFIED.value == "Unspecified"

    def test_exactly_four_members(self) -> None:
        assert len(AccessMode) == 4


# ---------------------------------------------------------------------------
# Access relationship
# ---------------------------------------------------------------------------


class TestAccess:
    @pytest.fixture()
    def pair(self) -> tuple[_ConcreteElement, _ConcreteElement]:
        return _ConcreteElement(name="a"), _ConcreteElement(name="b")

    def test_instantiation(self, pair: tuple[_ConcreteElement, _ConcreteElement]) -> None:
        a, b = pair
        r = Access(name="acc", source=a, target=b)
        assert r._type_name == "Access"

    def test_access_mode_defaults_to_unspecified(
        self, pair: tuple[_ConcreteElement, _ConcreteElement]
    ) -> None:
        a, b = pair
        r = Access(name="acc", source=a, target=b)
        assert r.access_mode is AccessMode.UNSPECIFIED

    @pytest.mark.parametrize("mode", list(AccessMode))
    def test_accepts_all_access_modes(
        self,
        pair: tuple[_ConcreteElement, _ConcreteElement],
        mode: AccessMode,
    ) -> None:
        a, b = pair
        r = Access(name="acc", source=a, target=b, access_mode=mode)
        assert r.access_mode is mode

    def test_is_dependency_relationship(self) -> None:
        assert issubclass(Access, DependencyRelationship)

    def test_category_inherited(self) -> None:
        assert Access.category is RelationshipCategory.DEPENDENCY

    def test_invalid_access_mode_raises(
        self, pair: tuple[_ConcreteElement, _ConcreteElement]
    ) -> None:
        a, b = pair
        with pytest.raises(Exception):  # noqa: B017
            Access(name="acc", source=a, target=b, access_mode="invalid")  # type: ignore[call-arg]
