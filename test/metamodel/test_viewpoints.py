"""Merged tests for test_viewpoints."""

from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from pyarchi.enums import ContentCategory, PurposeCategory
from pyarchi.exceptions import ValidationError
from pyarchi.metamodel.application import ApplicationComponent, ApplicationService
from pyarchi.metamodel.business import BusinessActor, BusinessProcess
from pyarchi.metamodel.concepts import Concept
from pyarchi.metamodel.model import Model
from pyarchi.metamodel.motivation import Stakeholder
from pyarchi.metamodel.relationships import Serving
from pyarchi.metamodel.viewpoints import Concern, View, Viewpoint


class TestPurposeCategory:
    def test_member_count(self) -> None:
        assert len(PurposeCategory) == 3

    def test_members_exist(self) -> None:
        assert PurposeCategory.DESIGNING.value == "Designing"
        assert PurposeCategory.DECIDING.value == "Deciding"
        assert PurposeCategory.INFORMING.value == "Informing"

    def test_is_enum_not_str(self) -> None:
        assert not isinstance(PurposeCategory.DESIGNING, str)


class TestContentCategory:
    def test_member_count(self) -> None:
        assert len(ContentCategory) == 3

    def test_members_exist(self) -> None:
        assert ContentCategory.DETAILS.value == "Details"
        assert ContentCategory.COHERENCE.value == "Coherence"
        assert ContentCategory.OVERVIEW.value == "Overview"

    def test_is_enum_not_str(self) -> None:
        assert not isinstance(ContentCategory.DETAILS, str)


@pytest.fixture
def basic_viewpoint() -> Viewpoint:
    return Viewpoint(
        name="Test VP",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.DETAILS,
        permitted_concept_types=frozenset({BusinessActor}),
    )


class TestViewpointConstruction:
    def test_minimal_construction(self, basic_viewpoint: Viewpoint) -> None:
        assert basic_viewpoint.name == "Test VP"
        assert basic_viewpoint.purpose == PurposeCategory.DESIGNING
        assert basic_viewpoint.content == ContentCategory.DETAILS
        assert BusinessActor in basic_viewpoint.permitted_concept_types

    def test_optional_fields_default(self, basic_viewpoint: Viewpoint) -> None:
        assert basic_viewpoint.representation_description is None
        assert basic_viewpoint.concerns == []

    def test_with_representation_description(self) -> None:
        vp = Viewpoint(
            name="VP",
            purpose=PurposeCategory.INFORMING,
            content=ContentCategory.OVERVIEW,
            permitted_concept_types=frozenset({BusinessActor}),
            representation_description="Shows actors only",
        )
        assert vp.representation_description == "Shows actors only"

    def test_missing_name_raises(self) -> None:
        with pytest.raises(PydanticValidationError):
            Viewpoint(
                purpose=PurposeCategory.DESIGNING,
                content=ContentCategory.DETAILS,
                permitted_concept_types=frozenset({BusinessActor}),
            )  # type: ignore[call-arg]

    def test_missing_purpose_raises(self) -> None:
        with pytest.raises(PydanticValidationError):
            Viewpoint(
                name="VP",
                content=ContentCategory.DETAILS,
                permitted_concept_types=frozenset({BusinessActor}),
            )  # type: ignore[call-arg]


class TestViewpointImmutability:
    def test_frozen_name(self, basic_viewpoint: Viewpoint) -> None:
        with pytest.raises(PydanticValidationError):
            basic_viewpoint.name = "Changed"  # type: ignore[misc]

    def test_frozen_permitted_types(self, basic_viewpoint: Viewpoint) -> None:
        with pytest.raises(PydanticValidationError):
            basic_viewpoint.permitted_concept_types = frozenset()  # type: ignore[misc]


class TestViewpointIsNotConcept:
    def test_not_a_concept(self, basic_viewpoint: Viewpoint) -> None:
        assert not isinstance(basic_viewpoint, Concept)

    def test_no_id_field(self) -> None:
        assert "id" not in Viewpoint.model_fields


class TestCustomViewpoints:
    def test_user_defined_viewpoint_accepted(self) -> None:
        vp = Viewpoint(
            name="My Custom VP",
            purpose=PurposeCategory.DECIDING,
            content=ContentCategory.COHERENCE,
            permitted_concept_types=frozenset({BusinessActor, BusinessProcess}),
        )
        assert len(vp.permitted_concept_types) == 2


