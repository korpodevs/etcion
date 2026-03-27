"""Merged tests: test_feat221_viewpoint_catalogue, test_feat222_viewpoint_catalogue."""

from __future__ import annotations

from collections.abc import Mapping
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError as PydanticValidationError

from etcion import VIEWPOINT_CATALOGUE
from etcion.enums import ContentCategory, PurposeCategory
from etcion.metamodel.concepts import Concept
from etcion.metamodel.viewpoints import Viewpoint

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_viewpoint(name: str = "Test") -> Viewpoint:
    """Return a minimal Viewpoint using a real concrete type as the sole
    permitted concept type so Pydantic validation passes."""
    from etcion.metamodel.motivation import Goal

    return Viewpoint(
        name=name,
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.DETAILS,
        permitted_concept_types=frozenset({Goal}),
    )


# ---------------------------------------------------------------------------
# ViewpointCatalogue mechanics
# ---------------------------------------------------------------------------


class TestViewpointCatalogueMechanics:
    """Unit tests for ViewpointCatalogue independent of real builders."""

    def _make_catalogue(self, keys: list[str]):
        """Build a catalogue with mock builders for the given keys."""
        from etcion.metamodel.viewpoint_catalogue import ViewpointCatalogue

        builders = {k: MagicMock(return_value=_make_viewpoint(k)) for k in keys}
        return ViewpointCatalogue(builders), builders

    def test_getitem_returns_viewpoint(self) -> None:
        cat, _ = self._make_catalogue(["Alpha"])
        result = cat["Alpha"]
        assert isinstance(result, Viewpoint)

    def test_getitem_nonexistent_raises_key_error(self) -> None:
        cat, _ = self._make_catalogue(["Alpha"])
        with pytest.raises(KeyError):
            _ = cat["NonExistent"]

    def test_len_matches_builder_count(self) -> None:
        keys = ["Alpha", "Beta", "Gamma"]
        cat, _ = self._make_catalogue(keys)
        assert len(cat) == 3

    def test_iter_yields_all_keys(self) -> None:
        keys = ["Alpha", "Beta", "Gamma"]
        cat, _ = self._make_catalogue(keys)
        assert set(cat) == set(keys)

    def test_caching_same_key_returns_same_object(self) -> None:
        cat, _ = self._make_catalogue(["Alpha"])
        first = cat["Alpha"]
        second = cat["Alpha"]
        assert first is second

    def test_caching_builder_called_only_once(self) -> None:
        cat, builders = self._make_catalogue(["Alpha"])
        _ = cat["Alpha"]
        _ = cat["Alpha"]
        builders["Alpha"].assert_called_once()

    def test_is_mapping(self) -> None:
        from etcion.metamodel.viewpoint_catalogue import ViewpointCatalogue

        assert issubclass(ViewpointCatalogue, Mapping)

    def test_no_setitem(self) -> None:
        cat, _ = self._make_catalogue(["Alpha"])
        with pytest.raises((AttributeError, TypeError)):
            cat["Alpha"] = _make_viewpoint("Alpha")  # type: ignore[index]

    def test_contains_true(self) -> None:
        cat, _ = self._make_catalogue(["Alpha"])
        assert "Alpha" in cat

    def test_contains_false(self) -> None:
        cat, _ = self._make_catalogue(["Alpha"])
        assert "NonExistent" not in cat


# ---------------------------------------------------------------------------
# VIEWPOINT_CATALOGUE singleton
# ---------------------------------------------------------------------------


class TestViewpointCatalogueSingleton:
    """Tests against the module-level VIEWPOINT_CATALOGUE instance."""

    @pytest.fixture(autouse=True)
    def import_catalogue(self):
        from etcion.metamodel.viewpoint_catalogue import VIEWPOINT_CATALOGUE

        self.catalogue = VIEWPOINT_CATALOGUE

    def test_catalogue_has_28_entries(self) -> None:
        assert len(self.catalogue) == 28

    def test_catalogue_is_mapping(self) -> None:
        assert isinstance(self.catalogue, Mapping)

    def test_lookup_organization(self) -> None:
        vp = self.catalogue["Organization"]
        assert vp.name == "Organization"

    def test_lookup_application_cooperation(self) -> None:
        vp = self.catalogue["Application Cooperation"]
        assert vp.name == "Application Cooperation"


