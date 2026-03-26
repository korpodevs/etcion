"""Merged tests for test_application."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.application import (
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
from pyarchi.metamodel.elements import (
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


class TestInstantiation_1:
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


class TestTypeNames_1:
    def test_application_component(self) -> None:
        assert ApplicationComponent(name="x")._type_name == "ApplicationComponent"

    def test_application_collaboration(self) -> None:
        c1 = ApplicationComponent(name="a")
        c2 = ApplicationComponent(name="b")
        obj = ApplicationCollaboration(name="x", assigned_elements=[c1, c2])
        assert obj._type_name == "ApplicationCollaboration"

    def test_application_interface(self) -> None:
        assert ApplicationInterface(name="x")._type_name == "ApplicationInterface"


class TestInheritance_1:
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


class TestClassVars_1:
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


class TestNotation_1:
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


class TestInstantiation_2:
    @pytest.mark.parametrize(
        "cls",
        [ApplicationFunction, ApplicationProcess, ApplicationEvent, ApplicationService],
    )
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"

    def test_application_interaction_instantiates(self) -> None:
        c1 = ApplicationComponent(name="a")
        c2 = ApplicationComponent(name="b")
        obj = ApplicationInteraction(name="test", assigned_elements=[c1, c2])
        assert obj.name == "test"


class TestTypeNames_2:
    def test_application_function(self) -> None:
        assert ApplicationFunction(name="x")._type_name == "ApplicationFunction"

    def test_application_interaction(self) -> None:
        c1 = ApplicationComponent(name="a")
        c2 = ApplicationComponent(name="b")
        obj = ApplicationInteraction(name="x", assigned_elements=[c1, c2])
        assert obj._type_name == "ApplicationInteraction"

    def test_application_process(self) -> None:
        assert ApplicationProcess(name="x")._type_name == "ApplicationProcess"

    def test_application_event(self) -> None:
        assert ApplicationEvent(name="x")._type_name == "ApplicationEvent"

    def test_application_service(self) -> None:
        assert ApplicationService(name="x")._type_name == "ApplicationService"


class TestInheritance_2:
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


class TestClassVars_2:
    @pytest.mark.parametrize(
        "cls",
        [
            ApplicationFunction,
            ApplicationInteraction,
            ApplicationProcess,
            ApplicationEvent,
            ApplicationService,
        ],
    )
    def test_layer_is_application(self, cls: type) -> None:
        assert cls.layer is Layer.APPLICATION

    @pytest.mark.parametrize(
        "cls",
        [
            ApplicationFunction,
            ApplicationInteraction,
            ApplicationProcess,
            ApplicationEvent,
            ApplicationService,
        ],
    )
    def test_aspect_is_behavior(self, cls: type) -> None:
        assert cls.aspect is Aspect.BEHAVIOR


class TestNotation_2:
    @pytest.mark.parametrize(
        "cls",
        [
            ApplicationFunction,
            ApplicationInteraction,
            ApplicationProcess,
            ApplicationEvent,
            ApplicationService,
        ],
    )
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#B5FFFF"

    @pytest.mark.parametrize(
        "cls",
        [
            ApplicationFunction,
            ApplicationInteraction,
            ApplicationProcess,
            ApplicationEvent,
            ApplicationService,
        ],
    )
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "A"

    @pytest.mark.parametrize(
        "cls",
        [
            ApplicationFunction,
            ApplicationInteraction,
            ApplicationProcess,
            ApplicationEvent,
            ApplicationService,
        ],
    )
    def test_corner_shape_round(self, cls: type) -> None:
        assert cls.notation.corner_shape == "round"


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


class TestInstantiation_3:
    def test_can_instantiate(self) -> None:
        obj = DataObject(name="test")
        assert obj.name == "test"


class TestTypeName:
    def test_data_object(self) -> None:
        assert DataObject(name="x")._type_name == "DataObject"


class TestInheritance_3:
    def test_is_passive_structure_element(self) -> None:
        assert issubclass(DataObject, PassiveStructureElement)

    def test_isinstance_passive_structure(self) -> None:
        assert isinstance(DataObject(name="x"), PassiveStructureElement)


class TestClassVars_3:
    def test_layer_is_application(self) -> None:
        assert DataObject.layer is Layer.APPLICATION

    def test_aspect_is_passive_structure(self) -> None:
        assert DataObject.aspect is Aspect.PASSIVE_STRUCTURE


class TestNotation_3:
    def test_layer_color(self) -> None:
        assert DataObject.notation.layer_color == "#B5FFFF"

    def test_badge_letter(self) -> None:
        assert DataObject.notation.badge_letter == "A"

    def test_corner_shape_square(self) -> None:
        assert DataObject.notation.corner_shape == "square"
