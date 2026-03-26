"""Tests for FEAT-23.2 -- Relationship traversal methods on Model."""

from __future__ import annotations

import pytest

from pyarchi.metamodel.application import ApplicationComponent, ApplicationService
from pyarchi.metamodel.business import (
    BusinessActor,
    BusinessRole,
    BusinessService,
)
from pyarchi.metamodel.model import Model
from pyarchi.metamodel.relationships import Assignment, Serving


@pytest.fixture
def populated_model() -> Model:
    """Build a small model:

    actor --Assignment--> role
    role  --Assignment--> service
    component --Serving--> app_service
    component --Serving--> service
    """
    actor = BusinessActor(name="Alice")
    role = BusinessRole(name="Manager")
    service = BusinessService(name="HR Service")
    component = ApplicationComponent(name="CRM")
    app_service = ApplicationService(name="CRM API")

    a1 = Assignment(source=actor, target=role, name="a1")
    a2 = Assignment(source=role, target=service, name="a2")
    s1 = Serving(source=component, target=app_service, name="s1")
    s2 = Serving(source=component, target=service, name="s2")

    m = Model()
    for c in [actor, role, service, component, app_service, a1, a2, s1, s2]:
        m.add(c)
    return m


def _by_name(model: Model, name: str):
    """Helper to find an element by name."""
    return next(e for e in model.elements if e.name == name)


# -- connected_to -------------------------------------------------------------


class TestConnectedTo:
    def test_returns_relationships_for_source(self, populated_model: Model) -> None:
        component = _by_name(populated_model, "CRM")
        result = populated_model.connected_to(component)
        assert len(result) == 2
        assert all(isinstance(r, Serving) for r in result)

    def test_returns_relationships_for_target(self, populated_model: Model) -> None:
        role = _by_name(populated_model, "Manager")
        result = populated_model.connected_to(role)
        # role is target of a1, source of a2
        assert len(result) == 2

    def test_returns_relationships_for_both_directions(self, populated_model: Model) -> None:
        service = _by_name(populated_model, "HR Service")
        result = populated_model.connected_to(service)
        # service is target of a2 and s2
        assert len(result) == 2

    def test_isolated_element(self) -> None:
        m = Model()
        actor = BusinessActor(name="Lonely")
        m.add(actor)
        assert m.connected_to(actor) == []

    def test_identity_not_equality(self, populated_model: Model) -> None:
        """A different object with the same name should not match."""
        impostor = BusinessActor(name="Alice")
        assert populated_model.connected_to(impostor) == []

    def test_returns_list(self, populated_model: Model) -> None:
        actor = _by_name(populated_model, "Alice")
        assert isinstance(populated_model.connected_to(actor), list)


# -- sources_of ---------------------------------------------------------------


class TestSourcesOf:
    def test_single_source(self, populated_model: Model) -> None:
        role = _by_name(populated_model, "Manager")
        result = populated_model.sources_of(role)
        assert len(result) == 1
        assert result[0].name == "Alice"

    def test_multiple_sources(self, populated_model: Model) -> None:
        service = _by_name(populated_model, "HR Service")
        result = populated_model.sources_of(service)
        names = {c.name for c in result}
        assert names == {"Manager", "CRM"}

    def test_no_sources(self, populated_model: Model) -> None:
        actor = _by_name(populated_model, "Alice")
        assert populated_model.sources_of(actor) == []

    def test_returns_concepts_not_relationships(self, populated_model: Model) -> None:
        role = _by_name(populated_model, "Manager")
        result = populated_model.sources_of(role)
        from pyarchi.metamodel.concepts import Concept, Relationship

        assert all(isinstance(c, Concept) for c in result)
        assert not any(isinstance(c, Relationship) for c in result)


# -- targets_of ---------------------------------------------------------------


class TestTargetsOf:
    def test_single_target(self, populated_model: Model) -> None:
        actor = _by_name(populated_model, "Alice")
        result = populated_model.targets_of(actor)
        assert len(result) == 1
        assert result[0].name == "Manager"

    def test_multiple_targets(self, populated_model: Model) -> None:
        component = _by_name(populated_model, "CRM")
        result = populated_model.targets_of(component)
        names = {c.name for c in result}
        assert names == {"CRM API", "HR Service"}

    def test_no_targets(self, populated_model: Model) -> None:
        api = _by_name(populated_model, "CRM API")
        assert populated_model.targets_of(api) == []

    def test_composition_with_of_type(self, populated_model: Model) -> None:
        """STORY-23.2.5 equivalent: targets_of(actor) filtered by type."""
        actor = _by_name(populated_model, "Alice")
        targets = populated_model.targets_of(actor)
        roles = [t for t in targets if isinstance(t, BusinessRole)]
        assert len(roles) == 1
        assert roles[0].name == "Manager"


# -- empty model edge case ----------------------------------------------------


class TestEmptyModel:
    def test_connected_to_empty(self) -> None:
        m = Model()
        actor = BusinessActor(name="Ghost")
        assert m.connected_to(actor) == []

    def test_sources_of_empty(self) -> None:
        m = Model()
        actor = BusinessActor(name="Ghost")
        assert m.sources_of(actor) == []

    def test_targets_of_empty(self) -> None:
        m = Model()
        actor = BusinessActor(name="Ghost")
        assert m.targets_of(actor) == []