# ---------------------------------------------------------------------------
# Fully-specified viewpoints (5 from the brief)
# ---------------------------------------------------------------------------


class TestOrganizationViewpoint:
    @pytest.fixture(autouse=True)
    def vp(self):
        from etcion.metamodel.viewpoint_catalogue import VIEWPOINT_CATALOGUE

        self.vp = VIEWPOINT_CATALOGUE["Organization"]

    def test_name(self) -> None:
        assert self.vp.name == "Organization"

    def test_purpose(self) -> None:
        assert self.vp.purpose is PurposeCategory.DESIGNING

    def test_content(self) -> None:
        assert self.vp.content is ContentCategory.COHERENCE

    def test_permitted_concept_types_non_empty(self) -> None:
        assert len(self.vp.permitted_concept_types) > 0

    def test_permitted_includes_business_actor(self) -> None:
        from etcion.metamodel.business import BusinessActor

        assert BusinessActor in self.vp.permitted_concept_types

    def test_permitted_includes_business_role(self) -> None:
        from etcion.metamodel.business import BusinessRole

        assert BusinessRole in self.vp.permitted_concept_types

    def test_permitted_includes_business_collaboration(self) -> None:
        from etcion.metamodel.business import BusinessCollaboration

        assert BusinessCollaboration in self.vp.permitted_concept_types

    def test_permitted_includes_business_interface(self) -> None:
        from etcion.metamodel.business import BusinessInterface

        assert BusinessInterface in self.vp.permitted_concept_types

    def test_permitted_includes_location(self) -> None:
        from etcion.metamodel.elements import Location

        assert Location in self.vp.permitted_concept_types

    def test_permitted_includes_composition(self) -> None:
        from etcion.metamodel.relationships import Composition

        assert Composition in self.vp.permitted_concept_types

    def test_permitted_includes_aggregation(self) -> None:
        from etcion.metamodel.relationships import Aggregation

        assert Aggregation in self.vp.permitted_concept_types

    def test_permitted_includes_assignment(self) -> None:
        from etcion.metamodel.relationships import Assignment

        assert Assignment in self.vp.permitted_concept_types

    def test_permitted_includes_serving(self) -> None:
        from etcion.metamodel.relationships import Serving

        assert Serving in self.vp.permitted_concept_types

    def test_permitted_includes_association(self) -> None:
        from etcion.metamodel.relationships import Association

        assert Association in self.vp.permitted_concept_types

    def test_permitted_includes_specialization(self) -> None:
        from etcion.metamodel.relationships import Specialization

        assert Specialization in self.vp.permitted_concept_types

    def test_permitted_includes_realization(self) -> None:
        from etcion.metamodel.relationships import Realization

        assert Realization in self.vp.permitted_concept_types


