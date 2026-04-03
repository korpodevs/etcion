"""Merged tests: test_feat221_viewpoint_catalogue, test_feat222_viewpoint_catalogue."""

from __future__ import annotations

from collections.abc import Mapping
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError as PydanticValidationError

from etcion import VIEWPOINT_CATALOGUE
from etcion.enums import ContentCategory, PurposeCategory
from etcion.metamodel.application import (
    ApplicationCollaboration,
    ApplicationComponent,
    ApplicationEvent,
    ApplicationFunction,
    ApplicationInteraction,
    ApplicationInterface,
    ApplicationProcess,
    ApplicationService,
    DataObject,
)
from etcion.metamodel.business import (
    BusinessActor,
    BusinessCollaboration,
    BusinessEvent,
    BusinessFunction,
    BusinessInteraction,
    BusinessInterface,
    BusinessObject,
    BusinessProcess,
    BusinessRole,
    BusinessService,
    Contract,
    Product,
    Representation,
)
from etcion.metamodel.concepts import Concept
from etcion.metamodel.elements import Grouping, Location
from etcion.metamodel.implementation_migration import (
    Deliverable,
    Gap,
    ImplementationEvent,
    Plateau,
    WorkPackage,
)
from etcion.metamodel.motivation import (
    Assessment,
    Constraint,
    Driver,
    Goal,
    Meaning,
    Outcome,
    Principle,
    Requirement,
    Stakeholder,
    Value,
)
from etcion.metamodel.physical import (
    DistributionNetwork,
    Equipment,
    Facility,
    Material,
)
from etcion.metamodel.relationships import (
    Access,
    Aggregation,
    Assignment,
    Association,
    Composition,
    Flow,
    Influence,
    Realization,
    Serving,
    Specialization,
    Triggering,
)
from etcion.metamodel.strategy import (
    Capability,
    CourseOfAction,
    Resource,
    ValueStream,
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
    TechnologyProcess,
    TechnologyService,
)
from etcion.metamodel.viewpoints import Viewpoint

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_viewpoint(name: str = "Test") -> Viewpoint:
    """Return a minimal Viewpoint using a real concrete type as the sole
    permitted concept type so Pydantic validation passes."""
    return Viewpoint(
        name=name,
        purpose=PurposeCategory.DESIGNING,
        content=ContentCategory.DETAILS,
        permitted_concept_types=frozenset({Goal}),
    )


# ---------------------------------------------------------------------------
# Expected permitted type sets — one entry per viewpoint
# ---------------------------------------------------------------------------

