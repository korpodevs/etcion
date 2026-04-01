"""Merged tests for test_viewpoints."""

from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from etcion.enums import ContentCategory, PurposeCategory
from etcion.exceptions import ValidationError
from etcion.metamodel.application import ApplicationComponent, ApplicationService
from etcion.metamodel.business import BusinessActor, BusinessProcess, BusinessRole
from etcion.metamodel.concepts import Concept
from etcion.metamodel.model import Model
from etcion.metamodel.motivation import Stakeholder
from etcion.metamodel.relationships import Association, Serving
from etcion.metamodel.viewpoints import Concern, View, Viewpoint


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
        from etcion.metamodel.concepts import Element

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
    def test_raises_etcion_validation_error_not_pydantic(self, actor_viewpoint: Viewpoint) -> None:
        """Confirm View.add() raises etcion.exceptions.ValidationError."""
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


# ---------------------------------------------------------------------------
# Fixtures for TestViewToModel
# ---------------------------------------------------------------------------


@pytest.fixture
def mixed_model() -> Model:
    """A model containing both Business and Application elements plus relationships."""
    actor = BusinessActor(name="Alice")
    role = BusinessRole(name="Manager")
    comp = ApplicationComponent(name="Backend")
    svc = ApplicationService(name="API")

    # Relationship between two Business elements (both survive under Business VP)
    bus_assoc = Association(name="manages", source=actor, target=role)
    # Relationship crossing layer boundaries — comp->svc (both Application)
    app_serving = Serving(name="serves", source=comp, target=svc)
    # Relationship that straddles excluded and included — actor->comp
    cross_layer = Association(name="uses", source=actor, target=comp)

    m = Model()
    for concept in (actor, role, comp, svc, bus_assoc, app_serving, cross_layer):
        m.add(concept)
    return m


@pytest.fixture
def business_only_viewpoint() -> Viewpoint:
    """Viewpoint permitting only Business-layer element types (no Application)."""
    return Viewpoint(
        name="Business Only",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.DETAILS,
        permitted_concept_types=frozenset({BusinessActor, BusinessRole, Association}),
    )


@pytest.fixture
def business_view(mixed_model: Model, business_only_viewpoint: Viewpoint) -> View:
    return View(governing_viewpoint=business_only_viewpoint, underlying_model=mixed_model)


# ---------------------------------------------------------------------------
# TestViewToModel
# ---------------------------------------------------------------------------


class TestViewToModel:
    def test_returns_model_instance(self, business_view: View, mixed_model: Model) -> None:
        result = business_view.to_model(mixed_model)
        assert isinstance(result, Model)

    def test_includes_permitted_elements(self, business_view: View, mixed_model: Model) -> None:
        result = business_view.to_model(mixed_model)
        result_types = {type(c) for c in result.elements}
        assert BusinessActor in result_types
        assert BusinessRole in result_types

    def test_excludes_non_permitted_elements(self, business_view: View, mixed_model: Model) -> None:
        result = business_view.to_model(mixed_model)
        result_types = {type(c) for c in result.elements}
        assert ApplicationComponent not in result_types
        assert ApplicationService not in result_types

    def test_includes_relationships_between_permitted_elements(
        self, business_view: View, mixed_model: Model
    ) -> None:
        """Association(actor -> role) has both endpoints permitted — must survive."""
        result = business_view.to_model(mixed_model)
        names = {getattr(r, "name", None) for r in result.relationships}
        assert "manages" in names

    def test_excludes_relationships_with_excluded_endpoints(
        self, business_view: View, mixed_model: Model
    ) -> None:
        """Relationships whose source or target is excluded must be dropped."""
        result = business_view.to_model(mixed_model)
        names = {getattr(r, "name", None) for r in result.relationships}
        # app_serving: both endpoints excluded
        assert "serves" not in names
        # cross_layer: target (ApplicationComponent) excluded
        assert "uses" not in names

    def test_deep_copied_elements_are_not_same_objects(
        self, business_view: View, mixed_model: Model
    ) -> None:
        """Result elements must be distinct Python objects (deep copy)."""
        result = business_view.to_model(mixed_model)
        original_ids = {id(c) for c in mixed_model.concepts}
        for c in result.concepts:
            assert id(c) not in original_ids, (
                f"{type(c).__name__} '{getattr(c, 'name', c.id)}' is the same object "
                "as the source — deep copy required"
            )

    def test_with_viewpoint_catalogue(self, mixed_model: Model) -> None:
        """Smoke-test against VIEWPOINT_CATALOGUE['Organization'] viewpoint."""
        from etcion.metamodel.viewpoint_catalogue import VIEWPOINT_CATALOGUE

        org_vp = VIEWPOINT_CATALOGUE["Organization"]
        view = View(governing_viewpoint=org_vp, underlying_model=mixed_model)
        result = view.to_model(mixed_model)
        # Organization VP permits BusinessActor, BusinessRole — check exclusion
        result_types = {type(c) for c in result.elements}
        assert ApplicationComponent not in result_types
        assert ApplicationService not in result_types
        # BusinessActor and BusinessRole ARE in Organization VP
        assert BusinessActor in result_types
        assert BusinessRole in result_types

    def test_result_is_independent(self, business_view: View, mixed_model: Model) -> None:
        """Modifying the result model must not affect the source model."""
        result = business_view.to_model(mixed_model)
        original_count = len(mixed_model)
        # Add a new concept to the result
        result.add(BusinessProcess(name="Extra"))
        assert len(mixed_model) == original_count

    def test_defaults_to_underlying_model_when_no_source(
        self, mixed_model: Model, business_only_viewpoint: Viewpoint
    ) -> None:
        """When called without an argument, to_model() uses underlying_model."""
        view = View(governing_viewpoint=business_only_viewpoint, underlying_model=mixed_model)
        result = view.to_model()
        assert isinstance(result, Model)
        result_types = {type(c) for c in result.elements}
        assert ApplicationComponent not in result_types
        assert BusinessActor in result_types

    def test_empty_model_returns_empty_model(self, business_only_viewpoint: Viewpoint) -> None:
        empty = Model()
        view = View(governing_viewpoint=business_only_viewpoint, underlying_model=empty)
        result = view.to_model(empty)
        assert isinstance(result, Model)
        assert len(result) == 0

    def test_result_element_ids_match_source(self, business_view: View, mixed_model: Model) -> None:
        """Copied elements must preserve their original IDs (different objects, same ID)."""
        result = business_view.to_model(mixed_model)
        result_ids = {c.id for c in result.elements}
        for elem in mixed_model.elements:
            if isinstance(elem, (BusinessActor, BusinessRole)):
                assert elem.id in result_ids


