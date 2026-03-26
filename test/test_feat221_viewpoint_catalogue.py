"""Tests for FEAT-22.1 -- Predefined Viewpoint Catalogue.

Covers ViewpointCatalogue class mechanics and the 5 fully-specified
viewpoints required by the brief.  Additional parametric coverage of
all 28 catalogue entries (one per XSD ViewpointsEnum token) is
exercised here as well.
"""

from __future__ import annotations

from collections.abc import Mapping
from unittest.mock import MagicMock

import pytest

from pyarchi.enums import ContentCategory, PurposeCategory
from pyarchi.metamodel.concepts import Concept
from pyarchi.metamodel.viewpoints import Viewpoint

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_viewpoint(name: str = "Test") -> Viewpoint:
    """Return a minimal Viewpoint using a real concrete type as the sole
    permitted concept type so Pydantic validation passes."""
    from pyarchi.metamodel.motivation import Goal

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
        from pyarchi.metamodel.viewpoint_catalogue import ViewpointCatalogue

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
        from pyarchi.metamodel.viewpoint_catalogue import ViewpointCatalogue

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
        from pyarchi.metamodel.viewpoint_catalogue import VIEWPOINT_CATALOGUE

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
        from pyarchi.metamodel.viewpoint_catalogue import VIEWPOINT_CATALOGUE

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
        from pyarchi.metamodel.business import BusinessActor

        assert BusinessActor in self.vp.permitted_concept_types

    def test_permitted_includes_business_role(self) -> None:
        from pyarchi.metamodel.business import BusinessRole

        assert BusinessRole in self.vp.permitted_concept_types

    def test_permitted_includes_business_collaboration(self) -> None:
        from pyarchi.metamodel.business import BusinessCollaboration

        assert BusinessCollaboration in self.vp.permitted_concept_types

    def test_permitted_includes_business_interface(self) -> None:
        from pyarchi.metamodel.business import BusinessInterface

        assert BusinessInterface in self.vp.permitted_concept_types

    def test_permitted_includes_location(self) -> None:
        from pyarchi.metamodel.elements import Location

        assert Location in self.vp.permitted_concept_types

    def test_permitted_includes_composition(self) -> None:
        from pyarchi.metamodel.relationships import Composition

        assert Composition in self.vp.permitted_concept_types

    def test_permitted_includes_aggregation(self) -> None:
        from pyarchi.metamodel.relationships import Aggregation

        assert Aggregation in self.vp.permitted_concept_types

    def test_permitted_includes_assignment(self) -> None:
        from pyarchi.metamodel.relationships import Assignment

        assert Assignment in self.vp.permitted_concept_types

    def test_permitted_includes_serving(self) -> None:
        from pyarchi.metamodel.relationships import Serving

        assert Serving in self.vp.permitted_concept_types

    def test_permitted_includes_association(self) -> None:
        from pyarchi.metamodel.relationships import Association

        assert Association in self.vp.permitted_concept_types

    def test_permitted_includes_specialization(self) -> None:
        from pyarchi.metamodel.relationships import Specialization

        assert Specialization in self.vp.permitted_concept_types

    def test_permitted_includes_realization(self) -> None:
        from pyarchi.metamodel.relationships import Realization

        assert Realization in self.vp.permitted_concept_types


