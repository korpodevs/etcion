"""Tests for FEAT-08.2 -- Application Active Structure concrete elements."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.application import (
    ApplicationCollaboration,
    ApplicationComponent,
    ApplicationInterface,
    ApplicationInternalActiveStructureElement,
)
from pyarchi.metamodel.elements import (
    ExternalActiveStructureElement,
    InternalActiveStructureElement,
)


class TestInstantiation:
    def test_application_component(self) -> None:
        obj = ApplicationComponent(name="test")
        assert obj.name == "test"

    def test_application_collaboration(self) -> None:
        c1 = ApplicationComponent(name="a")
        c2 = ApplicationComponent(name="b")
        obj = ApplicationCollaboration(name="test", assigned_elements=[c1, c2])
        assert obj.name == "test"

    def test_application_interface(self) -> None:
        obj = ApplicationInterface(name="test")
        assert obj.name == "test"


class TestTypeNames:
    def test_application_component(self) -> None:
        assert ApplicationComponent(name="x")._type_name == "ApplicationComponent"

    def test_application_collaboration(self) -> None:
        c1 = ApplicationComponent(name="a")
        c2 = ApplicationComponent(name="b")
        obj = ApplicationCollaboration(name="x", assigned_elements=[c1, c2])
        assert obj._type_name == "ApplicationCollaboration"

    def test_application_interface(self) -> None:
        assert ApplicationInterface(name="x")._type_name == "ApplicationInterface"


class TestInheritance:
    @pytest.mark.parametrize(
        "cls",
        [ApplicationComponent, ApplicationCollaboration],
    )
    def test_internal_types_are_application_internal_active(self, cls: type) -> None:
        assert issubclass(cls, ApplicationInternalActiveStructureElement)

    @pytest.mark.parametrize(
        "cls",
        [ApplicationComponent, ApplicationCollaboration],
    )
    def test_internal_types_are_internal_active_structure(self, cls: type) -> None:
        assert issubclass(cls, InternalActiveStructureElement)

    def test_application_interface_is_external_active_structure(self) -> None:
        assert isinstance(ApplicationInterface(name="x"), ExternalActiveStructureElement)

    def test_application_interface_is_not_application_internal_active(self) -> None:
        assert not isinstance(
            ApplicationInterface(name="x"),
            ApplicationInternalActiveStructureElement,
        )

    def test_application_interface_is_not_internal_active_structure(self) -> None:
        assert not isinstance(ApplicationInterface(name="x"), InternalActiveStructureElement)


class TestClassVars:
    @pytest.mark.parametrize(
        "cls",
        [ApplicationComponent, ApplicationCollaboration, ApplicationInterface],
    )
    def test_layer_is_application(self, cls: type) -> None:
        assert cls.layer is Layer.APPLICATION

    @pytest.mark.parametrize(
        "cls",
        [ApplicationComponent, ApplicationCollaboration, ApplicationInterface],
    )
    def test_aspect_is_active_structure(self, cls: type) -> None:
        assert cls.aspect is Aspect.ACTIVE_STRUCTURE


class TestNotation:
    @pytest.mark.parametrize(
        "cls",
        [ApplicationComponent, ApplicationCollaboration, ApplicationInterface],
    )
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#B5FFFF"

    @pytest.mark.parametrize(
        "cls",
        [ApplicationComponent, ApplicationCollaboration, ApplicationInterface],
    )
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "A"

    @pytest.mark.parametrize(
        "cls",
        [ApplicationComponent, ApplicationCollaboration, ApplicationInterface],
    )
    def test_corner_shape_square(self, cls: type) -> None:
        assert cls.notation.corner_shape == "square"


class TestApplicationCollaborationValidator:
    def test_zero_assigned_elements_raises(self) -> None:
        with pytest.raises(ValidationError, match="requires >= 2"):
            ApplicationCollaboration(name="x", assigned_elements=[])

    def test_one_assigned_element_raises(self) -> None:
        c1 = ApplicationComponent(name="a")
        with pytest.raises(ValidationError, match="requires >= 2"):
            ApplicationCollaboration(name="x", assigned_elements=[c1])

    def test_two_assigned_elements_ok(self) -> None:
        c1 = ApplicationComponent(name="a")
        c2 = ApplicationComponent(name="b")
        obj = ApplicationCollaboration(name="x", assigned_elements=[c1, c2])
        assert len(obj.assigned_elements) == 2

    def test_default_empty_raises(self) -> None:
        with pytest.raises(ValidationError, match="requires >= 2"):
            ApplicationCollaboration(name="x")
