"""Merged tests for test_relationships."""

from __future__ import annotations

from typing import ClassVar

import pytest
from pydantic import ValidationError as PydanticValidationError

from pyarchi.enums import (
    AccessMode,
    Aspect,
    AssociationDirection,
    InfluenceSign,
    JunctionType,
    Layer,
    RelationshipCategory,
)
from pyarchi.exceptions import ValidationError
from pyarchi.metamodel.business import (
    BusinessActor,
    BusinessObject,
    BusinessProcess,
    BusinessRole,
)
from pyarchi.metamodel.concepts import Concept, Relationship, RelationshipConnector
from pyarchi.metamodel.elements import ActiveStructureElement, BehaviorElement, Grouping
from pyarchi.metamodel.model import Model
from pyarchi.metamodel.relationships import (
    Access,
    Aggregation,
    Assignment,
    Association,
    Composition,
    DependencyRelationship,
    DynamicRelationship,
    Flow,
    Influence,
    Junction,
    OtherRelationship,
    Realization,
    Serving,
    Specialization,
    StructuralRelationship,
    Triggering,
)
from pyarchi.validation.permissions import is_permitted

# ---------------------------------------------------------------------------
# Test-local concrete element stub
# ---------------------------------------------------------------------------


class _ConcreteElement_1(ActiveStructureElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE

    @property
    def _type_name(self) -> str:
        return "Stub"


# ---------------------------------------------------------------------------
# ABC
# ---------------------------------------------------------------------------


class TestStructuralRelationshipABC:
    def test_cannot_instantiate(self) -> None:
        e = _ConcreteElement_1(name="e")
        with pytest.raises(TypeError):
            StructuralRelationship(name="r", source=e, target=e)  # type: ignore[abstract, call-arg]

    def test_category_is_structural(self) -> None:
        assert StructuralRelationship.category is RelationshipCategory.STRUCTURAL

    def test_is_subclass_of_relationship(self) -> None:
        assert issubclass(StructuralRelationship, Relationship)


# ---------------------------------------------------------------------------
# Concrete types
# ---------------------------------------------------------------------------


class TestConcreteStructuralTypes:
    @pytest.fixture()
    def pair(self) -> tuple[_ConcreteElement_1, _ConcreteElement_1]:
        return _ConcreteElement_1(name="a"), _ConcreteElement_1(name="b")

    @pytest.mark.parametrize(
        ("cls", "expected_name"),
        [
            (Composition, "Composition"),
            (Aggregation, "Aggregation"),
            (Assignment, "Assignment"),
            (Realization, "Realization"),
        ],
    )
    def test_instantiation_and_type_name(
        self,
        pair: tuple[_ConcreteElement_1, _ConcreteElement_1],
        cls: type,
        expected_name: str,
    ) -> None:
        a, b = pair
        r = cls(name="r", source=a, target=b)
        assert r._type_name == expected_name

    @pytest.mark.parametrize("cls", [Composition, Aggregation, Assignment, Realization])
    def test_is_structural_relationship(self, cls: type) -> None:
        assert issubclass(cls, StructuralRelationship)

    @pytest.mark.parametrize("cls", [Composition, Aggregation, Assignment, Realization])
    def test_category_inherited(self, cls: type) -> None:
        assert cls.category is RelationshipCategory.STRUCTURAL

    @pytest.mark.parametrize("cls", [Composition, Aggregation, Assignment, Realization])
    def test_is_concept(self, cls: type) -> None:
        assert issubclass(cls, Concept)


# ---------------------------------------------------------------------------
# is_nested
# ---------------------------------------------------------------------------


class TestIsNested:
    def test_defaults_to_false(self) -> None:
        a, b = _ConcreteElement_1(name="a"), _ConcreteElement_1(name="b")
        c = Composition(name="c", source=a, target=b)
        assert c.is_nested is False

    def test_set_to_true(self) -> None:
        a, b = _ConcreteElement_1(name="a"), _ConcreteElement_1(name="b")
        c = Composition(name="c", source=a, target=b, is_nested=True)
        assert c.is_nested is True


# ---------------------------------------------------------------------------
# Test-local concrete element stub
# ---------------------------------------------------------------------------


class _ConcreteElement_2(ActiveStructureElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE

    @property
    def _type_name(self) -> str:
        return "Stub"


# ---------------------------------------------------------------------------
# ABC
# ---------------------------------------------------------------------------


class TestDependencyRelationshipABC:
    def test_cannot_instantiate(self) -> None:
        e = _ConcreteElement_2(name="e")
        with pytest.raises(TypeError):
            DependencyRelationship(name="r", source=e, target=e)

    def test_category_is_dependency(self) -> None:
        assert DependencyRelationship.category is RelationshipCategory.DEPENDENCY

    def test_is_subclass_of_relationship(self) -> None:
        assert issubclass(DependencyRelationship, Relationship)

    def test_is_not_structural(self) -> None:
        assert not issubclass(DependencyRelationship, StructuralRelationship)


# ---------------------------------------------------------------------------
# Serving
# ---------------------------------------------------------------------------


class TestServing:
    @pytest.fixture()
    def pair(self) -> tuple[_ConcreteElement_2, _ConcreteElement_2]:
        return _ConcreteElement_2(name="a"), _ConcreteElement_2(name="b")

    def test_instantiation(self, pair: tuple[_ConcreteElement_2, _ConcreteElement_2]) -> None:
        a, b = pair
        r = Serving(name="s", source=a, target=b)
        assert r._type_name == "Serving"

    def test_category_inherited(self) -> None:
        assert Serving.category is RelationshipCategory.DEPENDENCY

    def test_is_dependency_relationship(self) -> None:
        assert issubclass(Serving, DependencyRelationship)

    def test_is_concept(self) -> None:
        assert issubclass(Serving, Concept)

    def test_is_derived_defaults_false(
        self, pair: tuple[_ConcreteElement_2, _ConcreteElement_2]
    ) -> None:
        a, b = pair
        r = Serving(name="s", source=a, target=b)
        assert r.is_derived is False

    def test_rejects_is_nested(self, pair: tuple[_ConcreteElement_2, _ConcreteElement_2]) -> None:
        a, b = pair
        with pytest.raises(PydanticValidationError):
            Serving(name="s", source=a, target=b, is_nested=True)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Test-local concrete element stub
# ---------------------------------------------------------------------------


class _ConcreteElement_3(ActiveStructureElement):
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
    def pair(self) -> tuple[_ConcreteElement_3, _ConcreteElement_3]:
        return _ConcreteElement_3(name="a"), _ConcreteElement_3(name="b")

    def test_instantiation(self, pair: tuple[_ConcreteElement_3, _ConcreteElement_3]) -> None:
        a, b = pair
        r = Access(name="acc", source=a, target=b)
        assert r._type_name == "Access"

    def test_access_mode_defaults_to_unspecified(
        self, pair: tuple[_ConcreteElement_3, _ConcreteElement_3]
    ) -> None:
        a, b = pair
        r = Access(name="acc", source=a, target=b)
        assert r.access_mode is AccessMode.UNSPECIFIED

    @pytest.mark.parametrize("mode", list(AccessMode))
    def test_accepts_all_access_modes(
        self,
        pair: tuple[_ConcreteElement_3, _ConcreteElement_3],
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
        self, pair: tuple[_ConcreteElement_3, _ConcreteElement_3]
    ) -> None:
        a, b = pair
        with pytest.raises(Exception):  # noqa: B017
            Access(name="acc", source=a, target=b, access_mode="invalid")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Test-local concrete element stub
# ---------------------------------------------------------------------------


class _ConcreteElement_4(ActiveStructureElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE

    @property
    def _type_name(self) -> str:
        return "Stub"


# ---------------------------------------------------------------------------
# InfluenceSign enum ratification
# ---------------------------------------------------------------------------


class TestInfluenceSignEnum:
    def test_strong_positive(self) -> None:
        assert InfluenceSign.STRONG_POSITIVE.value == "++"

    def test_positive(self) -> None:
        assert InfluenceSign.POSITIVE.value == "+"

    def test_neutral(self) -> None:
        assert InfluenceSign.NEUTRAL.value == "0"

    def test_negative(self) -> None:
        assert InfluenceSign.NEGATIVE.value == "-"

    def test_strong_negative(self) -> None:
        assert InfluenceSign.STRONG_NEGATIVE.value == "--"

    def test_exactly_five_members(self) -> None:
        assert len(InfluenceSign) == 5


# ---------------------------------------------------------------------------
# Influence relationship
# ---------------------------------------------------------------------------


class TestInfluence:
    @pytest.fixture()
    def pair(self) -> tuple[_ConcreteElement_4, _ConcreteElement_4]:
        return _ConcreteElement_4(name="a"), _ConcreteElement_4(name="b")

    def test_instantiation(self, pair: tuple[_ConcreteElement_4, _ConcreteElement_4]) -> None:
        a, b = pair
        r = Influence(name="inf", source=a, target=b)
        assert r._type_name == "Influence"

    def test_sign_defaults_to_none(
        self, pair: tuple[_ConcreteElement_4, _ConcreteElement_4]
    ) -> None:
        a, b = pair
        r = Influence(name="inf", source=a, target=b)
        assert r.sign is None

    def test_strength_defaults_to_none(
        self, pair: tuple[_ConcreteElement_4, _ConcreteElement_4]
    ) -> None:
        a, b = pair
        r = Influence(name="inf", source=a, target=b)
        assert r.strength is None

    @pytest.mark.parametrize("sign", list(InfluenceSign))
    def test_accepts_all_signs(
        self,
        pair: tuple[_ConcreteElement_4, _ConcreteElement_4],
        sign: InfluenceSign,
    ) -> None:
        a, b = pair
        r = Influence(name="inf", source=a, target=b, sign=sign)
        assert r.sign is sign

    def test_accepts_strength_string(
        self, pair: tuple[_ConcreteElement_4, _ConcreteElement_4]
    ) -> None:
        a, b = pair
        r = Influence(name="inf", source=a, target=b, strength="high")
        assert r.strength == "high"

    def test_is_dependency_relationship(self) -> None:
        assert issubclass(Influence, DependencyRelationship)

    def test_category_inherited(self) -> None:
        assert Influence.category is RelationshipCategory.DEPENDENCY


# ---------------------------------------------------------------------------
# Test-local concrete element stubs
# ---------------------------------------------------------------------------


class _ConcreteActive_1(ActiveStructureElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE

    @property
    def _type_name(self) -> str:
        return "StubActive"


class _ConcreteBehavior_1(BehaviorElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR

    @property
    def _type_name(self) -> str:
        return "StubBehavior"


# ---------------------------------------------------------------------------
# AssociationDirection enum ratification
# ---------------------------------------------------------------------------


class TestAssociationDirectionEnum:
    def test_undirected(self) -> None:
        assert AssociationDirection.UNDIRECTED.value == "Undirected"

    def test_directed(self) -> None:
        assert AssociationDirection.DIRECTED.value == "Directed"

    def test_exactly_two_members(self) -> None:
        assert len(AssociationDirection) == 2


# ---------------------------------------------------------------------------
# Association relationship
# ---------------------------------------------------------------------------


class TestAssociation:
    @pytest.fixture()
    def pair(self) -> tuple[_ConcreteActive_1, _ConcreteActive_1]:
        return _ConcreteActive_1(name="a"), _ConcreteActive_1(name="b")

    def test_instantiation(self, pair: tuple[_ConcreteActive_1, _ConcreteActive_1]) -> None:
        a, b = pair
        r = Association(name="assoc", source=a, target=b)
        assert r._type_name == "Association"

    def test_direction_defaults_to_undirected(
        self, pair: tuple[_ConcreteActive_1, _ConcreteActive_1]
    ) -> None:
        a, b = pair
        r = Association(name="assoc", source=a, target=b)
        assert r.direction is AssociationDirection.UNDIRECTED

    def test_directed_association(self, pair: tuple[_ConcreteActive_1, _ConcreteActive_1]) -> None:
        a, b = pair
        r = Association(name="assoc", source=a, target=b, direction=AssociationDirection.DIRECTED)
        assert r.direction is AssociationDirection.DIRECTED

    def test_is_dependency_relationship(self) -> None:
        assert issubclass(Association, DependencyRelationship)

    def test_category_inherited(self) -> None:
        assert Association.category is RelationshipCategory.DEPENDENCY

    def test_accepts_cross_type_source_target(self) -> None:
        """Association is universally permitted -- construction accepts any concepts."""
        a = _ConcreteActive_1(name="a")
        b = _ConcreteBehavior_1(name="b")
        r = Association(name="assoc", source=a, target=b)
        assert r.source is a
        assert r.target is b

    def test_accepts_relationship_as_target(self) -> None:
        """Association can target a Relationship (per spec, any two concepts)."""

        class _StubRel(Relationship):
            category: ClassVar[RelationshipCategory] = RelationshipCategory.OTHER

            @property
            def _type_name(self) -> str:
                return "StubRel"

        a = _ConcreteActive_1(name="a")
        b = _ConcreteActive_1(name="b")
        rel = _StubRel(name="r", source=a, target=b)
        assoc = Association(name="assoc", source=a, target=rel)
        assert assoc.target is rel


# ---------------------------------------------------------------------------
# Test-local concrete element stub
# ---------------------------------------------------------------------------


class _ConcreteElement_5(ActiveStructureElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE

    @property
    def _type_name(self) -> str:
        return "Stub"


# ---------------------------------------------------------------------------
# ABC
# ---------------------------------------------------------------------------


class TestDynamicRelationshipABC:
    def test_cannot_instantiate(self) -> None:
        e = _ConcreteElement_5(name="e")
        with pytest.raises(TypeError):
            DynamicRelationship(name="r", source=e, target=e)

    def test_category_is_dynamic(self) -> None:
        assert DynamicRelationship.category is RelationshipCategory.DYNAMIC

    def test_is_subclass_of_relationship(self) -> None:
        assert issubclass(DynamicRelationship, Relationship)

    def test_is_not_structural(self) -> None:
        assert not issubclass(DynamicRelationship, StructuralRelationship)


# ---------------------------------------------------------------------------
# Triggering
# ---------------------------------------------------------------------------


class TestTriggering:
    @pytest.fixture()
    def pair(self) -> tuple[_ConcreteElement_5, _ConcreteElement_5]:
        return _ConcreteElement_5(name="a"), _ConcreteElement_5(name="b")

    def test_instantiation(self, pair: tuple[_ConcreteElement_5, _ConcreteElement_5]) -> None:
        a, b = pair
        r = Triggering(name="t", source=a, target=b)
        assert r._type_name == "Triggering"

    def test_category_inherited(self) -> None:
        assert Triggering.category is RelationshipCategory.DYNAMIC

    def test_is_concept(self) -> None:
        assert issubclass(Triggering, Concept)


# ---------------------------------------------------------------------------
# Flow
# ---------------------------------------------------------------------------


class TestFlow:
    @pytest.fixture()
    def pair(self) -> tuple[_ConcreteElement_5, _ConcreteElement_5]:
        return _ConcreteElement_5(name="a"), _ConcreteElement_5(name="b")

    def test_instantiation(self, pair: tuple[_ConcreteElement_5, _ConcreteElement_5]) -> None:
        a, b = pair
        r = Flow(name="f", source=a, target=b)
        assert r._type_name == "Flow"

    def test_flow_type_defaults_to_none(
        self, pair: tuple[_ConcreteElement_5, _ConcreteElement_5]
    ) -> None:
        a, b = pair
        r = Flow(name="f", source=a, target=b)
        assert r.flow_type is None

    def test_flow_type_accepts_string(
        self, pair: tuple[_ConcreteElement_5, _ConcreteElement_5]
    ) -> None:
        a, b = pair
        r = Flow(name="f", source=a, target=b, flow_type="data")
        assert r.flow_type == "data"

    def test_category_inherited(self) -> None:
        assert Flow.category is RelationshipCategory.DYNAMIC


# ---------------------------------------------------------------------------
# is_nested rejection (STORY-05.7.4, 05.7.7)
# ---------------------------------------------------------------------------


class TestIsNestedRejection:
    def test_triggering_rejects_is_nested(self) -> None:
        a, b = _ConcreteElement_5(name="a"), _ConcreteElement_5(name="b")
        with pytest.raises(Exception):  # noqa: B017
            Triggering(name="t", source=a, target=b, is_nested=True)  # type: ignore[call-arg]

    def test_flow_rejects_is_nested(self) -> None:
        a, b = _ConcreteElement_5(name="a"), _ConcreteElement_5(name="b")
        with pytest.raises(Exception):  # noqa: B017
            Flow(name="f", source=a, target=b, is_nested=True)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Test-local concrete element stubs
# ---------------------------------------------------------------------------


class _ConcreteActive_2(ActiveStructureElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE

    @property
    def _type_name(self) -> str:
        return "StubActive"


class _ConcreteBehavior_2(BehaviorElement):
    layer: ClassVar[Layer] = Layer.BUSINESS
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR

    @property
    def _type_name(self) -> str:
        return "StubBehavior"


# ---------------------------------------------------------------------------
# ABC
# ---------------------------------------------------------------------------


class TestOtherRelationshipABC:
    def test_cannot_instantiate(self) -> None:
        e = _ConcreteActive_2(name="e")
        with pytest.raises(TypeError):
            OtherRelationship(name="r", source=e, target=e)

    def test_category_is_other(self) -> None:
        assert OtherRelationship.category is RelationshipCategory.OTHER

    def test_is_subclass_of_relationship(self) -> None:
        assert issubclass(OtherRelationship, Relationship)

    def test_is_not_structural(self) -> None:
        assert not issubclass(OtherRelationship, StructuralRelationship)

    def test_is_not_dependency(self) -> None:
        assert not issubclass(OtherRelationship, DependencyRelationship)


# ---------------------------------------------------------------------------
# Specialization
# ---------------------------------------------------------------------------


class TestSpecialization:
    @pytest.fixture()
    def pair(self) -> tuple[_ConcreteActive_2, _ConcreteActive_2]:
        return _ConcreteActive_2(name="a"), _ConcreteActive_2(name="b")

    def test_instantiation(self, pair: tuple[_ConcreteActive_2, _ConcreteActive_2]) -> None:
        a, b = pair
        r = Specialization(name="spec", source=a, target=b)
        assert r._type_name == "Specialization"

    def test_category_inherited(self) -> None:
        assert Specialization.category is RelationshipCategory.OTHER

    def test_is_other_relationship(self) -> None:
        assert issubclass(Specialization, OtherRelationship)

    def test_is_concept(self) -> None:
        assert issubclass(Specialization, Concept)

    def test_same_type_construction_succeeds(self) -> None:
        a = _ConcreteActive_2(name="a")
        b = _ConcreteActive_2(name="b")
        r = Specialization(name="spec", source=a, target=b)
        assert r.source is a
        assert r.target is b


# ---------------------------------------------------------------------------
# JunctionType enum ratification
# ---------------------------------------------------------------------------


class TestJunctionTypeEnum:
    def test_and(self) -> None:
        assert JunctionType.AND.value == "And"

    def test_or(self) -> None:
        assert JunctionType.OR.value == "Or"

    def test_exactly_two_members(self) -> None:
        assert len(JunctionType) == 2


# ---------------------------------------------------------------------------
# Junction instantiation
# ---------------------------------------------------------------------------


class TestJunctionInstantiation:
    def test_and_junction(self) -> None:
        j = Junction(junction_type=JunctionType.AND)
        assert j.junction_type is JunctionType.AND

    def test_or_junction(self) -> None:
        j = Junction(junction_type=JunctionType.OR)
        assert j.junction_type is JunctionType.OR

    def test_type_name(self) -> None:
        j = Junction(junction_type=JunctionType.AND)
        assert j._type_name == "Junction"

    def test_has_id(self) -> None:
        j = Junction(junction_type=JunctionType.AND)
        assert isinstance(j.id, str)
        assert len(j.id) > 0

    def test_missing_junction_type_raises(self) -> None:
        with pytest.raises(Exception):  # noqa: B017
            Junction()  # type: ignore[call-arg]

    def test_no_name_attribute(self) -> None:
        j = Junction(junction_type=JunctionType.AND)
        assert not hasattr(j, "name")


# ---------------------------------------------------------------------------
# Inheritance
# ---------------------------------------------------------------------------


class TestJunctionInheritance:
    def test_is_relationship_connector(self) -> None:
        j = Junction(junction_type=JunctionType.AND)
        assert isinstance(j, RelationshipConnector)

    def test_is_concept(self) -> None:
        j = Junction(junction_type=JunctionType.AND)
        assert isinstance(j, Concept)

    def test_is_not_relationship(self) -> None:
        j = Junction(junction_type=JunctionType.AND)
        assert not isinstance(j, Relationship)  # type: ignore[unreachable]


# ---------------------------------------------------------------------------
# Validation xfails (model-level, deferred per ADR-017 ss5/ss6)
# ---------------------------------------------------------------------------


class TestDeferredValidation:
    def test_mixed_relationship_types_raises(self) -> None:
        from pyarchi.enums import JunctionType
        from pyarchi.exceptions import ValidationError
        from pyarchi.metamodel.business import BusinessActor, BusinessProcess
        from pyarchi.metamodel.model import Model
        from pyarchi.metamodel.relationships import Assignment, Junction, Serving

        j = Junction(junction_type=JunctionType.AND)
        a1 = BusinessActor(name="a1")
        bp = BusinessProcess(name="bp")
        r1 = Assignment(name="r1", source=a1, target=j)
        r2 = Serving(name="r2", source=j, target=bp)
        model = Model(concepts=[j, a1, bp, r1, r2])
        errors = model.validate()
        assert any(isinstance(e, ValidationError) for e in errors)

    def test_endpoint_permission_violation_raises(self) -> None:
        from pyarchi.enums import JunctionType
        from pyarchi.exceptions import ValidationError
        from pyarchi.metamodel.business import BusinessActor, BusinessProcess
        from pyarchi.metamodel.model import Model
        from pyarchi.metamodel.relationships import Composition, Junction

        j = Junction(junction_type=JunctionType.AND)
        a1 = BusinessActor(name="a1")
        bp = BusinessProcess(name="bp")
        r1 = Composition(name="r1", source=a1, target=j)
        r2 = Composition(name="r2", source=j, target=bp)
        model = Model(concepts=[j, a1, bp, r1, r2])
        errors = model.validate()
        assert any(isinstance(e, ValidationError) for e in errors)


class TestDirectionInIsPermitted:
    """is_permitted() returns False for wrong-direction triples."""

    def test_assignment_passive_source_rejected(self) -> None:
        assert is_permitted(Assignment, BusinessObject, BusinessProcess) is False

    def test_access_passive_source_rejected(self) -> None:
        assert is_permitted(Access, BusinessObject, BusinessProcess) is False

    def test_serving_passive_source_rejected(self) -> None:
        assert is_permitted(Serving, BusinessObject, BusinessProcess) is False


class TestDirectionModelValidate:
    """Model.validate() surfaces direction errors (depends on FEAT-15.7)."""

    def test_assignment_wrong_direction_model_error(self) -> None:
        from pyarchi.exceptions import ValidationError
        from pyarchi.metamodel.model import Model

        bo = BusinessObject(name="obj")
        bp = BusinessProcess(name="proc")
        rel = Assignment(name="bad", source=bo, target=bp)
        model = Model(concepts=[bo, bp, rel])
        errors = model.validate()
        assert len(errors) >= 1
        assert isinstance(errors[0], ValidationError)

    def test_serving_wrong_direction_model_error(self) -> None:
        from pyarchi.metamodel.model import Model

        bo = BusinessObject(name="obj")
        bp = BusinessProcess(name="proc")
        rel = Serving(name="bad", source=bo, target=bp)
        model = Model(concepts=[bo, bp, rel])
        errors = model.validate()
        assert len(errors) >= 1

    def test_access_wrong_direction_model_error(self) -> None:
        from pyarchi.metamodel.model import Model

        bo = BusinessObject(name="obj")
        bp = BusinessProcess(name="proc")
        rel = Access(name="bad", source=bo, target=bp)
        model = Model(concepts=[bo, bp, rel])
        errors = model.validate()
        assert len(errors) >= 1


class TestCompositeSourcePermission:
    """is_permitted() enforces composite-source when target is Relationship."""

    def test_aggregation_non_composite_source_rel_target_rejected(self) -> None:
        assert is_permitted(Aggregation, BusinessActor, Assignment) is False

    def test_aggregation_composite_source_rel_target_permitted(self) -> None:
        assert is_permitted(Aggregation, Grouping, Assignment) is True

    def test_composition_non_composite_source_rel_target_rejected(self) -> None:
        assert is_permitted(Composition, BusinessActor, Assignment) is False

    def test_composition_composite_source_rel_target_permitted(self) -> None:
        assert is_permitted(Composition, Grouping, Assignment) is True

    def test_same_type_still_works(self) -> None:
        """Existing same-type rule is not broken."""
        assert is_permitted(Aggregation, BusinessActor, BusinessActor) is True


class TestCompositeSourceModelValidate:
    """Model.validate() surfaces the violation (depends on FEAT-15.7)."""

    def test_aggregation_non_composite_source_model_error(self) -> None:
        from pyarchi.exceptions import ValidationError
        from pyarchi.metamodel.model import Model

        a = BusinessActor(name="a")
        bp = BusinessProcess(name="bp")
        inner_rel = Assignment(name="inner", source=a, target=bp)
        outer_rel = Aggregation(name="outer", source=a, target=inner_rel)
        model = Model(concepts=[a, bp, inner_rel, outer_rel])
        errors = model.validate()
        assert len(errors) >= 1
        assert isinstance(errors[0], ValidationError)


class TestSpecializationPermission:
    def test_same_type_permitted(self) -> None:
        assert is_permitted(Specialization, BusinessActor, BusinessActor) is True

    def test_cross_type_rejected(self) -> None:
        assert is_permitted(Specialization, BusinessActor, BusinessProcess) is False


class TestSpecializationModelValidate:
    """Model.validate() catches cross-type Specialization (depends on FEAT-15.7)."""

    def test_cross_type_specialization_model_error(self) -> None:
        from pyarchi.exceptions import ValidationError
        from pyarchi.metamodel.model import Model

        ba = BusinessActor(name="actor")
        bp = BusinessProcess(name="proc")
        rel = Specialization(name="bad", source=ba, target=bp)
        model = Model(concepts=[ba, bp, rel])
        errors = model.validate()
        assert len(errors) >= 1
        assert isinstance(errors[0], ValidationError)

    def test_same_type_specialization_no_error(self) -> None:
        from pyarchi.metamodel.model import Model

        a1 = BusinessActor(name="a1")
        a2 = BusinessActor(name="a2")
        rel = Specialization(name="ok", source=a1, target=a2)
        model = Model(concepts=[a1, a2, rel])
        errors = model.validate()
        assert len(errors) == 0


class TestJunctionHomogeneity:
    def test_mixed_types_produces_error(self) -> None:
        j = Junction(junction_type=JunctionType.AND)
        a1 = BusinessActor(name="a1")
        bp = BusinessProcess(name="bp")
        r1 = Assignment(name="r1", source=a1, target=j)
        r2 = Serving(name="r2", source=j, target=bp)
        model = Model(concepts=[j, a1, bp, r1, r2])
        errors = model.validate()
        junction_errors = [e for e in errors if "Junction" in str(e)]
        assert len(junction_errors) >= 1

    def test_homogeneous_types_no_junction_error(self) -> None:
        j = Junction(junction_type=JunctionType.OR)
        a1 = BusinessActor(name="a1")
        a2 = BusinessActor(name="a2")
        a3 = BusinessActor(name="a3")
        r1 = Specialization(name="r1", source=a1, target=j)
        r2 = Specialization(name="r2", source=a2, target=j)
        r3 = Specialization(name="r3", source=j, target=a3)
        model = Model(concepts=[j, a1, a2, a3, r1, r2, r3])
        errors = model.validate()
        junction_errors = [e for e in errors if "Junction" in str(e)]
        assert len(junction_errors) == 0


class TestJunctionEndpointPermissions:
    def test_endpoint_violation_produces_error(self) -> None:
        """Non-junction endpoints must be permitted for the relationship type."""
        j = Junction(junction_type=JunctionType.AND)
        a1 = BusinessActor(name="a1")
        bp = BusinessProcess(name="bp")
        # Composition between BusinessActor and BusinessProcess is not same-type
        r1 = Composition(name="r1", source=a1, target=j)
        r2 = Composition(name="r2", source=j, target=bp)
        model = Model(concepts=[j, a1, bp, r1, r2])
        errors = model.validate()
        assert len(errors) >= 1


class TestPassiveBehaviorPermission:
    def test_passive_to_behavior_assignment_rejected(self) -> None:
        assert is_permitted(Assignment, BusinessObject, BusinessProcess) is False

    def test_passive_to_passive_assignment_not_affected(self) -> None:
        """This rule only covers passive->behavior, not passive->passive."""
        # passive->passive is handled by other rules; just document the boundary
        is_permitted(Assignment, BusinessObject, BusinessObject)


class TestPassiveBehaviorModelValidate:
    """Model.validate() surfaces the violation (depends on FEAT-15.7)."""

    def test_passive_assigned_to_behavior_model_error(self) -> None:
        from pyarchi.exceptions import ValidationError
        from pyarchi.metamodel.model import Model

        bo = BusinessObject(name="obj")
        bp = BusinessProcess(name="proc")
        rel = Assignment(name="bad", source=bo, target=bp)
        model = Model(concepts=[bo, bp, rel])
        errors = model.validate()
        assert len(errors) >= 1
        assert isinstance(errors[0], ValidationError)

    def test_construction_succeeds_silently(self) -> None:
        """Construction-time does NOT raise -- model-time only."""
        bo = BusinessObject(name="obj")
        bp = BusinessProcess(name="proc")
        rel = Assignment(name="bad", source=bo, target=bp)  # no error here
        assert rel.source is bo
