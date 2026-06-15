"""Structural-sharing editing API on Model (ADR-051).

``with_added`` / ``with_replaced`` / ``with_removed`` return new immutable
models that share unchanged concept instances with the source model.
"""

from __future__ import annotations

import pytest

from etcion.metamodel.business import BusinessActor, BusinessProcess
from etcion.metamodel.model import Model
from etcion.metamodel.relationships import Assignment


def _model() -> tuple[Model, BusinessActor, BusinessProcess, Assignment]:
    a = BusinessActor(id="a1", name="A")
    b = BusinessProcess(id="b1", name="B")
    rel = Assignment(id="rel-ab", name="AB", source=a, target=b)
    return Model(concepts=[a, b, rel]), a, b, rel


class TestWithReplaced:
    def test_returns_new_model_with_edited_concept(self) -> None:
        model, a, _b, _rel = _model()
        renamed = a.model_copy(update={"name": "A2"})

        edited = model.with_replaced(renamed)

        assert edited is not model
        assert edited["a1"].name == "A2"

    def test_original_is_unchanged(self) -> None:
        model, a, _b, _rel = _model()
        model.with_replaced(a.model_copy(update={"name": "A2"}))
        assert model["a1"].name == "A"

    def test_untouched_concepts_are_shared(self) -> None:
        model, a, b, rel = _model()
        edited = model.with_replaced(a.model_copy(update={"name": "A2"}))
        # b and rel are shared by reference; only a1 differs.
        assert edited["b1"] is b
        assert edited["rel-ab"] is rel

    def test_relationship_resolves_to_new_instance_without_relink(self) -> None:
        model, a, _b, _rel = _model()
        renamed = a.model_copy(update={"name": "A2"})
        edited = model.with_replaced(renamed)
        # The relationship still references "a1" by ID; it now resolves to the
        # edited instance with no re-linking.
        rel = edited["rel-ab"]
        assert edited[rel.source_id] is renamed

    def test_missing_id_raises(self) -> None:
        model, _a, _b, _rel = _model()
        ghost = BusinessActor(id="nope", name="X")
        with pytest.raises(KeyError):
            model.with_replaced(ghost)

    def test_non_concept_raises(self) -> None:
        model, _a, _b, _rel = _model()
        with pytest.raises(TypeError):
            model.with_replaced("not a concept")  # type: ignore[arg-type]


class TestWithAdded:
    def test_adds_concept(self) -> None:
        model, _a, _b, _rel = _model()
        c = BusinessActor(id="c1", name="C")
        edited = model.with_added(c)
        assert edited["c1"] is c
        assert "c1" not in model._concepts

    def test_shares_existing_concepts(self) -> None:
        model, a, _b, _rel = _model()
        edited = model.with_added(BusinessActor(id="c1", name="C"))
        assert edited["a1"] is a

    def test_duplicate_id_raises(self) -> None:
        model, _a, _b, _rel = _model()
        with pytest.raises(ValueError, match="Duplicate"):
            model.with_added(BusinessActor(id="a1", name="dup"))


class TestWithRemoved:
    def test_removes_concept_and_dangling_relationships(self) -> None:
        model, a, _b, _rel = _model()
        edited = model.with_removed(a)
        ids = {c.id for c in edited}
        assert "a1" not in ids
        assert "rel-ab" not in ids  # dangling (source removed) -> dropped
        assert "b1" in ids

    def test_accepts_id_string(self) -> None:
        model, _a, _b, _rel = _model()
        edited = model.with_removed("a1")
        assert "a1" not in {c.id for c in edited}

    def test_original_unchanged(self) -> None:
        model, _a, _b, _rel = _model()
        model.with_removed("a1")
        assert "a1" in model._concepts
        assert "rel-ab" in model._concepts

    def test_keeps_unrelated_relationships(self) -> None:
        a = BusinessActor(id="a1", name="A")
        b = BusinessProcess(id="b1", name="B")
        c = BusinessProcess(id="c1", name="C")
        rel_bc = Assignment(id="rel-bc", name="BC", source=b, target=c)
        model = Model(concepts=[a, b, c, rel_bc])

        edited = model.with_removed("a1")
        assert edited["rel-bc"] is rel_bc  # untouched relationship shared

    def test_missing_id_raises(self) -> None:
        model, _a, _b, _rel = _model()
        with pytest.raises(KeyError):
            model.with_removed("nope")


def test_edited_model_recomputes_graph_against_new_registry() -> None:
    pytest.importorskip("networkx")
    model, a, _b, _rel = _model()
    edited = model.with_removed(a)
    # The edited model's graph must reflect the removal, not inherit a stale cache.
    g = edited.to_networkx()
    assert "a1" not in g.nodes
