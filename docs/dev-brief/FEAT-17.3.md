# Technical Brief: FEAT-17.3 -- View Class

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-029-epic017-viewpoint-mechanism.md`
**Spec:** ArchiMate 3.2, Section 13
**Depends on:** FEAT-17.2 (Viewpoint)

## Scope

| Artifact | Location |
|---|---|
| `View` | `src/pyarchi/metamodel/viewpoints.py` |

## Class Structure

```python
from pydantic import BaseModel, ConfigDict

class View(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    governing_viewpoint: Viewpoint
    underlying_model: Model
    concepts: list[Concept] = []

    def add(self, concept: Concept) -> None:
        # Type gate
        if not any(issubclass(type(concept), t) for t in self.governing_viewpoint.permitted_concept_types):
            raise ValidationError(...)
        # Membership gate
        if concept.id not in self.underlying_model._concepts:
            raise ValidationError(...)
        self.concepts.append(concept)
```

NOT frozen -- `concepts` is mutated via `add()`. NOT a `Concept` subclass.

## Fields

| Field | Type | Required | Default | Mutable |
|---|---|---|---|---|
| `governing_viewpoint` | `Viewpoint` | Yes | -- | No |
| `underlying_model` | `Model` | Yes | -- | No |
| `concepts` | `list[Concept]` | No | `[]` | Yes (via `add()`) |

## Validation Rules

| Gate | Condition | Error |
|---|---|---|
| Type gate | `not any(issubclass(type(concept), t) for t in vp.permitted_concept_types)` | `pyarchi.exceptions.ValidationError` |
| Membership gate | `concept.id not in underlying_model._concepts` | `pyarchi.exceptions.ValidationError` |

Both checks are eager (on `add()`), not deferred. Error type is `pyarchi.exceptions.ValidationError`, NOT `pydantic.ValidationError`.

## Test File: `test/test_feat173_view.py`

```python
from __future__ import annotations

import pytest

from pyarchi.enums import ContentCategory, PurposeCategory
from pyarchi.exceptions import ValidationError
from pyarchi.metamodel.application import ApplicationComponent, ApplicationService
from pyarchi.metamodel.business import BusinessActor, BusinessProcess
from pyarchi.metamodel.concepts import Concept
from pyarchi.metamodel.model import Model
from pyarchi.metamodel.relationships import Serving
from pyarchi.metamodel.viewpoints import View, Viewpoint


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
    def test_add_permitted_type(
        self, model_with_actors: Model, actor_viewpoint: Viewpoint
    ) -> None:
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
    def test_not_a_concept(
        self, model_with_actors: Model, actor_viewpoint: Viewpoint
    ) -> None:
        view = View(
            governing_viewpoint=actor_viewpoint,
            underlying_model=model_with_actors,
        )
        assert not isinstance(view, Concept)


class TestViewErrorType:
    def test_raises_pyarchi_validation_error_not_pydantic(
        self, actor_viewpoint: Viewpoint
    ) -> None:
        """Confirm View.add() raises pyarchi.exceptions.ValidationError."""
        import pydantic

        m = Model()
        orphan = BusinessActor(name="X")
        view = View(governing_viewpoint=actor_viewpoint, underlying_model=m)
        with pytest.raises(ValidationError) as exc_info:
            view.add(orphan)
        assert not isinstance(exc_info.value, pydantic.ValidationError)
```