VIEWPOINT_EXPECTED: dict[str, tuple[PurposeCategory, ContentCategory, frozenset[type[Concept]]]] = {
    "Organization": (
        PurposeCategory.DESIGNING,
        ContentCategory.COHERENCE,
        frozenset(
            {
                BusinessActor,
                BusinessRole,
                BusinessCollaboration,
                BusinessInterface,
                Location,
                Composition,
                Aggregation,
                Assignment,
                Serving,
                Realization,
                Association,
                Specialization,
            }
        ),
    ),
    "Application Platform": (
        PurposeCategory.DESIGNING,
        ContentCategory.DETAILS,
        frozenset(
            {
                ApplicationComponent,
                ApplicationInterface,
                Node,
                Device,
                SystemSoftware,
                TechnologyInterface,
                TechnologyService,
                CommunicationNetwork,
                Path,
                Artifact,
                Composition,
                Aggregation,
                Assignment,
                Realization,
                Serving,
                Association,
                Specialization,
            }
        ),
    ),
    "Application Structure": (
        PurposeCategory.DESIGNING,
        ContentCategory.DETAILS,
        frozenset(
            {
                ApplicationComponent,
                ApplicationCollaboration,
                ApplicationInterface,
                ApplicationFunction,
                ApplicationInteraction,
                ApplicationProcess,
                ApplicationEvent,
                ApplicationService,
                DataObject,
                Composition,
                Aggregation,
                Assignment,
                Realization,
                Access,
                Association,
                Specialization,
            }
        ),
    ),
    "Information Structure": (
        PurposeCategory.DESIGNING,
        ContentCategory.DETAILS,
        frozenset(
            {
                BusinessObject,
                Contract,
                Representation,
                DataObject,
                Access,
                Association,
                Realization,
                Composition,
                Aggregation,
                Specialization,
            }
        ),
    ),
    "Technology": (
        PurposeCategory.DESIGNING,
        ContentCategory.DETAILS,
        frozenset(
            {
                Node,
                Device,
                SystemSoftware,
                TechnologyCollaboration,
                TechnologyInterface,
                Path,
                CommunicationNetwork,
                TechnologyFunction,
                TechnologyProcess,
                TechnologyInteraction,
                TechnologyEvent,
                TechnologyService,
                Artifact,
                Composition,
                Aggregation,
                Assignment,
                Realization,
                Serving,
                Access,
                Flow,
                Triggering,
                Association,
                Specialization,
            }
        ),
    ),
    "Layered": (
        PurposeCategory.DESIGNING,
        ContentCategory.OVERVIEW,
        frozenset(
            {
                # Strategy
                Resource,
                Capability,
                ValueStream,
                CourseOfAction,
                # Business
                BusinessActor,
                BusinessRole,
                BusinessCollaboration,
                BusinessInterface,
                BusinessProcess,
                BusinessFunction,
                BusinessInteraction,
                BusinessEvent,
                BusinessService,
                BusinessObject,
                Contract,
                Representation,
                Product,
                # Application
                ApplicationComponent,
                ApplicationCollaboration,
                ApplicationInterface,
                ApplicationFunction,
                ApplicationInteraction,
                ApplicationProcess,
                ApplicationEvent,
                ApplicationService,
                DataObject,
                # Technology
                Node,
                Device,
                SystemSoftware,
                TechnologyCollaboration,
                TechnologyInterface,
                Path,
                CommunicationNetwork,
                TechnologyFunction,
                TechnologyProcess,
                TechnologyInteraction,
                TechnologyEvent,
                TechnologyService,
                Artifact,
                # Physical
                Equipment,
                Facility,
                DistributionNetwork,
                Material,
                # Motivation
                Stakeholder,
                Driver,
                Assessment,
                Goal,
                Outcome,
                Principle,
                Requirement,
                Constraint,
                Meaning,
                Value,
                # Implementation & Migration
                WorkPackage,
                Deliverable,
                ImplementationEvent,
                Plateau,
                Gap,
                # Composite
                Grouping,
                Location,
                # Relationships
                Composition,
                Aggregation,
                Assignment,
                Realization,
                Serving,
                Access,
                Influence,
                Association,
                Triggering,
                Flow,
                Specialization,
            }
        ),
    ),
    "Physical": (
        PurposeCategory.DESIGNING,
        ContentCategory.DETAILS,
        frozenset(
            {
                Equipment,
                Facility,
                DistributionNetwork,
                Material,
                Node,
                Device,
                SystemSoftware,
                TechnologyInterface,
                TechnologyService,
                Artifact,
                Location,
                Composition,
                Aggregation,
                Assignment,
                Realization,
                Serving,
                Flow,
                Association,
                Specialization,
            }
        ),
    ),
    "Product": (
        PurposeCategory.DESIGNING,
        ContentCategory.COHERENCE,
        frozenset(
            {
                Product,
                BusinessService,
                BusinessInterface,
                BusinessEvent,
                BusinessRole,
                BusinessActor,
                BusinessObject,
                Contract,
                ApplicationService,
                ApplicationComponent,
                Serving,
                Composition,
                Aggregation,
                Association,
                Realization,
                Specialization,
            }
        ),
    ),
    "Application Usage": (
        PurposeCategory.DESIGNING,
        ContentCategory.COHERENCE,
        frozenset(
            {
                BusinessProcess,
                BusinessFunction,
                BusinessInteraction,
                BusinessEvent,
                BusinessService,
                BusinessRole,
                BusinessActor,
                BusinessCollaboration,
                BusinessInterface,
                ApplicationComponent,
                ApplicationCollaboration,
                ApplicationInterface,
                ApplicationFunction,
                ApplicationInteraction,
                ApplicationProcess,
                ApplicationEvent,
                ApplicationService,
                DataObject,
                Serving,
                Realization,
                Access,
                Composition,
                Aggregation,
                Assignment,
                Association,
                Specialization,
                Triggering,
                Flow,
            }
        ),
    ),
    "Technology Usage": (
        PurposeCategory.DESIGNING,
        ContentCategory.COHERENCE,
        frozenset(
            {
                ApplicationComponent,
                ApplicationCollaboration,
                ApplicationInterface,
                ApplicationFunction,
                ApplicationInteraction,
                ApplicationProcess,
                ApplicationEvent,
                ApplicationService,
                DataObject,
                Artifact,
                Node,
                Device,
                SystemSoftware,
                TechnologyCollaboration,
                TechnologyInterface,
                Path,
                CommunicationNetwork,
                TechnologyFunction,
                TechnologyProcess,
                TechnologyInteraction,
                TechnologyEvent,
                TechnologyService,
                Serving,
                Realization,
                Assignment,
                Composition,
                Aggregation,
                Access,
                Association,
                Specialization,
            }
        ),
    ),
    "Business Process Cooperation": (
        PurposeCategory.DESIGNING,
        ContentCategory.COHERENCE,
        frozenset(
            {
                BusinessProcess,
                BusinessFunction,
                BusinessInteraction,
                BusinessEvent,
                BusinessService,
                BusinessActor,
                BusinessRole,
                BusinessCollaboration,
                BusinessInterface,
                BusinessObject,
                Representation,
                Location,
                Flow,
                Triggering,
                Serving,
                Composition,
                Aggregation,
                Assignment,
                Association,
                Specialization,
                Realization,
            }
        ),
    ),
    "Application Cooperation": (
        PurposeCategory.DESIGNING,
        ContentCategory.COHERENCE,
        frozenset(
            {
                ApplicationComponent,
                ApplicationCollaboration,
                ApplicationInterface,
                ApplicationFunction,
                ApplicationInteraction,
                ApplicationProcess,
                ApplicationEvent,
                ApplicationService,
                DataObject,
                Location,
                Serving,
                Flow,
                Triggering,
                Realization,
                Access,
                Composition,
                Aggregation,
                Assignment,
                Association,
                Specialization,
            }
        ),
    ),
    "Service Realization": (
        PurposeCategory.DESIGNING,
        ContentCategory.COHERENCE,
        frozenset(
            {
                BusinessService,
                BusinessProcess,
                BusinessFunction,
                BusinessInteraction,
                BusinessEvent,
                BusinessActor,
                BusinessRole,
                BusinessCollaboration,
                ApplicationService,
                ApplicationComponent,
                ApplicationFunction,
                ApplicationInteraction,
                ApplicationProcess,
                ApplicationEvent,
                TechnologyService,
                TechnologyFunction,
                TechnologyProcess,
                TechnologyInteraction,
                Realization,
                Serving,
                Assignment,
                Composition,
                Aggregation,
                Triggering,
                Flow,
                Association,
                Specialization,
            }
        ),
    ),
    "Implementation and Deployment": (
        PurposeCategory.DESIGNING,
        ContentCategory.COHERENCE,
        frozenset(
            {
                ApplicationComponent,
                ApplicationCollaboration,
                ApplicationInterface,
                ApplicationService,
                DataObject,
                Artifact,
                Node,
                Device,
                SystemSoftware,
                TechnologyCollaboration,
                TechnologyInterface,
                Path,
                CommunicationNetwork,
                TechnologyService,
                Assignment,
                Realization,
                Composition,
                Aggregation,
                Association,
                Serving,
                Specialization,
            }
        ),
    ),
    "Goal Realization": (
        PurposeCategory.DECIDING,
        ContentCategory.COHERENCE,
        frozenset(
            {
                Goal,
                Outcome,
                Requirement,
                Constraint,
                Principle,
                Driver,
                Assessment,
                Stakeholder,
                Realization,
                Influence,
                Association,
                Composition,
                Aggregation,
                Specialization,
            }
        ),
    ),
    "Goal Contribution": (
        PurposeCategory.DECIDING,
        ContentCategory.DETAILS,
        frozenset(
            {
                Goal,
                Outcome,
                Requirement,
                Constraint,
                Principle,
                Influence,
                Association,
                Composition,
                Aggregation,
                Specialization,
            }
        ),
    ),
    "Principles": (
        PurposeCategory.DECIDING,
        ContentCategory.DETAILS,
        frozenset(
            {
                Principle,
                Requirement,
                Constraint,
                Goal,
                Outcome,
                Driver,
                Assessment,
                Stakeholder,
                Realization,
                Influence,
                Association,
                Composition,
                Aggregation,
                Specialization,
            }
        ),
    ),
    "Requirements Realization": (
        PurposeCategory.DECIDING,
        ContentCategory.COHERENCE,
        frozenset(
            {
                Requirement,
                Constraint,
                Goal,
                Outcome,
                Principle,
                BusinessProcess,
                BusinessFunction,
                BusinessService,
                BusinessActor,
                BusinessRole,
                ApplicationComponent,
                ApplicationService,
                Node,
                TechnologyService,
                WorkPackage,
                Deliverable,
                Realization,
                Association,
                Composition,
                Aggregation,
                Influence,
                Specialization,
            }
        ),
    ),
    "Motivation": (
        PurposeCategory.DECIDING,
        ContentCategory.OVERVIEW,
        frozenset(
            {
                Stakeholder,
                Driver,
                Assessment,
                Goal,
                Outcome,
                Principle,
                Requirement,
                Constraint,
                Meaning,
                Value,
                Composition,
                Aggregation,
                Influence,
                Realization,
                Association,
                Specialization,
            }
        ),
    ),
    "Strategy": (
        PurposeCategory.DESIGNING,
        ContentCategory.OVERVIEW,
        frozenset(
            {
                Resource,
                Capability,
                ValueStream,
                CourseOfAction,
                Composition,
                Aggregation,
                Assignment,
                Realization,
                Serving,
                Flow,
                Triggering,
                Access,
                Influence,
                Association,
                Specialization,
            }
        ),
    ),
    "Capability Map": (
        PurposeCategory.DESIGNING,
        ContentCategory.OVERVIEW,
        frozenset(
            {
                Capability,
                Resource,
                Assignment,
                Serving,
                Composition,
                Aggregation,
                Specialization,
                Association,
                Realization,
            }
        ),
    ),
    "Outcome Realization": (
        PurposeCategory.DECIDING,
        ContentCategory.COHERENCE,
        frozenset(
            {
                Capability,
                CourseOfAction,
                Resource,
                ValueStream,
                Outcome,
                Goal,
                Realization,
                Influence,
                Composition,
                Aggregation,
                Association,
                Specialization,
            }
        ),
    ),
    "Resource Map": (
        PurposeCategory.DESIGNING,
        ContentCategory.OVERVIEW,
        frozenset(
            {
                Resource,
                Capability,
                Assignment,
                Composition,
                Aggregation,
                Specialization,
                Association,
                Serving,
            }
        ),
    ),
    "Value Stream": (
        PurposeCategory.DESIGNING,
        ContentCategory.DETAILS,
        frozenset(
            {
                ValueStream,
                Capability,
                Resource,
                CourseOfAction,
                Flow,
                Triggering,
                Serving,
                Composition,
                Aggregation,
                Association,
                Specialization,
            }
        ),
    ),
    "Project": (
        PurposeCategory.DESIGNING,
        ContentCategory.DETAILS,
        frozenset(
            {
                WorkPackage,
                Deliverable,
                ImplementationEvent,
                BusinessActor,
                BusinessRole,
                Location,
                Assignment,
                Realization,
                Triggering,
                Flow,
                Composition,
                Aggregation,
                Association,
                Specialization,
            }
        ),
    ),
    "Migration": (
        PurposeCategory.DESIGNING,
        ContentCategory.COHERENCE,
        frozenset(
            {
                Plateau,
                Gap,
                WorkPackage,
                Composition,
                Aggregation,
                Triggering,
                Association,
                Realization,
                Specialization,
            }
        ),
    ),
    "Implementation and Migration": (
        PurposeCategory.DESIGNING,
        ContentCategory.OVERVIEW,
        frozenset(
            {
                WorkPackage,
                Deliverable,
                ImplementationEvent,
                Plateau,
                Gap,
                Location,
                Composition,
                Aggregation,
                Assignment,
                Realization,
                Serving,
                Triggering,
                Flow,
                Association,
                Specialization,
            }
        ),
    ),
    "Stakeholder": (
        PurposeCategory.INFORMING,
        ContentCategory.OVERVIEW,
        frozenset(
            {
                Stakeholder,
                Driver,
                Assessment,
                Goal,
                Outcome,
                Principle,
                Requirement,
                Constraint,
                Influence,
                Association,
                Composition,
                Aggregation,
                Specialization,
            }
        ),
    ),
}