class TestApplicationCooperationViewpoint:
    @pytest.fixture(autouse=True)
    def vp(self):
        from pyarchi.metamodel.viewpoint_catalogue import VIEWPOINT_CATALOGUE

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
        from pyarchi.metamodel.application import ApplicationComponent

        assert ApplicationComponent in self.vp.permitted_concept_types

    def test_permitted_includes_application_collaboration(self) -> None:
        from pyarchi.metamodel.application import ApplicationCollaboration

        assert ApplicationCollaboration in self.vp.permitted_concept_types

    def test_permitted_includes_application_interface(self) -> None:
        from pyarchi.metamodel.application import ApplicationInterface

        assert ApplicationInterface in self.vp.permitted_concept_types

    def test_permitted_includes_application_function(self) -> None:
        from pyarchi.metamodel.application import ApplicationFunction

        assert ApplicationFunction in self.vp.permitted_concept_types

    def test_permitted_includes_application_interaction(self) -> None:
        from pyarchi.metamodel.application import ApplicationInteraction

        assert ApplicationInteraction in self.vp.permitted_concept_types

    def test_permitted_includes_application_process(self) -> None:
        from pyarchi.metamodel.application import ApplicationProcess

        assert ApplicationProcess in self.vp.permitted_concept_types

    def test_permitted_includes_application_event(self) -> None:
        from pyarchi.metamodel.application import ApplicationEvent

        assert ApplicationEvent in self.vp.permitted_concept_types

    def test_permitted_includes_application_service(self) -> None:
        from pyarchi.metamodel.application import ApplicationService

        assert ApplicationService in self.vp.permitted_concept_types

    def test_permitted_includes_data_object(self) -> None:
        from pyarchi.metamodel.application import DataObject

        assert DataObject in self.vp.permitted_concept_types

    def test_permitted_includes_location(self) -> None:
        from pyarchi.metamodel.elements import Location

        assert Location in self.vp.permitted_concept_types

    def test_permitted_includes_serving(self) -> None:
        from pyarchi.metamodel.relationships import Serving

        assert Serving in self.vp.permitted_concept_types

    def test_permitted_includes_flow(self) -> None:
        from pyarchi.metamodel.relationships import Flow

        assert Flow in self.vp.permitted_concept_types

    def test_permitted_includes_triggering(self) -> None:
        from pyarchi.metamodel.relationships import Triggering

        assert Triggering in self.vp.permitted_concept_types

    def test_permitted_includes_realization(self) -> None:
        from pyarchi.metamodel.relationships import Realization

        assert Realization in self.vp.permitted_concept_types

    def test_permitted_includes_access(self) -> None:
        from pyarchi.metamodel.relationships import Access

        assert Access in self.vp.permitted_concept_types

    def test_permitted_includes_composition(self) -> None:
        from pyarchi.metamodel.relationships import Composition

        assert Composition in self.vp.permitted_concept_types

    def test_permitted_includes_aggregation(self) -> None:
        from pyarchi.metamodel.relationships import Aggregation

        assert Aggregation in self.vp.permitted_concept_types

    def test_permitted_includes_assignment(self) -> None:
        from pyarchi.metamodel.relationships import Assignment

        assert Assignment in self.vp.permitted_concept_types

    def test_permitted_includes_association(self) -> None:
        from pyarchi.metamodel.relationships import Association

        assert Association in self.vp.permitted_concept_types

    def test_permitted_includes_specialization(self) -> None:
        from pyarchi.metamodel.relationships import Specialization

        assert Specialization in self.vp.permitted_concept_types


class TestMotivationViewpoint:
    @pytest.fixture(autouse=True)
    def vp(self):
        from pyarchi.metamodel.viewpoint_catalogue import VIEWPOINT_CATALOGUE

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
        from pyarchi.metamodel.motivation import Stakeholder

        assert Stakeholder in self.vp.permitted_concept_types

    def test_permitted_includes_driver(self) -> None:
        from pyarchi.metamodel.motivation import Driver

        assert Driver in self.vp.permitted_concept_types

    def test_permitted_includes_assessment(self) -> None:
        from pyarchi.metamodel.motivation import Assessment

        assert Assessment in self.vp.permitted_concept_types

    def test_permitted_includes_goal(self) -> None:
        from pyarchi.metamodel.motivation import Goal

        assert Goal in self.vp.permitted_concept_types

    def test_permitted_includes_outcome(self) -> None:
        from pyarchi.metamodel.motivation import Outcome

        assert Outcome in self.vp.permitted_concept_types

    def test_permitted_includes_principle(self) -> None:
        from pyarchi.metamodel.motivation import Principle

        assert Principle in self.vp.permitted_concept_types

    def test_permitted_includes_requirement(self) -> None:
        from pyarchi.metamodel.motivation import Requirement

        assert Requirement in self.vp.permitted_concept_types

    def test_permitted_includes_constraint(self) -> None:
        from pyarchi.metamodel.motivation import Constraint

        assert Constraint in self.vp.permitted_concept_types

    def test_permitted_includes_meaning(self) -> None:
        from pyarchi.metamodel.motivation import Meaning

        assert Meaning in self.vp.permitted_concept_types

    def test_permitted_includes_value(self) -> None:
        from pyarchi.metamodel.motivation import Value

        assert Value in self.vp.permitted_concept_types

    def test_permitted_includes_influence(self) -> None:
        from pyarchi.metamodel.relationships import Influence

        assert Influence in self.vp.permitted_concept_types

    def test_permitted_includes_realization(self) -> None:
        from pyarchi.metamodel.relationships import Realization

        assert Realization in self.vp.permitted_concept_types

    def test_permitted_includes_association(self) -> None:
        from pyarchi.metamodel.relationships import Association

        assert Association in self.vp.permitted_concept_types

    def test_permitted_includes_specialization(self) -> None:
        from pyarchi.metamodel.relationships import Specialization

        assert Specialization in self.vp.permitted_concept_types

    def test_permitted_includes_composition(self) -> None:
        from pyarchi.metamodel.relationships import Composition

        assert Composition in self.vp.permitted_concept_types

    def test_permitted_includes_aggregation(self) -> None:
        from pyarchi.metamodel.relationships import Aggregation

        assert Aggregation in self.vp.permitted_concept_types


