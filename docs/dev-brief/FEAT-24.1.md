# Technical Brief: FEAT-24.1 -- Structural Diff Engine

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-037-epic024-model-comparison-diff.md`
**Target file:** `src/pyarchi/comparison.py`
**Test file:** `test/test_feat241_diff_engine.py`

---

## Data Model

| Class | Base | Frozen | Fields |
|-------|------|--------|--------|
| `FieldChange` | `dataclass` | Yes | `field: str`, `old: Any`, `new: Any` |
| `ConceptChange` | `dataclass` | Yes | `concept_id: str`, `concept_type: str`, `changes: dict[str, FieldChange]` |
| `ModelDiff` | `dataclass` | Yes | `added: tuple[Concept, ...]`, `removed: tuple[Concept, ...]`, `modified: tuple[ConceptChange, ...]` |

## Function Signature

```python
def diff_models(
    model_a: Model,
    model_b: Model,
    *,
    match_by: Literal["id", "type_name"] = "id",
) -> ModelDiff:
```

- `model_a` = baseline ("before"), `model_b` = revised ("after").
- `match_by="id"`: key is `concept.id`.
- `match_by="type_name"`: key is `(type(concept).__name__, concept.name)`.

## Algorithm

1. Build `dict[key, Concept]` for both models from `model.concepts`.
2. `added` = concepts in `model_b` whose key is absent from `model_a`.
3. `removed` = concepts in `model_a` whose key is absent from `model_b`.
4. For each shared key:
   - `model_dump()` both concepts.
   - Remove `"id"` from both dicts (id is the match key, not a diffable field).
   - For `Relationship` instances: normalize `"source"` and `"target"` values to their `"id"` string (i.e. `dump["source"] = concept.source.id`).
   - Compare remaining fields. Each difference becomes a `FieldChange`.
   - If any `FieldChange` exists, emit a `ConceptChange`.
5. Return `ModelDiff(added=tuple(...), removed=tuple(...), modified=tuple(...))`.

Complexity: O(n + m).

---

## Implementation

```python
"""Model comparison and diff utilities (EPIC-024, FEAT-24.1 / FEAT-24.2)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pyarchi.metamodel.concepts import Concept, Relationship
from pyarchi.metamodel.model import Model

__all__: list[str] = [
    "FieldChange",
    "ConceptChange",
    "ModelDiff",
    "diff_models",
]


@dataclass(frozen=True)
class FieldChange:
    """A single field-level change between two concept snapshots."""

    field: str
    old: Any
    new: Any


@dataclass(frozen=True)
class ConceptChange:
    """A concept present in both models whose fields differ."""

    concept_id: str
    concept_type: str
    changes: dict[str, FieldChange]


@dataclass(frozen=True)
class ModelDiff:
    """Immutable result of comparing two models."""

    added: tuple[Concept, ...]
    removed: tuple[Concept, ...]
    modified: tuple[ConceptChange, ...]


def _build_key(concept: Concept, match_by: Literal["id", "type_name"]) -> str | tuple[str, str]:
    """Return the lookup key for a concept."""
    if match_by == "id":
        return concept.id
    # match_by == "type_name"
    name = getattr(concept, "name", "") or ""
    return (type(concept).__name__, name)


def _normalize_dump(concept: Concept) -> dict[str, Any]:
    """Return a model_dump() dict with id removed and source/target normalized."""
    d = concept.model_dump()
    d.pop("id", None)
    if isinstance(concept, Relationship):
        d["source"] = concept.source.id
        d["target"] = concept.target.id
    return d


def _diff_fields(dump_a: dict[str, Any], dump_b: dict[str, Any]) -> dict[str, FieldChange]:
    """Compare two normalized dumps, returning changed fields."""
    changes: dict[str, FieldChange] = {}
    all_keys = dump_a.keys() | dump_b.keys()
    for key in all_keys:
        old = dump_a.get(key)
        new = dump_b.get(key)
        if old != new:
            changes[key] = FieldChange(field=key, old=old, new=new)
    return changes


def diff_models(
    model_a: Model,
    model_b: Model,
    *,
    match_by: Literal["id", "type_name"] = "id",
) -> ModelDiff:
    """Compare two models and return a structured diff.

    :param model_a: Baseline ("before") model.
    :param model_b: Revised ("after") model.
    :param match_by: ``"id"`` matches concepts by id; ``"type_name"`` matches
        by ``(type_name, name)`` tuple.
    :returns: A frozen :class:`ModelDiff`.
    """
    lookup_a = {_build_key(c, match_by): c for c in model_a.concepts}
    lookup_b = {_build_key(c, match_by): c for c in model_b.concepts}

    keys_a = set(lookup_a)
    keys_b = set(lookup_b)

    added = tuple(lookup_b[k] for k in keys_b - keys_a)
    removed = tuple(lookup_a[k] for k in keys_a - keys_b)

    modified: list[ConceptChange] = []
    for key in keys_a & keys_b:
        ca, cb = lookup_a[key], lookup_b[key]
        dump_a = _normalize_dump(ca)
        dump_b = _normalize_dump(cb)
        changes = _diff_fields(dump_a, dump_b)
        if changes:
            modified.append(
                ConceptChange(
                    concept_id=ca.id,
                    concept_type=type(ca).__name__,
                    changes=changes,
                )
            )

    return ModelDiff(added=added, removed=removed, modified=tuple(modified))
```

---

## Test File

```python
"""Tests for FEAT-24.1: Structural Diff Engine."""

from __future__ import annotations

import pytest

from pyarchi.comparison import ConceptChange, FieldChange, ModelDiff, diff_models
from pyarchi.metamodel.business import BusinessActor, BusinessRole
from pyarchi.metamodel.model import Model
from pyarchi.metamodel.relationships import Association


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def actor_alice() -> BusinessActor:
    return BusinessActor(id="actor-1", name="Alice")


@pytest.fixture()
def actor_bob() -> BusinessActor:
    return BusinessActor(id="actor-2", name="Bob")


# ---------------------------------------------------------------------------
# Dataclass basics
# ---------------------------------------------------------------------------

class TestDataclassesAreFrozen:
    def test_field_change_frozen(self) -> None:
        fc = FieldChange(field="name", old="a", new="b")
        with pytest.raises(AttributeError):
            fc.field = "x"  # type: ignore[misc]

    def test_concept_change_frozen(self) -> None:
        cc = ConceptChange(concept_id="1", concept_type="BusinessActor", changes={})
        with pytest.raises(AttributeError):
            cc.concept_id = "2"  # type: ignore[misc]

    def test_model_diff_frozen(self) -> None:
        md = ModelDiff(added=(), removed=(), modified=())
        with pytest.raises(AttributeError):
            md.added = ()  # type: ignore[misc]


# ---------------------------------------------------------------------------
# diff_models -- match_by="id" (default)
# ---------------------------------------------------------------------------

class TestDiffById:
    def test_identical_models_empty_diff(self, actor_alice: BusinessActor) -> None:
        m1 = Model(concepts=[actor_alice])
        m2 = Model(concepts=[actor_alice])
        diff = diff_models(m1, m2)
        assert diff.added == ()
        assert diff.removed == ()
        assert diff.modified == ()

    def test_added_element(self, actor_alice: BusinessActor, actor_bob: BusinessActor) -> None:
        m1 = Model(concepts=[actor_alice])
        m2 = Model(concepts=[actor_alice, actor_bob])
        diff = diff_models(m1, m2)
        assert len(diff.added) == 1
        assert diff.added[0].id == "actor-2"
        assert diff.removed == ()
        assert diff.modified == ()

    def test_removed_element(self, actor_alice: BusinessActor, actor_bob: BusinessActor) -> None:
        m1 = Model(concepts=[actor_alice, actor_bob])
        m2 = Model(concepts=[actor_alice])
        diff = diff_models(m1, m2)
        assert diff.added == ()
        assert len(diff.removed) == 1
        assert diff.removed[0].id == "actor-2"

    def test_modified_element_name_change(self) -> None:
        a = BusinessActor(id="a1", name="Alice")
        b = BusinessActor(id="a1", name="Alicia")
        m1 = Model(concepts=[a])
        m2 = Model(concepts=[b])
        diff = diff_models(m1, m2)
        assert diff.added == ()
        assert diff.removed == ()
        assert len(diff.modified) == 1
        change = diff.modified[0]
        assert change.concept_id == "a1"
        assert change.concept_type == "BusinessActor"
        assert "name" in change.changes
        assert change.changes["name"].old == "Alice"
        assert change.changes["name"].new == "Alicia"

    def test_modified_element_description_change(self) -> None:
        a = BusinessActor(id="a1", name="X", description="old")
        b = BusinessActor(id="a1", name="X", description="new")
        m1 = Model(concepts=[a])
        m2 = Model(concepts=[b])
        diff = diff_models(m1, m2)
        assert len(diff.modified) == 1
        assert diff.modified[0].changes["description"].old == "old"
        assert diff.modified[0].changes["description"].new == "new"

    def test_relationship_source_retarget(self) -> None:
        a1 = BusinessActor(id="a1", name="A1")
        a2 = BusinessActor(id="a2", name="A2")
        a3 = BusinessActor(id="a3", name="A3")
        r_before = Association(id="r1", name="link", source=a1, target=a2)
        r_after = Association(id="r1", name="link", source=a1, target=a3)
        m1 = Model(concepts=[a1, a2, a3, r_before])
        m2 = Model(concepts=[a1, a2, a3, r_after])
        diff = diff_models(m1, m2)
        assert len(diff.modified) == 1
        assert "target" in diff.modified[0].changes
        assert diff.modified[0].changes["target"].old == "a2"
        assert diff.modified[0].changes["target"].new == "a3"

    def test_empty_models(self) -> None:
        diff = diff_models(Model(), Model())
        assert diff.added == ()
        assert diff.removed == ()
        assert diff.modified == ()


# ---------------------------------------------------------------------------
# diff_models -- match_by="type_name"
# ---------------------------------------------------------------------------

class TestDiffByTypeName:
    def test_match_by_type_name_same_name(self) -> None:
        a = BusinessActor(id="id-aaa", name="Alice")
        b = BusinessActor(id="id-bbb", name="Alice")
        m1 = Model(concepts=[a])
        m2 = Model(concepts=[b])
        diff = diff_models(m1, m2, match_by="type_name")
        # Same type+name -> matched, not added/removed
        assert diff.added == ()
        assert diff.removed == ()

    def test_match_by_type_name_different_names(self) -> None:
        a = BusinessActor(id="id-aaa", name="Alice")
        b = BusinessActor(id="id-bbb", name="Bob")
        m1 = Model(concepts=[a])
        m2 = Model(concepts=[b])
        diff = diff_models(m1, m2, match_by="type_name")
        assert len(diff.added) == 1
        assert len(diff.removed) == 1

    def test_match_by_type_name_detects_description_change(self) -> None:
        a = BusinessActor(id="x", name="Alice", description="v1")
        b = BusinessActor(id="y", name="Alice", description="v2")
        m1 = Model(concepts=[a])
        m2 = Model(concepts=[b])
        diff = diff_models(m1, m2, match_by="type_name")
        assert len(diff.modified) == 1
        assert "description" in diff.modified[0].changes


# ---------------------------------------------------------------------------
# Mixed elements and relationships
# ---------------------------------------------------------------------------

class TestMixedConcepts:
    def test_added_relationship_detected(self) -> None:
        a1 = BusinessActor(id="a1", name="A1")
        a2 = BusinessActor(id="a2", name="A2")
        r = Association(id="r1", name="link", source=a1, target=a2)
        m1 = Model(concepts=[a1, a2])
        m2 = Model(concepts=[a1, a2, r])
        diff = diff_models(m1, m2)
        assert len(diff.added) == 1
        assert diff.added[0].id == "r1"
```

---

## Acceptance Criteria

| # | Criterion |
|---|-----------|
| 1 | `FieldChange`, `ConceptChange`, `ModelDiff` are frozen dataclasses |
| 2 | `diff_models()` with default `match_by="id"` detects added, removed, modified concepts |
| 3 | `diff_models()` with `match_by="type_name"` matches by `(type_name, name)` |
| 4 | Relationship `source`/`target` compared by id string, not nested dict |
| 5 | All tests in `test/test_feat241_diff_engine.py` pass |
