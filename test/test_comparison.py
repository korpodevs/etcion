"""Merged tests: test_feat241_diff_engine, test_feat242_diff_serialization."""

from __future__ import annotations

import json

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