class TestStrategyViewpoint:
    @pytest.fixture(autouse=True)
    def vp(self):
        from pyarchi.metamodel.viewpoint_catalogue import VIEWPOINT_CATALOGUE

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
        from pyarchi.metamodel.strategy import Resource

        assert Resource in self.vp.permitted_concept_types

    def test_permitted_includes_capability(self) -> None:
        from pyarchi.metamodel.strategy import Capability

        assert Capability in self.vp.permitted_concept_types

    def test_permitted_includes_value_stream(self) -> None:
        from pyarchi.metamodel.strategy import ValueStream

        assert ValueStream in self.vp.permitted_concept_types

    def test_permitted_includes_course_of_action(self) -> None:
        from pyarchi.metamodel.strategy import CourseOfAction

        assert CourseOfAction in self.vp.permitted_concept_types

    def test_permitted_includes_composition(self) -> None:
        from pyarchi.metamodel.relationships import Composition

        assert Composition in self.vp.permitted_concept_types

    def test_permitted_includes_aggregation(self) -> None:
        from pyarchi.metamodel.relationships import Aggregation

        assert Aggregation in self.vp.permitted_concept_types

    def test_permitted_includes_assignment(self) -> None:
        from pyarchi.metamodel.relationships import Assignment

        assert Assignment in self.vp.permitted_concept_types

    def test_permitted_includes_realization(self) -> None:
        from pyarchi.metamodel.relationships import Realization

        assert Realization in self.vp.permitted_concept_types

    def test_permitted_includes_serving(self) -> None:
        from pyarchi.metamodel.relationships import Serving

        assert Serving in self.vp.permitted_concept_types

    def test_permitted_includes_flow(self) -> None:
        from pyarchi.metamodel.relationships import Flow

        assert Flow in self.vp.permitted_concept_types

    def test_permitted_includes_triggering(self) -> None:
        from pyarchi.metamodel.relationships import Triggering

        assert Triggering in self.vp.permitted_concept_types

    def test_permitted_includes_access(self) -> None:
        from pyarchi.metamodel.relationships import Access

        assert Access in self.vp.permitted_concept_types

    def test_permitted_includes_influence(self) -> None:
        from pyarchi.metamodel.relationships import Influence

        assert Influence in self.vp.permitted_concept_types

    def test_permitted_includes_association(self) -> None:
        from pyarchi.metamodel.relationships import Association

        assert Association in self.vp.permitted_concept_types

    def test_permitted_includes_specialization(self) -> None:
        from pyarchi.metamodel.relationships import Specialization

        assert Specialization in self.vp.permitted_concept_types


class TestImplementationAndMigrationViewpoint:
    @pytest.fixture(autouse=True)
    def vp(self):
        from pyarchi.metamodel.viewpoint_catalogue import VIEWPOINT_CATALOGUE

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
        from pyarchi.metamodel.implementation_migration import WorkPackage

        assert WorkPackage in self.vp.permitted_concept_types

    def test_permitted_includes_deliverable(self) -> None:
        from pyarchi.metamodel.implementation_migration import Deliverable

        assert Deliverable in self.vp.permitted_concept_types

    def test_permitted_includes_implementation_event(self) -> None:
        from pyarchi.metamodel.implementation_migration import ImplementationEvent

        assert ImplementationEvent in self.vp.permitted_concept_types

    def test_permitted_includes_plateau(self) -> None:
        from pyarchi.metamodel.implementation_migration import Plateau

        assert Plateau in self.vp.permitted_concept_types

    def test_permitted_includes_gap(self) -> None:
        from pyarchi.metamodel.implementation_migration import Gap

        assert Gap in self.vp.permitted_concept_types

    def test_permitted_includes_location(self) -> None:
        from pyarchi.metamodel.elements import Location

        assert Location in self.vp.permitted_concept_types

    def test_permitted_includes_composition(self) -> None:
        from pyarchi.metamodel.relationships import Composition

        assert Composition in self.vp.permitted_concept_types

    def test_permitted_includes_aggregation(self) -> None:
        from pyarchi.metamodel.relationships import Aggregation

        assert Aggregation in self.vp.permitted_concept_types

    def test_permitted_includes_assignment(self) -> None:
        from pyarchi.metamodel.relationships import Assignment

        assert Assignment in self.vp.permitted_concept_types

    def test_permitted_includes_realization(self) -> None:
        from pyarchi.metamodel.relationships import Realization

        assert Realization in self.vp.permitted_concept_types

    def test_permitted_includes_serving(self) -> None:
        from pyarchi.metamodel.relationships import Serving

        assert Serving in self.vp.permitted_concept_types

    def test_permitted_includes_triggering(self) -> None:
        from pyarchi.metamodel.relationships import Triggering

        assert Triggering in self.vp.permitted_concept_types

    def test_permitted_includes_flow(self) -> None:
        from pyarchi.metamodel.relationships import Flow

        assert Flow in self.vp.permitted_concept_types

    def test_permitted_includes_association(self) -> None:
        from pyarchi.metamodel.relationships import Association

        assert Association in self.vp.permitted_concept_types

    def test_permitted_includes_specialization(self) -> None:
        from pyarchi.metamodel.relationships import Specialization

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
        from pyarchi.metamodel.viewpoint_catalogue import VIEWPOINT_CATALOGUE

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