class TestApplicationCooperationViewpoint:
    @pytest.fixture(autouse=True)
    def vp(self):
        from etcion.metamodel.viewpoint_catalogue import VIEWPOINT_CATALOGUE

        self.vp = VIEWPOINT_CATALOGUE["Application Cooperation"]

    def test_name(self) -> None:
        assert self.vp.name == "Application Cooperation"

    def test_purpose(self) -> None:
        assert self.vp.purpose is PurposeCategory.DESIGNING

    def test_content(self) -> None:
        assert self.vp.content is ContentCategory.COHERENCE

    def test_permitted_concept_types_non_empty(self) -> None:
        assert len(self.vp.permitted_concept_types) > 0

    def test_permitted_includes_application_component(self) -> None:
        from etcion.metamodel.application import ApplicationComponent

        assert ApplicationComponent in self.vp.permitted_concept_types

    def test_permitted_includes_application_collaboration(self) -> None:
        from etcion.metamodel.application import ApplicationCollaboration

        assert ApplicationCollaboration in self.vp.permitted_concept_types

    def test_permitted_includes_application_interface(self) -> None:
        from etcion.metamodel.application import ApplicationInterface

        assert ApplicationInterface in self.vp.permitted_concept_types

    def test_permitted_includes_application_function(self) -> None:
        from etcion.metamodel.application import ApplicationFunction

        assert ApplicationFunction in self.vp.permitted_concept_types

    def test_permitted_includes_application_interaction(self) -> None:
        from etcion.metamodel.application import ApplicationInteraction

        assert ApplicationInteraction in self.vp.permitted_concept_types

    def test_permitted_includes_application_process(self) -> None:
        from etcion.metamodel.application import ApplicationProcess

        assert ApplicationProcess in self.vp.permitted_concept_types

    def test_permitted_includes_application_event(self) -> None:
        from etcion.metamodel.application import ApplicationEvent

        assert ApplicationEvent in self.vp.permitted_concept_types

    def test_permitted_includes_application_service(self) -> None:
        from etcion.metamodel.application import ApplicationService

        assert ApplicationService in self.vp.permitted_concept_types

    def test_permitted_includes_data_object(self) -> None:
        from etcion.metamodel.application import DataObject

        assert DataObject in self.vp.permitted_concept_types

    def test_permitted_includes_location(self) -> None:
        from etcion.metamodel.elements import Location

        assert Location in self.vp.permitted_concept_types

    def test_permitted_includes_serving(self) -> None:
        from etcion.metamodel.relationships import Serving

        assert Serving in self.vp.permitted_concept_types

    def test_permitted_includes_flow(self) -> None:
        from etcion.metamodel.relationships import Flow

        assert Flow in self.vp.permitted_concept_types

    def test_permitted_includes_triggering(self) -> None:
        from etcion.metamodel.relationships import Triggering

        assert Triggering in self.vp.permitted_concept_types

    def test_permitted_includes_realization(self) -> None:
        from etcion.metamodel.relationships import Realization

        assert Realization in self.vp.permitted_concept_types

    def test_permitted_includes_access(self) -> None:
        from etcion.metamodel.relationships import Access

        assert Access in self.vp.permitted_concept_types

    def test_permitted_includes_composition(self) -> None:
        from etcion.metamodel.relationships import Composition

        assert Composition in self.vp.permitted_concept_types

    def test_permitted_includes_aggregation(self) -> None:
        from etcion.metamodel.relationships import Aggregation

        assert Aggregation in self.vp.permitted_concept_types

    def test_permitted_includes_assignment(self) -> None:
        from etcion.metamodel.relationships import Assignment

        assert Assignment in self.vp.permitted_concept_types

    def test_permitted_includes_association(self) -> None:
        from etcion.metamodel.relationships import Association

        assert Association in self.vp.permitted_concept_types

    def test_permitted_includes_specialization(self) -> None:
        from etcion.metamodel.relationships import Specialization

        assert Specialization in self.vp.permitted_concept_types


