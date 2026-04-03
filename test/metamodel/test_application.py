"""Application-layer-specific tests.

Generic property checks (layer, aspect, notation, type_name, instantiation)
are covered by test_element_properties.py via the ELEMENT_SPECS registry.
This file retains only behaviour unique to the application layer:
  - ABC instantiation guards
  - Inheritance / subclass relationships
  - ApplicationCollaboration validator (>= 2 assigned elements)
  - ApplicationInteraction validator (>= 2 assigned elements)
  - ApplicationEvent.time field
  - DataObject passive-structure inheritance
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from etcion.enums import Aspect, Layer
from etcion.metamodel.application import (
    ApplicationCollaboration,
    ApplicationComponent,
    ApplicationEvent,
    ApplicationFunction,
    ApplicationInteraction,
    ApplicationInterface,
    ApplicationInternalActiveStructureElement,
    ApplicationInternalBehaviorElement,
    ApplicationProcess,
    ApplicationService,
    DataObject,
)
from etcion.metamodel.elements import (
    Event,
    ExternalActiveStructureElement,
    ExternalBehaviorElement,
    InternalActiveStructureElement,
    InternalBehaviorElement,
    PassiveStructureElement,
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


class TestActiveStructureInheritance:
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


class TestBehaviorInheritance:
    @pytest.mark.parametrize(
        "cls",
        [ApplicationFunction, ApplicationInteraction, ApplicationProcess],
    )
    def test_internal_types_are_application_internal_behavior(self, cls: type) -> None:
        assert issubclass(cls, ApplicationInternalBehaviorElement)

    @pytest.mark.parametrize(
        "cls",
        [ApplicationFunction, ApplicationInteraction, ApplicationProcess],
    )
    def test_internal_types_are_internal_behavior_element(self, cls: type) -> None:
        assert issubclass(cls, InternalBehaviorElement)

    def test_application_event_is_event(self) -> None:
        assert issubclass(ApplicationEvent, Event)

    def test_application_event_is_not_application_internal_behavior(self) -> None:
        assert not issubclass(ApplicationEvent, ApplicationInternalBehaviorElement)

    def test_application_service_is_external_behavior_element(self) -> None:
        assert issubclass(ApplicationService, ExternalBehaviorElement)

    def test_application_service_is_not_application_internal_behavior(self) -> None:
        assert not issubclass(ApplicationService, ApplicationInternalBehaviorElement)


class TestDataObjectInheritance:
    def test_is_passive_structure_element(self) -> None:
        assert issubclass(DataObject, PassiveStructureElement)

    def test_isinstance_passive_structure(self) -> None:
        assert isinstance(DataObject(name="x"), PassiveStructureElement)


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


class TestApplicationInteractionValidator:
    def test_fewer_than_two_assigned_elements_raises(self) -> None:
        with pytest.raises(ValidationError, match="requires >= 2"):
            ApplicationInteraction(name="x", assigned_elements=[])

    def test_one_assigned_element_raises(self) -> None:
        c1 = ApplicationComponent(name="a")
        with pytest.raises(ValidationError, match="requires >= 2"):
            ApplicationInteraction(name="x", assigned_elements=[c1])

    def test_two_assigned_elements_ok(self) -> None:
        c1 = ApplicationComponent(name="a")
        c2 = ApplicationComponent(name="b")
        obj = ApplicationInteraction(name="x", assigned_elements=[c1, c2])
        assert len(obj.assigned_elements) == 2


class TestApplicationEventTime:
    def test_time_defaults_to_none(self) -> None:
        ae = ApplicationEvent(name="x")
        assert ae.time is None

    def test_time_accepts_string(self) -> None:
        ae = ApplicationEvent(name="x", time="2026-01-01")
        assert ae.time == "2026-01-01"
