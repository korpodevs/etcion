"""Merged tests for test_business."""

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


class TestInstantiation_1:
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


class TestTypeNames_1:
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


class TestInheritance_1:
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


class TestClassVars_1:
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


class TestNotation_1:
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


class TestInstantiation_2:
    @pytest.mark.parametrize(
        "cls",
        [BusinessProcess, BusinessFunction, BusinessEvent, BusinessService],
    )
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"


class TestTypeNames_2:
    def test_business_process(self) -> None:
        assert BusinessProcess(name="x")._type_name == "BusinessProcess"

    def test_business_function(self) -> None:
        assert BusinessFunction(name="x")._type_name == "BusinessFunction"

    def test_business_interaction(self) -> None:
        from etcion.metamodel.business import BusinessActor

        a1 = BusinessActor(name="a")
        a2 = BusinessActor(name="b")
        bi = BusinessInteraction(
            name="x",
            assigned_elements=[a1, a2],
        )
        assert bi._type_name == "BusinessInteraction"

    def test_business_event(self) -> None:
        assert BusinessEvent(name="x")._type_name == "BusinessEvent"

    def test_business_service(self) -> None:
        assert BusinessService(name="x")._type_name == "BusinessService"


class TestInheritance_2:
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


class TestClassVars_2:
    @pytest.mark.parametrize(
        "cls",
        [
            BusinessProcess,
            BusinessFunction,
            BusinessInteraction,
            BusinessEvent,
            BusinessService,
        ],
    )
    def test_layer_is_business(self, cls: type) -> None:
        assert cls.layer is Layer.BUSINESS

    @pytest.mark.parametrize(
        "cls",
        [
            BusinessProcess,
            BusinessFunction,
            BusinessInteraction,
            BusinessEvent,
            BusinessService,
        ],
    )
    def test_aspect_is_behavior(self, cls: type) -> None:
        assert cls.aspect is Aspect.BEHAVIOR


class TestNotation_2:
    @pytest.mark.parametrize(
        "cls",
        [
            BusinessProcess,
            BusinessFunction,
            BusinessInteraction,
            BusinessEvent,
            BusinessService,
        ],
    )
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#FFFFB5"

    @pytest.mark.parametrize(
        "cls",
        [
            BusinessProcess,
            BusinessFunction,
            BusinessInteraction,
            BusinessEvent,
            BusinessService,
        ],
    )
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "B"

    @pytest.mark.parametrize(
        "cls",
        [
            BusinessProcess,
            BusinessFunction,
            BusinessInteraction,
            BusinessEvent,
            BusinessService,
        ],
    )
    def test_corner_shape_round(self, cls: type) -> None:
        assert cls.notation.corner_shape == "round"


class TestBusinessInteractionValidator:
    def test_fewer_than_two_assigned_elements_raises(self) -> None:
        with pytest.raises(ValidationError, match="requires >= 2"):
            BusinessInteraction(name="x", assigned_elements=[])

    def test_one_assigned_element_raises(self) -> None:
        from etcion.metamodel.business import BusinessActor

        with pytest.raises(ValidationError, match="requires >= 2"):
            BusinessInteraction(name="x", assigned_elements=[BusinessActor(name="a")])


class TestBusinessEventTime:
    def test_time_defaults_to_none(self) -> None:
        be = BusinessEvent(name="x")
        assert be.time is None

    def test_time_accepts_string(self) -> None:
        be = BusinessEvent(name="x", time="2026-01-01")
        assert be.time == "2026-01-01"


class TestInstantiation_3:
    @pytest.mark.parametrize(
        "cls",
        [BusinessObject, Contract, Representation],
    )
    def test_can_instantiate(self, cls: type) -> None:
        obj = cls(name="test")
        assert obj.name == "test"


class TestTypeNames_3:
    def test_business_object(self) -> None:
        assert BusinessObject(name="x")._type_name == "BusinessObject"

    def test_contract(self) -> None:
        assert Contract(name="x")._type_name == "Contract"

    def test_representation(self) -> None:
        assert Representation(name="x")._type_name == "Representation"


class TestInheritance_3:
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


class TestClassVars_3:
    @pytest.mark.parametrize(
        "cls",
        [BusinessObject, Contract, Representation],
    )
    def test_layer_is_business(self, cls: type) -> None:
        assert cls.layer is Layer.BUSINESS

    @pytest.mark.parametrize(
        "cls",
        [BusinessObject, Contract, Representation],
    )
    def test_aspect_is_passive_structure(self, cls: type) -> None:
        assert cls.aspect is Aspect.PASSIVE_STRUCTURE


class TestNotation_3:
    @pytest.mark.parametrize(
        "cls",
        [BusinessObject, Contract, Representation],
    )
    def test_layer_color(self, cls: type) -> None:
        assert cls.notation.layer_color == "#FFFFB5"

    @pytest.mark.parametrize(
        "cls",
        [BusinessObject, Contract, Representation],
    )
    def test_badge_letter(self, cls: type) -> None:
        assert cls.notation.badge_letter == "B"

    @pytest.mark.parametrize(
        "cls",
        [BusinessObject, Contract, Representation],
    )
    def test_corner_shape_square(self, cls: type) -> None:
        assert cls.notation.corner_shape == "square"

    def test_contract_has_own_notation(self) -> None:
        assert Contract.notation is not BusinessObject.notation


class TestProductInstantiation:
    def test_can_instantiate(self) -> None:
        p = Product(name="Insurance Product")
        assert p.name == "Insurance Product"

    def test_type_name(self) -> None:
        p = Product(name="x")
        assert p._type_name == "Product"


class TestProductInheritance:
    def test_is_composite_element(self) -> None:
        assert isinstance(Product(name="x"), CompositeElement)

    def test_is_not_business_internal_active_structure(self) -> None:
        assert not isinstance(Product(name="x"), BusinessInternalActiveStructureElement)


class TestProductClassVars:
    def test_layer(self) -> None:
        assert Product.layer is Layer.BUSINESS

    def test_aspect(self) -> None:
        assert Product.aspect is Aspect.COMPOSITE


class TestProductNotation:
    def test_corner_shape(self) -> None:
        assert Product.notation.corner_shape == "square"

    def test_layer_color(self) -> None:
        assert Product.notation.layer_color == "#FFFFB5"

    def test_badge_letter(self) -> None:
        assert Product.notation.badge_letter == "B"


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
