# Technical Brief: FEAT-23.3 -- Relationship Query + Integration
**Status:** Ready for TDD
**ADR Link:** `docs/adr/ADR-036-epic023-model-querying.md`

## Story Disposition

| Story | Status | Maps To |
|---|---|---|
| STORY-23.3.1 (`relationships()` switch) | **Rejected** (ADR D6) | `Model.relationships_of_type()` replaces it |
| STORY-23.3.2 (`of_category`) | **Rejected** (ADR D6) | Trivial: `[r for r in model.relationships_of_type(X) if r.category == cat]` |
| STORY-23.3.3 (`between`) | **Rejected** (ADR D6) | Trivial: comprehension over `relationships_of_type` |
| STORY-23.3.4 (test: rel of_type) | Accepted | See test file below |
| STORY-23.3.5 (test: between) | Modified | Composition test via comprehension |

## Method Signature

Single method added to `Model` in `src/pyarchi/metamodel/model.py`.

```python
def relationships_of_type(self, cls: type[Relationship]) -> list[Relationship]:
    """Return relationships that are instances of *cls* (includes subclasses)."""
    return [r for r in self.relationships if isinstance(r, cls)]
```

## Integration Test Scope

This feature's test file also serves as the EPIC-023 integration test, exercising all 8 methods together in realistic scenarios.

## Test File

`test/test_feat233_relationship_query.py`

```python
"""Tests for FEAT-23.3 -- Relationship query + EPIC-023 integration."""
from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer, RelationshipCategory
from pyarchi.metamodel.business import (
    BusinessActor,
    BusinessObject,
    BusinessRole,
    BusinessService,
)
from pyarchi.metamodel.application import (
    ApplicationComponent,
    ApplicationService,
)
from pyarchi.metamodel.concepts import Relationship
from pyarchi.metamodel.model import Model
from pyarchi.metamodel.relationships import (
    Assignment,
    Serving,
    StructuralRelationship,
)


@pytest.fixture
def full_model() -> Model:
    """A model with mixed elements and relationships.

    Elements:
        actor, role, biz_service, biz_obj (Business layer)
        component, app_service (Application layer)

    Relationships:
        actor --Assignment--> role
        role  --Assignment--> biz_service
        component --Serving--> app_service
        component --Serving--> biz_service
    """
    actor = BusinessActor(name="Alice")
    role = BusinessRole(name="Manager")
    biz_service = BusinessService(name="HR Service")
    biz_obj = BusinessObject(name="Policy Doc")
    component = ApplicationComponent(name="CRM")
    app_service = ApplicationService(name="CRM API")

    a1 = Assignment(source=actor, target=role, name="assign-1")
    a2 = Assignment(source=role, target=biz_service, name="assign-2")
    s1 = Serving(source=component, target=app_service, name="serve-1")
    s2 = Serving(source=component, target=biz_service, name="serve-2")

    m = Model()
    for c in [actor, role, biz_service, biz_obj, component, app_service,
              a1, a2, s1, s2]:
        m.add(c)
    return m


def _elem(model: Model, name: str):
    return next(e for e in model.elements if e.name == name)


# -- relationships_of_type ----------------------------------------------------

class TestRelationshipsOfType:
    def test_serving_only(self, full_model: Model) -> None:
        result = full_model.relationships_of_type(Serving)
        assert len(result) == 2
        assert all(isinstance(r, Serving) for r in result)

    def test_assignment_only(self, full_model: Model) -> None:
        result = full_model.relationships_of_type(Assignment)
        assert len(result) == 2

    def test_superclass_includes_subclasses(self, full_model: Model) -> None:
        result = full_model.relationships_of_type(StructuralRelationship)
        # Assignment is a StructuralRelationship
        assert len(result) == 2
        assert all(isinstance(r, Assignment) for r in result)

    def test_base_relationship_returns_all(self, full_model: Model) -> None:
        result = full_model.relationships_of_type(Relationship)
        assert len(result) == 4

    def test_no_matches(self, full_model: Model) -> None:
        from pyarchi.metamodel.relationships import Composition
        assert full_model.relationships_of_type(Composition) == []

    def test_returns_list(self, full_model: Model) -> None:
        assert isinstance(full_model.relationships_of_type(Serving), list)


# -- rejected story compositions (STORY-23.3.2, 23.3.3) -----------------------

class TestCompositionPatterns:
    def test_filter_by_category(self, full_model: Model) -> None:
        """STORY-23.3.2 equivalent via comprehension."""
        structural = [
            r for r in full_model.relationships
            if r.category == RelationshipCategory.STRUCTURAL
        ]
        assert len(structural) == 2  # both Assignments

    def test_between_types(self, full_model: Model) -> None:
        """STORY-23.3.3 equivalent: Serving rels from AppComponent to AppService."""
        result = [
            r for r in full_model.relationships_of_type(Serving)
            if isinstance(r.source, ApplicationComponent)
            and isinstance(r.target, ApplicationService)
        ]
        assert len(result) == 1
        assert result[0].name == "serve-1"


# -- EPIC-023 integration tests -----------------------------------------------

class TestIntegration:
    """End-to-end tests composing multiple EPIC-023 methods."""

    def test_find_actors_serving_a_service(self, full_model: Model) -> None:
        """Who ultimately serves HR Service?  Traverse sources_of."""
        service = _elem(full_model, "HR Service")
        sources = full_model.sources_of(service)
        names = {c.name for c in sources}
        # role (via Assignment) and component (via Serving)
        assert names == {"Manager", "CRM"}

    def test_elements_of_type_then_targets(self, full_model: Model) -> None:
        """For each BusinessActor, find their targets."""
        actors = full_model.elements_of_type(BusinessActor)
        assert len(actors) == 1
        targets = full_model.targets_of(actors[0])
        assert len(targets) == 1
        assert targets[0].name == "Manager"

    def test_layer_filter_plus_connected(self, full_model: Model) -> None:
        """Find all Application-layer elements and their relationships."""
        app_elems = full_model.elements_by_layer(Layer.APPLICATION)
        all_rels = []
        for elem in app_elems:
            all_rels.extend(full_model.connected_to(elem))
        # Deduplicate (component appears in s1 and s2; app_service in s1)
        unique_rels = list({id(r): r for r in all_rels}.values())
        assert len(unique_rels) == 3  # s1, s2, and s1 again from app_service side

    def test_name_search_then_traverse(self, full_model: Model) -> None:
        """Find elements by name, then traverse."""
        crm_elems = full_model.elements_by_name("CRM")
        assert len(crm_elems) == 2  # CRM and CRM API
        component = next(e for e in crm_elems if e.name == "CRM")
        targets = full_model.targets_of(component)
        assert len(targets) == 2

    def test_aspect_filter(self, full_model: Model) -> None:
        """Passive structure elements in business layer."""
        passive = full_model.elements_by_aspect(Aspect.PASSIVE_STRUCTURE)
        biz_passive = [e for e in passive if getattr(type(e), 'layer', None) is Layer.BUSINESS]
        assert len(biz_passive) == 1
        assert biz_passive[0].name == "Policy Doc"

    def test_all_eight_methods_exist(self, full_model: Model) -> None:
        """Smoke test: all 8 ADR-036 methods are callable."""
        assert callable(full_model.elements_of_type)
        assert callable(full_model.elements_by_layer)
        assert callable(full_model.elements_by_aspect)
        assert callable(full_model.elements_by_name)
        assert callable(full_model.relationships_of_type)
        assert callable(full_model.connected_to)
        assert callable(full_model.sources_of)
        assert callable(full_model.targets_of)
```