class TestMotivationViewpoint:
    @pytest.fixture(autouse=True)
    def vp(self):
        from etcion.metamodel.viewpoint_catalogue import VIEWPOINT_CATALOGUE

        self.vp = VIEWPOINT_CATALOGUE["Motivation"]

    def test_name(self) -> None:
        assert self.vp.name == "Motivation"

    def test_purpose(self) -> None:
        assert self.vp.purpose is PurposeCategory.DECIDING

    def test_content(self) -> None:
        assert self.vp.content is ContentCategory.OVERVIEW

    def test_permitted_concept_types_non_empty(self) -> None:
        assert len(self.vp.permitted_concept_types) > 0

    def test_permitted_includes_stakeholder(self) -> None:
        from etcion.metamodel.motivation import Stakeholder

        assert Stakeholder in self.vp.permitted_concept_types

    def test_permitted_includes_driver(self) -> None:
        from etcion.metamodel.motivation import Driver

        assert Driver in self.vp.permitted_concept_types

    def test_permitted_includes_assessment(self) -> None:
        from etcion.metamodel.motivation import Assessment

        assert Assessment in self.vp.permitted_concept_types

    def test_permitted_includes_goal(self) -> None:
        from etcion.metamodel.motivation import Goal

        assert Goal in self.vp.permitted_concept_types

    def test_permitted_includes_outcome(self) -> None:
        from etcion.metamodel.motivation import Outcome

        assert Outcome in self.vp.permitted_concept_types

    def test_permitted_includes_principle(self) -> None:
        from etcion.metamodel.motivation import Principle

        assert Principle in self.vp.permitted_concept_types

    def test_permitted_includes_requirement(self) -> None:
        from etcion.metamodel.motivation import Requirement

        assert Requirement in self.vp.permitted_concept_types

    def test_permitted_includes_constraint(self) -> None:
        from etcion.metamodel.motivation import Constraint

        assert Constraint in self.vp.permitted_concept_types

    def test_permitted_includes_meaning(self) -> None:
        from etcion.metamodel.motivation import Meaning

        assert Meaning in self.vp.permitted_concept_types

    def test_permitted_includes_value(self) -> None:
        from etcion.metamodel.motivation import Value

        assert Value in self.vp.permitted_concept_types

    def test_permitted_includes_influence(self) -> None:
        from etcion.metamodel.relationships import Influence

        assert Influence in self.vp.permitted_concept_types

    def test_permitted_includes_realization(self) -> None:
        from etcion.metamodel.relationships import Realization

        assert Realization in self.vp.permitted_concept_types

    def test_permitted_includes_association(self) -> None:
        from etcion.metamodel.relationships import Association

        assert Association in self.vp.permitted_concept_types

    def test_permitted_includes_specialization(self) -> None:
        from etcion.metamodel.relationships import Specialization

        assert Specialization in self.vp.permitted_concept_types

    def test_permitted_includes_composition(self) -> None:
        from etcion.metamodel.relationships import Composition

        assert Composition in self.vp.permitted_concept_types

    def test_permitted_includes_aggregation(self) -> None:
        from etcion.metamodel.relationships import Aggregation

        assert Aggregation in self.vp.permitted_concept_types