@pytest.fixture
def model_with_actors() -> Model:
    m = Model()
    m.add(BusinessActor(name="Alice"))
    m.add(BusinessActor(name="Bob"))
    return m


@pytest.fixture
def actor_viewpoint() -> Viewpoint:
    return Viewpoint(
        name="Actor VP",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.DETAILS,
        permitted_concept_types=frozenset({BusinessActor}),
    )


@pytest.fixture
def app_viewpoint() -> Viewpoint:
    """Viewpoint permitting ApplicationComponent, ApplicationService, Serving."""
    return Viewpoint(
        name="App Cooperation",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.COHERENCE,
        permitted_concept_types=frozenset({ApplicationComponent, ApplicationService, Serving}),
    )


class TestViewConstruction:
    def test_minimal_construction(
        self, model_with_actors: Model, actor_viewpoint: Viewpoint
    ) -> None:
        view = View(
            governing_viewpoint=actor_viewpoint,
            underlying_model=model_with_actors,
        )
        assert view.concepts == []
        assert view.governing_viewpoint is actor_viewpoint
        assert view.underlying_model is model_with_actors


class TestViewAddTypeGate:
    def test_add_permitted_type(self, model_with_actors: Model, actor_viewpoint: Viewpoint) -> None:
        view = View(
            governing_viewpoint=actor_viewpoint,
            underlying_model=model_with_actors,
        )
        actor = model_with_actors.elements[0]
        view.add(actor)
        assert len(view.concepts) == 1

    def test_add_unpermitted_type_raises(
        self, model_with_actors: Model, actor_viewpoint: Viewpoint
    ) -> None:
        """BusinessProcess not in actor_viewpoint.permitted_concept_types."""
        proc = BusinessProcess(name="Do Work")
        model_with_actors.add(proc)
        view = View(
            governing_viewpoint=actor_viewpoint,
            underlying_model=model_with_actors,
        )
        with pytest.raises(ValidationError):
            view.add(proc)

    def test_subclass_permitted_via_issubclass(self) -> None:
        """If permitted_concept_types contains a base class, subclasses pass the gate."""
        from pyarchi.metamodel.concepts import Element

        actor = BusinessActor(name="A")
        m = Model()
        m.add(actor)
        vp = Viewpoint(
            name="All Elements",
            purpose=PurposeCategory.INFORMING,
            content=ContentCategory.OVERVIEW,
            permitted_concept_types=frozenset({Element}),
        )
        view = View(governing_viewpoint=vp, underlying_model=m)
        view.add(actor)  # BusinessActor is subclass of Element
        assert len(view.concepts) == 1


class TestViewAddMembershipGate:
    def test_concept_not_in_model_raises(self, actor_viewpoint: Viewpoint) -> None:
        m = Model()
        orphan = BusinessActor(name="Orphan")
        view = View(governing_viewpoint=actor_viewpoint, underlying_model=m)
        with pytest.raises(ValidationError):
            view.add(orphan)


class TestViewAddRelationship:
    def test_serving_relationship_accepted(self, app_viewpoint: Viewpoint) -> None:
        comp = ApplicationComponent(name="Backend")
        svc = ApplicationService(name="API")
        rel = Serving(name="serves", source=comp, target=svc)
        m = Model()
        m.add(comp)
        m.add(svc)
        m.add(rel)
        view = View(governing_viewpoint=app_viewpoint, underlying_model=m)
        view.add(rel)
        assert rel in view.concepts


class TestViewIsProjection:
    def test_concepts_are_same_objects(
        self, model_with_actors: Model, actor_viewpoint: Viewpoint
    ) -> None:
        view = View(
            governing_viewpoint=actor_viewpoint,
            underlying_model=model_with_actors,
        )
        actor = model_with_actors.elements[0]
        view.add(actor)
        assert view.concepts[0] is model_with_actors[actor.id]


class TestViewIsNotConcept:
    def test_not_a_concept(self, model_with_actors: Model, actor_viewpoint: Viewpoint) -> None:
        view = View(
            governing_viewpoint=actor_viewpoint,
            underlying_model=model_with_actors,
        )
        assert not isinstance(view, Concept)