ALL_VIEWPOINT_KEYS = list(VIEWPOINT_EXPECTED.keys())

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
# Parametrized: full permitted_concept_types set equality per viewpoint
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "vp_name,expected", [(name, data[2]) for name, data in VIEWPOINT_EXPECTED.items()]
)
def test_viewpoint_permitted_types(vp_name: str, expected: frozenset) -> None:
    """Assert exact permitted_concept_types set for each viewpoint."""
    vp = VIEWPOINT_CATALOGUE[vp_name]
    assert vp.permitted_concept_types == expected, (
        f"Viewpoint '{vp_name}': permitted_concept_types mismatch.\n"
        f"  Extra in actual:   {vp.permitted_concept_types - expected}\n"
        f"  Missing in actual: {expected - vp.permitted_concept_types}"
    )


# ---------------------------------------------------------------------------
# Parametrized: structural properties per viewpoint
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("vp_name", ALL_VIEWPOINT_KEYS)
def test_viewpoint_name(vp_name: str) -> None:
    vp = VIEWPOINT_CATALOGUE[vp_name]
    assert vp.name == vp_name


@pytest.mark.parametrize(
    "vp_name,expected", [(name, data[0]) for name, data in VIEWPOINT_EXPECTED.items()]
)
def test_viewpoint_purpose(vp_name: str, expected: PurposeCategory) -> None:
    vp = VIEWPOINT_CATALOGUE[vp_name]
    assert vp.purpose is expected


@pytest.mark.parametrize(
    "vp_name,expected", [(name, data[1]) for name, data in VIEWPOINT_EXPECTED.items()]
)
def test_viewpoint_content(vp_name: str, expected: ContentCategory) -> None:
    vp = VIEWPOINT_CATALOGUE[vp_name]
    assert vp.content is expected


@pytest.mark.parametrize("vp_name", ALL_VIEWPOINT_KEYS)
def test_all_types_are_concept_subclasses(vp_name: str) -> None:
    vp = VIEWPOINT_CATALOGUE[vp_name]
    for t in vp.permitted_concept_types:
        assert issubclass(t, Concept), (
            f"Type {t!r} in '{vp_name}' permitted_concept_types is not a Concept subclass"
        )


@pytest.mark.parametrize("vp_name", ALL_VIEWPOINT_KEYS)
def test_caching_identity(vp_name: str) -> None:
    """Accessing the same key twice returns the identical object."""
    first = VIEWPOINT_CATALOGUE[vp_name]
    second = VIEWPOINT_CATALOGUE[vp_name]
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