class TestStrategyViewpoint:
    @pytest.fixture(autouse=True)
    def vp(self):
        from etcion.metamodel.viewpoint_catalogue import VIEWPOINT_CATALOGUE

        self.vp = VIEWPOINT_CATALOGUE["Strategy"]

    def test_name(self) -> None:
        assert self.vp.name == "Strategy"

    def test_purpose(self) -> None:
        assert self.vp.purpose is PurposeCategory.DESIGNING

    def test_content(self) -> None:
        assert self.vp.content is ContentCategory.OVERVIEW

    def test_permitted_concept_types_non_empty(self) -> None:
        assert len(self.vp.permitted_concept_types) > 0

    def test_permitted_includes_resource(self) -> None:
        from etcion.metamodel.strategy import Resource

        assert Resource in self.vp.permitted_concept_types

    def test_permitted_includes_capability(self) -> None:
        from etcion.metamodel.strategy import Capability

        assert Capability in self.vp.permitted_concept_types

    def test_permitted_includes_value_stream(self) -> None:
        from etcion.metamodel.strategy import ValueStream

        assert ValueStream in self.vp.permitted_concept_types

    def test_permitted_includes_course_of_action(self) -> None:
        from etcion.metamodel.strategy import CourseOfAction

        assert CourseOfAction in self.vp.permitted_concept_types

    def test_permitted_includes_composition(self) -> None:
        from etcion.metamodel.relationships import Composition

        assert Composition in self.vp.permitted_concept_types

    def test_permitted_includes_aggregation(self) -> None:
        from etcion.metamodel.relationships import Aggregation

        assert Aggregation in self.vp.permitted_concept_types

    def test_permitted_includes_assignment(self) -> None:
        from etcion.metamodel.relationships import Assignment

        assert Assignment in self.vp.permitted_concept_types

    def test_permitted_includes_realization(self) -> None:
        from etcion.metamodel.relationships import Realization

        assert Realization in self.vp.permitted_concept_types

    def test_permitted_includes_serving(self) -> None:
        from etcion.metamodel.relationships import Serving

        assert Serving in self.vp.permitted_concept_types

    def test_permitted_includes_flow(self) -> None:
        from etcion.metamodel.relationships import Flow

        assert Flow in self.vp.permitted_concept_types

    def test_permitted_includes_triggering(self) -> None:
        from etcion.metamodel.relationships import Triggering

        assert Triggering in self.vp.permitted_concept_types

    def test_permitted_includes_access(self) -> None:
        from etcion.metamodel.relationships import Access

        assert Access in self.vp.permitted_concept_types

    def test_permitted_includes_influence(self) -> None:
        from etcion.metamodel.relationships import Influence

        assert Influence in self.vp.permitted_concept_types

    def test_permitted_includes_association(self) -> None:
        from etcion.metamodel.relationships import Association

        assert Association in self.vp.permitted_concept_types

    def test_permitted_includes_specialization(self) -> None:
        from etcion.metamodel.relationships import Specialization

        assert Specialization in self.vp.permitted_concept_types


class TestImplementationAndMigrationViewpoint:
    @pytest.fixture(autouse=True)
    def vp(self):
        from etcion.metamodel.viewpoint_catalogue import VIEWPOINT_CATALOGUE

        self.vp = VIEWPOINT_CATALOGUE["Implementation and Migration"]

    def test_name(self) -> None:
        assert self.vp.name == "Implementation and Migration"

    def test_purpose(self) -> None:
        assert self.vp.purpose is PurposeCategory.DESIGNING

    def test_content(self) -> None:
        assert self.vp.content is ContentCategory.OVERVIEW

    def test_permitted_concept_types_non_empty(self) -> None:
        assert len(self.vp.permitted_concept_types) > 0

    def test_permitted_includes_work_package(self) -> None:
        from etcion.metamodel.implementation_migration import WorkPackage

        assert WorkPackage in self.vp.permitted_concept_types

    def test_permitted_includes_deliverable(self) -> None:
        from etcion.metamodel.implementation_migration import Deliverable

        assert Deliverable in self.vp.permitted_concept_types

    def test_permitted_includes_implementation_event(self) -> None:
        from etcion.metamodel.implementation_migration import ImplementationEvent

        assert ImplementationEvent in self.vp.permitted_concept_types

    def test_permitted_includes_plateau(self) -> None:
        from etcion.metamodel.implementation_migration import Plateau

        assert Plateau in self.vp.permitted_concept_types

    def test_permitted_includes_gap(self) -> None:
        from etcion.metamodel.implementation_migration import Gap

        assert Gap in self.vp.permitted_concept_types

    def test_permitted_includes_location(self) -> None:
        from etcion.metamodel.elements import Location

        assert Location in self.vp.permitted_concept_types

    def test_permitted_includes_composition(self) -> None:
        from etcion.metamodel.relationships import Composition

        assert Composition in self.vp.permitted_concept_types

    def test_permitted_includes_aggregation(self) -> None:
        from etcion.metamodel.relationships import Aggregation

        assert Aggregation in self.vp.permitted_concept_types

    def test_permitted_includes_assignment(self) -> None:
        from etcion.metamodel.relationships import Assignment

        assert Assignment in self.vp.permitted_concept_types

    def test_permitted_includes_realization(self) -> None:
        from etcion.metamodel.relationships import Realization

        assert Realization in self.vp.permitted_concept_types

    def test_permitted_includes_serving(self) -> None:
        from etcion.metamodel.relationships import Serving

        assert Serving in self.vp.permitted_concept_types

    def test_permitted_includes_triggering(self) -> None:
        from etcion.metamodel.relationships import Triggering

        assert Triggering in self.vp.permitted_concept_types

    def test_permitted_includes_flow(self) -> None:
        from etcion.metamodel.relationships import Flow

        assert Flow in self.vp.permitted_concept_types

    def test_permitted_includes_association(self) -> None:
        from etcion.metamodel.relationships import Association

        assert Association in self.vp.permitted_concept_types

    def test_permitted_includes_specialization(self) -> None:
        from etcion.metamodel.relationships import Specialization

        assert Specialization in self.vp.permitted_concept_types


