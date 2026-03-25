"""Tests for FEAT-07.2 -- Business Active Structure concrete elements."""

from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.business import (
    BusinessActor,
    BusinessCollaboration,
    BusinessInterface,
    BusinessInternalActiveStructureElement,
    BusinessRole,
)
from pyarchi.metamodel.elements import (
    ExternalActiveStructureElement,
    InternalActiveStructureElement,
)


class TestInstantiation:
    @pytest.mark.parametrize(
        "cls",
        [BusinessActor, BusinessRole, BusinessInterface],
    )
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"

    def test_can_instantiate_business_collaboration(self) -> None:
        a1 = BusinessActor(name="a1")
        a2 = BusinessActor(name="a2")
        obj = BusinessCollaboration(name="test", assigned_elements=[a1, a2])
        assert obj.name == "test"


class TestTypeNames:
    def test_business_actor(self) -> None:
        assert BusinessActor(name="x")._type_name == "BusinessActor"

    def test_business_role(self) -> None:
        assert BusinessRole(name="x")._type_name == "BusinessRole"

    def test_business_collaboration(self) -> None:
        a1 = BusinessActor(name="a")
        a2 = BusinessActor(name="b")
        bc = BusinessCollaboration(name="x", assigned_elements=[a1, a2])
        assert bc._type_name == "BusinessCollaboration"

    def test_business_interface(self) -> None:
        assert BusinessInterface(name="x")._type_name == "BusinessInterface"


class TestInheritance:
    @pytest.mark.parametrize(
        "cls",
        [BusinessActor, BusinessRole],
    )
    def test_internal_types_are_business_internal_active(self, cls: type) -> None:
        assert isinstance(cls(name="x"), BusinessInternalActiveStructureElement)

    def test_business_collaboration_is_business_internal_active(self) -> None:
        assert issubclass(BusinessCollaboration, BusinessInternalActiveStructureElement)

    @pytest.mark.parametrize(
        "cls",
        [BusinessActor, BusinessRole],
    )
    def test_internal_types_are_internal_active_structure(self, cls: type) -> None:
        assert isinstance(cls(name="x"), InternalActiveStructureElement)

    def test_business_collaboration_is_internal_active_structure(self) -> None:
        assert issubclass(BusinessCollaboration, InternalActiveStructureElement)

    def test_business_interface_is_external_active_structure(self) -> None:
        assert isinstance(BusinessInterface(name="x"), ExternalActiveStructureElement)

    def test_business_interface_is_not_business_internal_active(self) -> None:
        assert not isinstance(BusinessInterface(name="x"), BusinessInternalActiveStructureElement)

    def test_business_interface_is_not_internal_active_structure(self) -> None:
        assert not isinstance(BusinessInterface(name="x"), InternalActiveStructureElement)


class TestClassVars:
    @pytest.mark.parametrize(
        "cls",
        [BusinessActor, BusinessRole, BusinessCollaboration, BusinessInterface],
    )
    def test_layer_is_business(self, cls: type) -> None:
        assert cls.layer is Layer.BUSINESS

    @pytest.mark.parametrize(
        "cls",
        [BusinessActor, BusinessRole, BusinessCollaboration, BusinessInterface],
    )
    def test_aspect_is_active_structure(self, cls: type) -> None:
        assert cls.aspect is Aspect.ACTIVE_STRUCTURE


class TestNotation:
    @pytest.mark.parametrize(
        "cls",
        [BusinessActor, BusinessRole, BusinessCollaboration, BusinessInterface],
    )
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#FFFFB5"

    @pytest.mark.parametrize(
        "cls",
        [BusinessActor, BusinessRole, BusinessCollaboration, BusinessInterface],
    )
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "B"

    @pytest.mark.parametrize(
        "cls",
        [BusinessActor, BusinessRole, BusinessCollaboration, BusinessInterface],
    )
    def test_corner_shape_square(self, cls: type) -> None:
        assert cls.notation.corner_shape == "square"
