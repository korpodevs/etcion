"""Tests for FEAT-09.2 -- Technology Active Structure concrete elements."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import (
    ExternalActiveStructureElement,
    InternalActiveStructureElement,
)
from pyarchi.metamodel.technology import (
    CommunicationNetwork,
    Device,
    Node,
    Path,
    SystemSoftware,
    TechnologyCollaboration,
    TechnologyInterface,
    TechnologyInternalActiveStructureElement,
)

ALL_ACTIVE = [
    Node,
    Device,
    SystemSoftware,
    TechnologyCollaboration,
    TechnologyInterface,
    Path,
    CommunicationNetwork,
]

INTERNAL_ACTIVE = [
    Node,
    Device,
    SystemSoftware,
    TechnologyCollaboration,
    Path,
    CommunicationNetwork,
]


class TestInstantiation:
    @pytest.mark.parametrize(
        "cls",
        [Node, Device, SystemSoftware, TechnologyInterface, Path, CommunicationNetwork],
    )
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"

    def test_technology_collaboration(self) -> None:
        n1 = Node(name="a")
        n2 = Node(name="b")
        obj = TechnologyCollaboration(name="test", assigned_elements=[n1, n2])
        assert obj.name == "test"


class TestTypeNames:
    @pytest.mark.parametrize(
        ("cls", "expected"),
        [
            (Node, "Node"),
            (Device, "Device"),
            (SystemSoftware, "SystemSoftware"),
            (TechnologyInterface, "TechnologyInterface"),
            (Path, "Path"),
            (CommunicationNetwork, "CommunicationNetwork"),
        ],
    )
    def test_type_name(self, cls: type, expected: str) -> None:
        assert cls(name="x")._type_name == expected

    def test_technology_collaboration_type_name(self) -> None:
        n1 = Node(name="a")
        n2 = Node(name="b")
        obj = TechnologyCollaboration(name="x", assigned_elements=[n1, n2])
        assert obj._type_name == "TechnologyCollaboration"


class TestInheritance:
    @pytest.mark.parametrize("cls", INTERNAL_ACTIVE)
    def test_internal_types_are_technology_internal_active(self, cls: type) -> None:
        assert issubclass(cls, TechnologyInternalActiveStructureElement)

    @pytest.mark.parametrize("cls", INTERNAL_ACTIVE)
    def test_internal_types_are_internal_active_structure(self, cls: type) -> None:
        assert issubclass(cls, InternalActiveStructureElement)

    def test_device_isinstance_node(self) -> None:
        assert isinstance(Device(name="x"), Node)

    def test_system_software_isinstance_node(self) -> None:
        assert isinstance(SystemSoftware(name="x"), Node)

    def test_technology_interface_is_external_active_structure(self) -> None:
        assert isinstance(TechnologyInterface(name="x"), ExternalActiveStructureElement)

    def test_technology_interface_is_not_technology_internal_active(self) -> None:
        assert not isinstance(
            TechnologyInterface(name="x"),
            TechnologyInternalActiveStructureElement,
        )

    def test_technology_interface_is_not_internal_active_structure(self) -> None:
        assert not isinstance(TechnologyInterface(name="x"), InternalActiveStructureElement)


class TestClassVars:
    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_layer_is_technology(self, cls: type) -> None:
        assert cls.layer is Layer.TECHNOLOGY

    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_aspect_is_active_structure(self, cls: type) -> None:
        assert cls.aspect is Aspect.ACTIVE_STRUCTURE


class TestNotation:
    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#C9E7B7"

    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "T"

    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_corner_shape_square(self, cls: type) -> None:
        assert cls.notation.corner_shape == "square"


class TestTechnologyCollaborationValidator:
    def test_zero_assigned_elements_raises(self) -> None:
        with pytest.raises(ValidationError, match="requires >= 2"):
            TechnologyCollaboration(name="x", assigned_elements=[])

    def test_one_assigned_element_raises(self) -> None:
        n1 = Node(name="a")
        with pytest.raises(ValidationError, match="requires >= 2"):
            TechnologyCollaboration(name="x", assigned_elements=[n1])

    def test_two_assigned_elements_ok(self) -> None:
        n1 = Node(name="a")
        n2 = Node(name="b")
        obj = TechnologyCollaboration(name="x", assigned_elements=[n1, n2])
        assert len(obj.assigned_elements) == 2

    def test_default_empty_raises(self) -> None:
        with pytest.raises(ValidationError, match="requires >= 2"):
            TechnologyCollaboration(name="x")