# ---------------------------------------------------------------------------
# Parametric coverage: all 28 catalogue entries
# ---------------------------------------------------------------------------

ALL_VIEWPOINT_KEYS = [
    "Organization",
    "Application Platform",
    "Application Structure",
    "Information Structure",
    "Technology",
    "Layered",
    "Physical",
    "Product",
    "Application Usage",
    "Technology Usage",
    "Business Process Cooperation",
    "Application Cooperation",
    "Service Realization",
    "Implementation and Deployment",
    "Goal Realization",
    "Goal Contribution",
    "Principles",
    "Requirements Realization",
    "Motivation",
    "Strategy",
    "Capability Map",
    "Outcome Realization",
    "Resource Map",
    "Value Stream",
    "Project",
    "Migration",
    "Implementation and Migration",
    "Stakeholder",
]


class TestAllViewpoints:
    """Parametric tests covering all 28 catalogue entries."""

    @pytest.fixture(autouse=True)
    def catalogue(self):
        from etcion.metamodel.viewpoint_catalogue import VIEWPOINT_CATALOGUE

        self.catalogue = VIEWPOINT_CATALOGUE

    @pytest.mark.parametrize("key", ALL_VIEWPOINT_KEYS)
    def test_key_exists_in_catalogue(self, key: str) -> None:
        assert key in self.catalogue

    @pytest.mark.parametrize("key", ALL_VIEWPOINT_KEYS)
    def test_name_matches_key(self, key: str) -> None:
        vp = self.catalogue[key]
        assert vp.name == key

    @pytest.mark.parametrize("key", ALL_VIEWPOINT_KEYS)
    def test_purpose_is_valid_enum(self, key: str) -> None:
        vp = self.catalogue[key]
        assert isinstance(vp.purpose, PurposeCategory)

    @pytest.mark.parametrize("key", ALL_VIEWPOINT_KEYS)
    def test_content_is_valid_enum(self, key: str) -> None:
        vp = self.catalogue[key]
        assert isinstance(vp.content, ContentCategory)

    @pytest.mark.parametrize("key", ALL_VIEWPOINT_KEYS)
    def test_permitted_concept_types_non_empty(self, key: str) -> None:
        vp = self.catalogue[key]
        assert len(vp.permitted_concept_types) > 0

    @pytest.mark.parametrize("key", ALL_VIEWPOINT_KEYS)
    def test_all_types_are_concept_subclasses(self, key: str) -> None:
        vp = self.catalogue[key]
        for t in vp.permitted_concept_types:
            assert issubclass(t, Concept), (
                f"Type {t!r} in '{key}' permitted_concept_types is not a Concept subclass"
            )

    @pytest.mark.parametrize("key", ALL_VIEWPOINT_KEYS)
    def test_caching_identity(self, key: str) -> None:
        """Accessing the same key twice returns the identical object."""
        first = self.catalogue[key]
        second = self.catalogue[key]
        assert first is second


# ---------------------------------------------------------------------------
# STORY-22.2.1 / STORY-22.2.3: Catalogue contract on the real singleton
# ---------------------------------------------------------------------------


def test_catalogue_length_is_28() -> None:
    """The catalogue must contain exactly 28 viewpoints (XSD token count)."""
    assert len(VIEWPOINT_CATALOGUE) == 28


