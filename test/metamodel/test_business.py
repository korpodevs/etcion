"""Business-layer-specific tests.

Generic property checks (layer, aspect, notation, type_name, instantiation)
are covered by test_element_properties.py via the ELEMENT_SPECS registry.
This file retains only behaviour unique to the business layer:
  - ABC instantiation guards
  - Inheritance / subclass relationships
  - BusinessCollaboration validator (>= 2 assigned elements)
  - BusinessInteraction validator (>= 2 assigned elements)
  - BusinessEvent.time field
  - Contract-is-BusinessObject relationship
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from pydantic import ValidationError as PydanticValidationError

from etcion.enums import Aspect, Layer
from etcion.metamodel.business import (
    BusinessActor,
    BusinessCollaboration,
    BusinessEvent,
    BusinessFunction,
    BusinessInteraction,
    BusinessInterface,
    BusinessInternalActiveStructureElement,
    BusinessInternalBehaviorElement,
    BusinessObject,
    BusinessPassiveStructureElement,
    BusinessProcess,
    BusinessRole,
    BusinessService,
    Contract,
    Product,
    Representation,
)
from etcion.metamodel.elements import (
    BehaviorElement,
    CompositeElement,
    Event,
    ExternalActiveStructureElement,
    ExternalBehaviorElement,
    InternalActiveStructureElement,
    InternalBehaviorElement,
    PassiveStructureElement,
)


class TestBusinessABCsCannotInstantiate:
    """Each ABC raises TypeError on direct instantiation."""

    @pytest.mark.parametrize(
        "cls",
        [
            BusinessInternalActiveStructureElement,
            BusinessInternalBehaviorElement,
            BusinessPassiveStructureElement,
        ],
    )
    def test_cannot_instantiate(self, cls: type) -> None:
        with pytest.raises(TypeError):
            cls(name="test")


class TestBusinessInternalActiveStructureElementInheritance:
    def test_is_internal_active_structure_element(self) -> None:
        assert issubclass(BusinessInternalActiveStructureElement, InternalActiveStructureElement)

    def test_layer(self) -> None:
        assert BusinessInternalActiveStructureElement.layer is Layer.BUSINESS

    def test_aspect(self) -> None:
        assert BusinessInternalActiveStructureElement.aspect is Aspect.ACTIVE_STRUCTURE


class TestBusinessInternalBehaviorElementInheritance:
    def test_is_internal_behavior_element(self) -> None:
        assert issubclass(BusinessInternalBehaviorElement, InternalBehaviorElement)

    def test_layer(self) -> None:
        assert BusinessInternalBehaviorElement.layer is Layer.BUSINESS

    def test_aspect(self) -> None:
        assert BusinessInternalBehaviorElement.aspect is Aspect.BEHAVIOR


class TestBusinessPassiveStructureElementInheritance:
    def test_is_passive_structure_element(self) -> None:
        assert issubclass(BusinessPassiveStructureElement, PassiveStructureElement)

    def test_layer(self) -> None:
        assert BusinessPassiveStructureElement.layer is Layer.BUSINESS

    def test_aspect(self) -> None:
        assert BusinessPassiveStructureElement.aspect is Aspect.PASSIVE_STRUCTURE


class TestActiveStructureInheritance:
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


class TestBehaviorInheritance:
    @pytest.mark.parametrize(
        "cls",
        [BusinessProcess, BusinessFunction, BusinessInteraction],
    )
    def test_internal_types_are_business_internal_behavior(self, cls: type) -> None:
        assert issubclass(cls, BusinessInternalBehaviorElement)

    @pytest.mark.parametrize(
        "cls",
        [BusinessProcess, BusinessFunction, BusinessInteraction],
    )
    def test_internal_types_are_internal_behavior_element(self, cls: type) -> None:
        assert issubclass(cls, InternalBehaviorElement)

    def test_business_event_is_event(self) -> None:
        assert issubclass(BusinessEvent, Event)

    def test_business_event_is_not_business_internal_behavior(self) -> None:
        assert not issubclass(BusinessEvent, BusinessInternalBehaviorElement)

    def test_business_service_is_external_behavior_element(self) -> None:
        assert issubclass(BusinessService, ExternalBehaviorElement)

    def test_business_service_is_not_business_internal_behavior(self) -> None:
        assert not issubclass(BusinessService, BusinessInternalBehaviorElement)


class TestPassiveStructureInheritance:
    @pytest.mark.parametrize(
        "cls",
        [BusinessObject, Contract, Representation],
    )
    def test_is_passive_structure_element(self, cls: type) -> None:
        assert issubclass(cls, PassiveStructureElement)

    @pytest.mark.parametrize(
        "cls",
        [BusinessObject, Contract, Representation],
    )
    def test_is_business_passive_structure(self, cls: type) -> None:
        assert issubclass(cls, BusinessPassiveStructureElement)

    def test_contract_is_business_object(self) -> None:
        assert isinstance(Contract(name="x"), BusinessObject)

    def test_contract_issubclass_business_object(self) -> None:
        assert issubclass(Contract, BusinessObject)

    def test_contract_has_own_notation(self) -> None:
        assert Contract.notation is not BusinessObject.notation


class TestProductInheritance:
    def test_is_composite_element(self) -> None:
        assert isinstance(Product(name="x"), CompositeElement)

    def test_is_not_business_internal_active_structure(self) -> None:
        assert not isinstance(Product(name="x"), BusinessInternalActiveStructureElement)


class TestBusinessCollaborationValidator:
    def test_zero_assigned_raises(self) -> None:
        with pytest.raises(PydanticValidationError):
            BusinessCollaboration(name="collab")

    def test_one_assigned_raises(self) -> None:
        a = BusinessActor(name="a")
        with pytest.raises(PydanticValidationError):
            BusinessCollaboration(name="collab", assigned_elements=[a])

    def test_two_assigned_succeeds(self) -> None:
        a1 = BusinessActor(name="a1")
        a2 = BusinessActor(name="a2")
        bc = BusinessCollaboration(name="collab", assigned_elements=[a1, a2])
        assert len(bc.assigned_elements) == 2

    def test_three_assigned_succeeds(self) -> None:
        actors = [BusinessActor(name=f"a{i}") for i in range(3)]
        bc = BusinessCollaboration(name="collab", assigned_elements=actors)
        assert len(bc.assigned_elements) == 3


class TestBusinessInteractionValidator:
    def test_fewer_than_two_assigned_elements_raises(self) -> None:
        with pytest.raises(ValidationError, match="requires >= 2"):
            BusinessInteraction(name="x", assigned_elements=[])

    def test_one_assigned_element_raises(self) -> None:
        with pytest.raises(ValidationError, match="requires >= 2"):
            BusinessInteraction(name="x", assigned_elements=[BusinessActor(name="a")])


class TestBusinessEventTime:
    def test_time_defaults_to_none(self) -> None:
        be = BusinessEvent(name="x")
        assert be.time is None

    def test_time_accepts_string(self) -> None:
        be = BusinessEvent(name="x", time="2026-01-01")
        assert be.time == "2026-01-01"
