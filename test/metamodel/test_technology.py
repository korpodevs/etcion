"""Merged tests for test_technology."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import (
    Event,
    ExternalActiveStructureElement,
    ExternalBehaviorElement,
    InternalActiveStructureElement,
    InternalBehaviorElement,
    PassiveStructureElement,
)
from pyarchi.metamodel.technology import (
    Artifact,
    CommunicationNetwork,
    Device,
    Node,
    Path,
    SystemSoftware,
    TechnologyCollaboration,
    TechnologyEvent,
    TechnologyFunction,
    TechnologyInteraction,
    TechnologyInterface,
    TechnologyInternalActiveStructureElement,
    TechnologyInternalBehaviorElement,
    TechnologyProcess,
    TechnologyService,
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


class TestInstantiation_1:
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


class TestTypeNames_1:
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


class TestInheritance_1:
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


class TestClassVars_1:
    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_layer_is_technology(self, cls: type) -> None:
        assert cls.layer is Layer.TECHNOLOGY

    @pytest.mark.parametrize("cls", ALL_ACTIVE)
    def test_aspect_is_active_structure(self, cls: type) -> None:
        assert cls.aspect is Aspect.ACTIVE_STRUCTURE


class TestNotation_1:
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


ALL_BEHAVIOR = [
    TechnologyFunction,
    TechnologyInteraction,
    TechnologyProcess,
    TechnologyEvent,
    TechnologyService,
]

INTERNAL_BEHAVIOR = [
    TechnologyFunction,
    TechnologyInteraction,
    TechnologyProcess,
]


class TestInstantiation_2:
    @pytest.mark.parametrize(
        "cls",
        [TechnologyFunction, TechnologyProcess, TechnologyEvent, TechnologyService],
    )
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"

    def test_technology_interaction_instantiates(self) -> None:
        n1 = Node(name="a")
        n2 = Node(name="b")
        obj = TechnologyInteraction(name="test", assigned_elements=[n1, n2])
        assert obj.name == "test"


class TestTypeNames_2:
    def test_technology_function(self) -> None:
        assert TechnologyFunction(name="x")._type_name == "TechnologyFunction"

    def test_technology_interaction(self) -> None:
        n1 = Node(name="a")
        n2 = Node(name="b")
        obj = TechnologyInteraction(name="x", assigned_elements=[n1, n2])
        assert obj._type_name == "TechnologyInteraction"

    def test_technology_process(self) -> None:
        assert TechnologyProcess(name="x")._type_name == "TechnologyProcess"

    def test_technology_event(self) -> None:
        assert TechnologyEvent(name="x")._type_name == "TechnologyEvent"

    def test_technology_service(self) -> None:
        assert TechnologyService(name="x")._type_name == "TechnologyService"


class TestInheritance_2:
    @pytest.mark.parametrize("cls", INTERNAL_BEHAVIOR)
    def test_internal_types_are_technology_internal_behavior(self, cls: type) -> None:
        assert issubclass(cls, TechnologyInternalBehaviorElement)

    @pytest.mark.parametrize("cls", INTERNAL_BEHAVIOR)
    def test_internal_types_are_internal_behavior_element(self, cls: type) -> None:
        assert issubclass(cls, InternalBehaviorElement)

    def test_technology_event_is_event(self) -> None:
        assert issubclass(TechnologyEvent, Event)

    def test_technology_event_is_not_technology_internal_behavior(self) -> None:
        assert not issubclass(TechnologyEvent, TechnologyInternalBehaviorElement)

    def test_technology_service_is_external_behavior_element(self) -> None:
        assert issubclass(TechnologyService, ExternalBehaviorElement)

    def test_technology_service_is_not_technology_internal_behavior(self) -> None:
        assert not issubclass(TechnologyService, TechnologyInternalBehaviorElement)


class TestClassVars_2:
    @pytest.mark.parametrize("cls", ALL_BEHAVIOR)
    def test_layer_is_technology(self, cls: type) -> None:
        assert cls.layer is Layer.TECHNOLOGY

    @pytest.mark.parametrize("cls", ALL_BEHAVIOR)
    def test_aspect_is_behavior(self, cls: type) -> None:
        assert cls.aspect is Aspect.BEHAVIOR


class TestNotation_2:
    @pytest.mark.parametrize("cls", ALL_BEHAVIOR)
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#C9E7B7"

    @pytest.mark.parametrize("cls", ALL_BEHAVIOR)
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "T"

    @pytest.mark.parametrize("cls", ALL_BEHAVIOR)
    def test_corner_shape_round(self, cls: type) -> None:
        assert cls.notation.corner_shape == "round"


class TestTechnologyInteractionValidator:
    def test_fewer_than_two_assigned_elements_raises(self) -> None:
        with pytest.raises(ValidationError, match="requires >= 2"):
            TechnologyInteraction(name="x", assigned_elements=[])

    def test_one_assigned_element_raises(self) -> None:
        n1 = Node(name="a")
        with pytest.raises(ValidationError, match="requires >= 2"):
            TechnologyInteraction(name="x", assigned_elements=[n1])

    def test_two_assigned_elements_ok(self) -> None:
        n1 = Node(name="a")
        n2 = Node(name="b")
        obj = TechnologyInteraction(name="x", assigned_elements=[n1, n2])
        assert len(obj.assigned_elements) == 2


class TestTechnologyEventTime:
    def test_time_defaults_to_none(self) -> None:
        te = TechnologyEvent(name="x")
        assert te.time is None

    def test_time_accepts_string(self) -> None:
        te = TechnologyEvent(name="x", time="2026-01-01")
        assert te.time == "2026-01-01"


class TestInstantiation_3:
    def test_can_instantiate(self) -> None:
        obj = Artifact(name="test")
        assert obj.name == "test"


class TestTypeName:
    def test_artifact(self) -> None:
        assert Artifact(name="x")._type_name == "Artifact"


class TestInheritance_3:
    def test_is_passive_structure_element(self) -> None:
        assert issubclass(Artifact, PassiveStructureElement)

    def test_isinstance_passive_structure(self) -> None:
        assert isinstance(Artifact(name="x"), PassiveStructureElement)


class TestClassVars_3:
    def test_layer_is_technology(self) -> None:
        assert Artifact.layer is Layer.TECHNOLOGY

    def test_aspect_is_passive_structure(self) -> None:
        assert Artifact.aspect is Aspect.PASSIVE_STRUCTURE


class TestNotation_3:
    def test_layer_color(self) -> None:
        assert Artifact.notation.layer_color == "#C9E7B7"

    def test_badge_letter(self) -> None:
        assert Artifact.notation.badge_letter == "T"

    def test_corner_shape_square(self) -> None:
        assert Artifact.notation.corner_shape == "square"