def test_catalogue_is_not_mutable() -> None:
    """ViewpointCatalogue is a Mapping, not a MutableMapping.

    It must not expose __setitem__ or __delitem__.
    """
    assert not hasattr(VIEWPOINT_CATALOGUE, "__setitem__")
    assert not hasattr(VIEWPOINT_CATALOGUE, "__delitem__")


def test_unknown_key_raises_key_error() -> None:
    """Accessing a non-existent viewpoint key raises KeyError."""
    with pytest.raises(KeyError):
        VIEWPOINT_CATALOGUE["Nonexistent Viewpoint"]  # noqa: PIE806


# ---------------------------------------------------------------------------
# Caching behaviour (STORY-22.2.1)
# ---------------------------------------------------------------------------


def test_catalogue_caches_viewpoint_instances() -> None:
    """The same key must return the identical object on repeated access."""
    vp1 = VIEWPOINT_CATALOGUE["Organization"]
    vp2 = VIEWPOINT_CATALOGUE["Organization"]
    assert vp1 is vp2


# ---------------------------------------------------------------------------
# Frozen Viewpoint: mutation resistance
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("key", sorted(VIEWPOINT_CATALOGUE.keys()))
def test_viewpoint_is_frozen(key: str) -> None:
    """Every catalogue entry is a frozen Pydantic model — mutation raises."""
    vp = VIEWPOINT_CATALOGUE[key]
    assert isinstance(vp, Viewpoint)
    with pytest.raises(PydanticValidationError):
        vp.name = "mutated"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# STORY-22.2.2: Top-level import surface
# ---------------------------------------------------------------------------


def test_catalogue_importable_from_top_level() -> None:
    """VIEWPOINT_CATALOGUE is importable directly from etcion."""
    import etcion

    assert hasattr(etcion, "VIEWPOINT_CATALOGUE")
    assert etcion.VIEWPOINT_CATALOGUE is VIEWPOINT_CATALOGUE


def test_catalogue_in_all() -> None:
    """VIEWPOINT_CATALOGUE is listed in etcion.__all__."""
    import etcion

    assert "VIEWPOINT_CATALOGUE" in etcion.__all__


# ---------------------------------------------------------------------------
# STORY-22.2.4: View integration
# ---------------------------------------------------------------------------


def test_view_accepts_permitted_concept() -> None:
    """A View governed by the Organization viewpoint accepts a BusinessActor."""
    from etcion import BusinessActor, Model, View

    model = Model()
    actor = BusinessActor(name="Alice")
    model.add(actor)

    vp = VIEWPOINT_CATALOGUE["Organization"]
    view = View(governing_viewpoint=vp, underlying_model=model)
    view.add(actor)
    assert actor in view.concepts


def test_view_rejects_unpermitted_concept() -> None:
    """A View governed by Organization viewpoint rejects a DataObject."""
    from etcion import DataObject, Model, View
    from etcion.exceptions import ValidationError

    model = Model()
    obj = DataObject(name="Invoice")
    model.add(obj)

    vp = VIEWPOINT_CATALOGUE["Organization"]
    view = View(governing_viewpoint=vp, underlying_model=model)
    with pytest.raises(ValidationError, match="not permitted"):
        view.add(obj)


def test_view_rejects_concept_not_in_model() -> None:
    """A View rejects a concept that is not in the underlying model.

    This verifies the membership gate in View.add() works with catalogue
    viewpoints, even when the concept type itself would be permitted.
    """
    from etcion import BusinessActor, Model, View
    from etcion.exceptions import ValidationError

    model = Model()
    orphan = BusinessActor(name="Orphan")
    # Intentionally do NOT add orphan to model.

    vp = VIEWPOINT_CATALOGUE["Organization"]
    view = View(governing_viewpoint=vp, underlying_model=model)
    with pytest.raises(ValidationError):
        view.add(orphan)
