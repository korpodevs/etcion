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