# ---------------------------------------------------------------------------
# Fixtures for TestViewToNetworkx
# ---------------------------------------------------------------------------


@pytest.fixture
def mixed_model_for_graph() -> Model:
    """A model with Business + Application elements for graph tests."""
    actor = BusinessActor(name="Alice")
    role = BusinessRole(name="Manager")
    comp = ApplicationComponent(name="Backend")
    svc = ApplicationService(name="API")

    # Relationship between two Business elements — survives under Business VP
    bus_assoc = Association(name="manages", source=actor, target=role)
    # Relationship between Application elements — excluded under Business VP
    app_serving = Serving(name="serves", source=comp, target=svc)

    m = Model()
    for concept in (actor, role, comp, svc, bus_assoc, app_serving):
        m.add(concept)
    return m


@pytest.fixture
def business_only_viewpoint_graph() -> Viewpoint:
    """Viewpoint permitting only Business-layer types."""
    return Viewpoint(
        name="Business Only Graph",
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.DETAILS,
        permitted_concept_types=frozenset({BusinessActor, BusinessRole, Association}),
    )


@pytest.fixture
def business_view_for_graph(
    mixed_model_for_graph: Model, business_only_viewpoint_graph: Viewpoint
) -> View:
    return View(
        governing_viewpoint=business_only_viewpoint_graph,
        underlying_model=mixed_model_for_graph,
    )


# ---------------------------------------------------------------------------
# TestViewToNetworkx
# ---------------------------------------------------------------------------


class TestViewToNetworkx:
    def test_returns_multidigraph(
        self, business_view_for_graph: View, mixed_model_for_graph: Model
    ) -> None:
        """View.to_networkx() must return a networkx.MultiDiGraph instance."""
        nx = pytest.importorskip("networkx")
        g = business_view_for_graph.to_networkx(mixed_model_for_graph)
        assert isinstance(g, nx.MultiDiGraph)

    def test_node_count_matches_filtered_model(
        self, business_view_for_graph: View, mixed_model_for_graph: Model
    ) -> None:
        """Only Business-layer elements appear as nodes; Application elements are excluded."""
        pytest.importorskip("networkx")
        g = business_view_for_graph.to_networkx(mixed_model_for_graph)
        # BusinessActor + BusinessRole = 2 nodes; ApplicationComponent and
        # ApplicationService are excluded by the viewpoint.
        assert g.number_of_nodes() == 2

    def test_edge_count_matches_filtered_model(
        self, business_view_for_graph: View, mixed_model_for_graph: Model
    ) -> None:
        """Only the cross-Business association survives; app_serving is dropped."""
        pytest.importorskip("networkx")
        g = business_view_for_graph.to_networkx(mixed_model_for_graph)
        # Association(actor -> role) survives; Serving(comp -> svc) is excluded.
        assert g.number_of_edges() == 1

    def test_node_attributes_match_model_schema(
        self, business_view_for_graph: View, mixed_model_for_graph: Model
    ) -> None:
        """Each node must carry type, name, layer, aspect, and concept attributes."""
        pytest.importorskip("networkx")
        g = business_view_for_graph.to_networkx(mixed_model_for_graph)
        for _node_id, attrs in g.nodes(data=True):
            assert "type" in attrs
            assert "name" in attrs
            assert "layer" in attrs
            assert "aspect" in attrs
            assert "concept" in attrs

    def test_import_error_without_networkx(
        self, business_view_for_graph: View, mixed_model_for_graph: Model
    ) -> None:
        """View.to_networkx() must raise ImportError when networkx is absent."""
        import sys
        import unittest.mock as mock

        with mock.patch.dict(sys.modules, {"networkx": None}):
            with pytest.raises(ImportError, match="pip install etcion\\[graph\\]"):
                # Reset the underlying model's nx cache so the guard is exercised.
                filtered = business_view_for_graph.to_model(mixed_model_for_graph)
                filtered._nx_graph = None
                filtered.to_networkx()
