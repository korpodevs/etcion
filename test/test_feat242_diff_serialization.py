"""Tests for FEAT-24.2: Diff Serialization and Display."""

from __future__ import annotations

import json

import pytest

from pyarchi.comparison import ConceptChange, FieldChange, ModelDiff, diff_models
from pyarchi.metamodel.business import BusinessActor, BusinessRole
from pyarchi.metamodel.model import Model
from pyarchi.metamodel.relationships import Association

# ---------------------------------------------------------------------------
# to_dict()
# ---------------------------------------------------------------------------


class TestToDict:
    def test_empty_diff_to_dict(self) -> None:
        diff = ModelDiff(added=(), removed=(), modified=())
        d = diff.to_dict()
        assert d == {"added": [], "removed": [], "modified": []}

    def test_added_entry_structure(self) -> None:
        actor = BusinessActor(id="a1", name="Alice")
        diff = ModelDiff(added=(actor,), removed=(), modified=())
        d = diff.to_dict()
        assert len(d["added"]) == 1
        entry = d["added"][0]
        assert entry["id"] == "a1"
        assert entry["type"] == "BusinessActor"
        assert entry["name"] == "Alice"

    def test_removed_entry_structure(self) -> None:
        actor = BusinessActor(id="a1", name="Bob")
        diff = ModelDiff(added=(), removed=(actor,), modified=())
        d = diff.to_dict()
        assert len(d["removed"]) == 1
        assert d["removed"][0]["id"] == "a1"
        assert d["removed"][0]["name"] == "Bob"

    def test_modified_entry_structure(self) -> None:
        cc = ConceptChange(
            concept_id="a1",
            concept_type="BusinessActor",
            changes={"name": FieldChange(field="name", old="Alice", new="Alicia")},
        )
        diff = ModelDiff(added=(), removed=(), modified=(cc,))
        d = diff.to_dict()
        assert len(d["modified"]) == 1
        mod = d["modified"][0]
        assert mod["concept_id"] == "a1"
        assert mod["concept_type"] == "BusinessActor"
        assert mod["changes"]["name"] == {"old": "Alice", "new": "Alicia"}

    def test_to_dict_is_json_serializable(self) -> None:
        a = BusinessActor(id="a1", name="Alice")
        b = BusinessActor(id="a1", name="Alicia")
        m1 = Model(concepts=[a])
        m2 = Model(concepts=[b])
        diff = diff_models(m1, m2)
        # Must not raise
        result = json.dumps(diff.to_dict())
        assert isinstance(result, str)

    def test_to_dict_round_trip_keys(self) -> None:
        a1 = BusinessActor(id="a1", name="A")
        a2 = BusinessActor(id="a2", name="B")
        a1_v2 = BusinessActor(id="a1", name="A-renamed")
        a3 = BusinessActor(id="a3", name="C")
        m1 = Model(concepts=[a1, a2])
        m2 = Model(concepts=[a1_v2, a3])
        diff = diff_models(m1, m2)
        d = diff.to_dict()
        assert set(d.keys()) == {"added", "removed", "modified"}
        assert len(d["added"]) == 1  # a3
        assert len(d["removed"]) == 1  # a2
        assert len(d["modified"]) == 1  # a1 renamed


# ---------------------------------------------------------------------------
# summary()
# ---------------------------------------------------------------------------


class TestSummary:
    def test_empty_summary(self) -> None:
        diff = ModelDiff(added=(), removed=(), modified=())
        assert diff.summary() == "ModelDiff: 0 added, 0 removed, 0 modified"

    def test_summary_with_counts(self) -> None:
        a = BusinessActor(id="a1", name="A")
        b = BusinessActor(id="a2", name="B")
        cc = ConceptChange(concept_id="x", concept_type="T", changes={})
        diff = ModelDiff(added=(a,), removed=(b,), modified=(cc, cc, cc))
        assert diff.summary() == "ModelDiff: 1 added, 1 removed, 3 modified"

    def test_summary_includes_counts_from_real_diff(self) -> None:
        a1 = BusinessActor(id="a1", name="A")
        a2 = BusinessActor(id="a2", name="B")
        m1 = Model(concepts=[a1])
        m2 = Model(concepts=[a2])
        diff = diff_models(m1, m2)
        s = diff.summary()
        assert "1 added" in s
        assert "1 removed" in s
        assert "0 modified" in s


# ---------------------------------------------------------------------------
# __str__
# ---------------------------------------------------------------------------


class TestStr:
    def test_str_delegates_to_summary(self) -> None:
        diff = ModelDiff(added=(), removed=(), modified=())
        assert str(diff) == diff.summary()


# ---------------------------------------------------------------------------
# __bool__
# ---------------------------------------------------------------------------


class TestBool:
    def test_empty_diff_is_falsy(self) -> None:
        diff = ModelDiff(added=(), removed=(), modified=())
        assert not diff
        assert bool(diff) is False

    def test_diff_with_added_is_truthy(self) -> None:
        a = BusinessActor(id="a1", name="A")
        diff = ModelDiff(added=(a,), removed=(), modified=())
        assert diff
        assert bool(diff) is True

    def test_diff_with_removed_is_truthy(self) -> None:
        a = BusinessActor(id="a1", name="A")
        diff = ModelDiff(added=(), removed=(a,), modified=())
        assert diff

    def test_diff_with_modified_is_truthy(self) -> None:
        cc = ConceptChange(concept_id="x", concept_type="T", changes={})
        diff = ModelDiff(added=(), removed=(), modified=(cc,))
        assert diff


# ---------------------------------------------------------------------------
# Exports from pyarchi.__init__
# ---------------------------------------------------------------------------


class TestExports:
    def test_field_change_importable(self) -> None:
        from pyarchi import FieldChange as FC

        assert FC is FieldChange

    def test_concept_change_importable(self) -> None:
        from pyarchi import ConceptChange as CC

        assert CC is ConceptChange

    def test_model_diff_importable(self) -> None:
        from pyarchi import ModelDiff as MD

        assert MD is ModelDiff

    def test_diff_models_importable(self) -> None:
        from pyarchi import diff_models as dm

        assert dm is diff_models