class TestViewErrorType:
    def test_raises_pyarchi_validation_error_not_pydantic(self, actor_viewpoint: Viewpoint) -> None:
        """Confirm View.add() raises pyarchi.exceptions.ValidationError."""
        import pydantic

        m = Model()
        orphan = BusinessActor(name="X")
        view = View(governing_viewpoint=actor_viewpoint, underlying_model=m)
        with pytest.raises(ValidationError) as exc_info:
            view.add(orphan)
        assert not isinstance(exc_info.value, pydantic.ValidationError)


@pytest.fixture
def stakeholder() -> Stakeholder:
    return Stakeholder(name="CTO")


@pytest.fixture
def viewpoint() -> Viewpoint:
    return Viewpoint(
        name="Business VP",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.DETAILS,
        permitted_concept_types=frozenset({BusinessActor, BusinessProcess}),
    )


class TestConcernConstruction:
    def test_minimal(self) -> None:
        c = Concern(description="Data privacy compliance")
        assert c.description == "Data privacy compliance"
        assert c.stakeholders == []
        assert c.viewpoints == []

    def test_with_stakeholder_and_viewpoint(
        self, stakeholder: Stakeholder, viewpoint: Viewpoint
    ) -> None:
        c = Concern(
            description="Operational efficiency",
            stakeholders=[stakeholder],
            viewpoints=[viewpoint],
        )
        assert len(c.stakeholders) == 1
        assert len(c.viewpoints) == 1
        assert c.stakeholders[0] is stakeholder
        assert c.viewpoints[0] is viewpoint

    def test_missing_description_raises(self) -> None:
        with pytest.raises(PydanticValidationError):
            Concern()  # type: ignore[call-arg]


class TestConcernIsNotConcept:
    def test_not_a_concept(self) -> None:
        c = Concern(description="test")
        assert not isinstance(c, Concept)


class TestConcernMutability:
    def test_append_stakeholder(self, stakeholder: Stakeholder) -> None:
        c = Concern(description="test")
        c.stakeholders.append(stakeholder)
        assert len(c.stakeholders) == 1

    def test_append_viewpoint(self, viewpoint: Viewpoint) -> None:
        c = Concern(description="test")
        c.viewpoints.append(viewpoint)
        assert len(c.viewpoints) == 1


class TestStakeholderConcernViewpointNavigation:
    def test_end_to_end_chain(self, stakeholder: Stakeholder, viewpoint: Viewpoint) -> None:
        """Stakeholder -> Concern -> Viewpoint -> View navigation."""
        concern = Concern(
            description="System reliability",
            stakeholders=[stakeholder],
            viewpoints=[viewpoint],
        )

        actor = BusinessActor(name="Alice")
        m = Model()
        m.add(actor)
        m.add(stakeholder)

        view = View(
            governing_viewpoint=viewpoint,
            underlying_model=m,
        )
        view.add(actor)

        # Navigate the chain
        found_viewpoints = concern.viewpoints
        assert viewpoint in found_viewpoints

        found_stakeholders = concern.stakeholders
        assert stakeholder in found_stakeholders

        # Verify the view is governed by a viewpoint reachable from the concern
        assert view.governing_viewpoint in found_viewpoints
        assert len(view.concepts) == 1

    def test_reverse_navigation_via_comprehension(
        self, stakeholder: Stakeholder, viewpoint: Viewpoint
    ) -> None:
        """Find all concerns for a given stakeholder by filtering a collection."""
        c1 = Concern(
            description="Privacy",
            stakeholders=[stakeholder],
            viewpoints=[viewpoint],
        )
        c2 = Concern(description="Unrelated")
        all_concerns = [c1, c2]

        stakeholder_concerns = [c for c in all_concerns if stakeholder in c.stakeholders]
        assert stakeholder_concerns == [c1]


class TestViewpointConcernsBidirectional:
    def test_viewpoint_concerns_field(self, viewpoint: Viewpoint) -> None:
        """Viewpoint.concerns populated at construction time."""
        concern = Concern(description="test")
        vp = Viewpoint(
            name="VP with concerns",
            purpose=PurposeCategory.INFORMING,
            content=ContentCategory.OVERVIEW,
            permitted_concept_types=frozenset({BusinessActor}),
            concerns=[concern],
        )
        assert concern in vp.concerns
