"""Technology-layer-specific tests.

Generic property checks (layer, aspect, notation, type_name, instantiation)
are covered by test_element_properties.py via the ELEMENT_SPECS registry.
This file retains only behaviour unique to the technology layer:
  - ABC instantiation guards
  - Inheritance / subclass relationships (including Device/SystemSoftware-is-Node)
  - TechnologyCollaboration validator (>= 2 assigned elements)
  - TechnologyInteraction validator (>= 2 assigned elements)
  - TechnologyEvent.time field
  - Artifact passive-structure inheritance
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from etcion.enums import Aspect, Layer
from etcion.metamodel.elements import (
    Event,
    ExternalActiveStructureElement,
    ExternalBehaviorElement,
    InternalActiveStructureElement,
    InternalBehaviorElement,
    PassiveStructureElement,
)
from etcion.metamodel.technology import (
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

INTERNAL_ACTIVE = [
    Node,
    Device,
    SystemSoftware,
    TechnologyCollaboration,
    Path,
    CommunicationNetwork,
]

INTERNAL_BEHAVIOR = [
    TechnologyFunction,
    TechnologyInteraction,
    TechnologyProcess,
]


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


class TestActiveStructureInheritance:
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


class TestBehaviorInheritance:
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


class TestArtifactInheritance:
    def test_is_passive_structure_element(self) -> None:
        assert issubclass(Artifact, PassiveStructureElement)

    def test_isinstance_passive_structure(self) -> None:
        assert isinstance(Artifact(name="x"), PassiveStructureElement)


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
