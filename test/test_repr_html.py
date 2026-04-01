"""Tests for _repr_html_() on ModelDiff, ImpactResult, GapResult, and MergeResult.

GitHub Issue #29: Notebook-friendly HTML rendering for result dataclasses.
"""

from __future__ import annotations

import re

import pytest

from etcion.comparison import ConceptChange, FieldChange, ModelDiff
from etcion.impact import ImpactedConcept, ImpactResult, Violation  # noqa: F401
from etcion.merge import MergeResult
from etcion.metamodel.business import BusinessActor, BusinessRole  # noqa: F401
from etcion.metamodel.model import Model
from etcion.metamodel.relationships import Association
from etcion.patterns import GapResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _count_open_close(html: str, tag: str) -> tuple[int, int]:
    """Return (open_count, close_count) for a given HTML tag name."""
    open_count = len(re.findall(rf"<{tag}[\s>]", html, re.IGNORECASE))
    close_count = len(re.findall(rf"</{tag}>", html, re.IGNORECASE))
    return open_count, close_count


def _tags_balanced(html: str) -> bool:
    """Check that common paired HTML tags are balanced."""
    for tag in ("div", "table", "tr", "th", "td", "ul", "li"):
        opens, closes = _count_open_close(html, tag)
        if opens != closes:
            return False
    return True


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def actor_alice() -> BusinessActor:
    return BusinessActor(id="actor-alice-1", name="Alice")


@pytest.fixture()
def actor_bob() -> BusinessActor:
    return BusinessActor(id="actor-bob-2", name="Bob")


@pytest.fixture()
def role_manager() -> BusinessRole:
    return BusinessRole(id="role-mgr-3", name="Manager")


@pytest.fixture()
def assoc(actor_alice: BusinessActor, actor_bob: BusinessActor) -> Association:
    return Association(id="rel-1", source=actor_alice, target=actor_bob)


# ---------------------------------------------------------------------------
# TestModelDiffHtml
# ---------------------------------------------------------------------------


class TestModelDiffHtml:
    def _make_diff(
        self,
        added: tuple = (),
        removed: tuple = (),
        modified: tuple = (),
    ) -> ModelDiff:
        return ModelDiff(added=added, removed=removed, modified=modified)

    def test_returns_string(self, actor_alice: BusinessActor) -> None:
        diff = self._make_diff(added=(actor_alice,))
        html = diff._repr_html_()
        assert isinstance(html, str)

    def test_contains_added_element_name(self, actor_alice: BusinessActor) -> None:
        diff = self._make_diff(added=(actor_alice,))
        html = diff._repr_html_()
        assert "Alice" in html

    def test_contains_removed_element_name(self, actor_bob: BusinessActor) -> None:
        diff = self._make_diff(removed=(actor_bob,))
        html = diff._repr_html_()
        assert "Bob" in html

    def test_contains_modified_field(self, actor_alice: BusinessActor) -> None:
        change = ConceptChange(
            concept_id=actor_alice.id,
            concept_type="BusinessActor",
            changes={"name": FieldChange(field="name", old="Alice", new="Alicia")},
        )
        diff = self._make_diff(modified=(change,))
        html = diff._repr_html_()
        assert "name" in html

    def test_green_style_for_added(self, actor_alice: BusinessActor) -> None:
        diff = self._make_diff(added=(actor_alice,))
        html = diff._repr_html_()
        assert "green" in html.lower() or "#d4edda" in html

    def test_red_style_for_removed(self, actor_bob: BusinessActor) -> None:
        diff = self._make_diff(removed=(actor_bob,))
        html = diff._repr_html_()
        assert "red" in html.lower() or "#f8d7da" in html

    def test_empty_diff_clean_message(self) -> None:
        diff = self._make_diff()
        html = diff._repr_html_()
        assert "No changes" in html

    def test_valid_html_no_unclosed_tags(
        self, actor_alice: BusinessActor, actor_bob: BusinessActor
    ) -> None:
        change = ConceptChange(
            concept_id="actor-alice-1",
            concept_type="BusinessActor",
            changes={"name": FieldChange(field="name", old="Alice", new="Alicia")},
        )
        diff = self._make_diff(added=(actor_alice,), removed=(actor_bob,), modified=(change,))
        html = diff._repr_html_()
        assert _tags_balanced(html)


# ---------------------------------------------------------------------------
# TestImpactResultHtml
# ---------------------------------------------------------------------------


class TestImpactResultHtml:
    def test_returns_string(self, actor_alice: BusinessActor) -> None:
        ic = ImpactedConcept(concept=actor_alice, depth=1)
        result = ImpactResult(affected=(ic,))
        html = result._repr_html_()
        assert isinstance(html, str)

    def test_contains_affected_element(self, actor_alice: BusinessActor) -> None:
        ic = ImpactedConcept(concept=actor_alice, depth=1)
        result = ImpactResult(affected=(ic,))
        html = result._repr_html_()
        assert "Alice" in html

    def test_contains_depth(self, actor_alice: BusinessActor) -> None:
        ic = ImpactedConcept(concept=actor_alice, depth=3)
        result = ImpactResult(affected=(ic,))
        html = result._repr_html_()
        assert "3" in html

    def test_contains_broken_relationship(
        self, actor_alice: BusinessActor, actor_bob: BusinessActor
    ) -> None:
        assoc = Association(
            id="rel-broken-1", name="broken-assoc", source=actor_alice, target=actor_bob
        )
        result = ImpactResult(broken_relationships=(assoc,))
        html = result._repr_html_()
        # The relationship ID or type should appear
        assert "Association" in html or "rel-broken-1" in html

    def test_empty_result_clean_message(self) -> None:
        result = ImpactResult()
        html = result._repr_html_()
        assert "No impact" in html


# ---------------------------------------------------------------------------
# TestGapResultHtml
# ---------------------------------------------------------------------------


class TestGapResultHtml:
    def test_returns_string(self, actor_alice: BusinessActor) -> None:
        gap = GapResult(element=actor_alice, missing=["No Serving edge to ApplicationService"])
        html = gap._repr_html_()
        assert isinstance(html, str)

    def test_contains_element_name(self, actor_alice: BusinessActor) -> None:
        gap = GapResult(element=actor_alice, missing=["No Serving edge to ApplicationService"])
        html = gap._repr_html_()
        assert "Alice" in html

    def test_contains_missing_description(self, actor_alice: BusinessActor) -> None:
        gap = GapResult(
            element=actor_alice,
            missing=[
                "No Serving edge to ApplicationService",
                "Missing Realization from TechService",
            ],
        )
        html = gap._repr_html_()
        assert "No Serving edge to ApplicationService" in html
        assert "Missing Realization from TechService" in html


# ---------------------------------------------------------------------------
# TestMergeResultHtml
# ---------------------------------------------------------------------------


class TestMergeResultHtml:
    def _make_empty_model(self) -> Model:
        return Model()

    def test_returns_string(self) -> None:
        result = MergeResult(merged_model=self._make_empty_model())
        html = result._repr_html_()
        assert isinstance(html, str)

    def test_contains_conflict_info(self, actor_alice: BusinessActor) -> None:
        change = ConceptChange(
            concept_id=actor_alice.id,
            concept_type="BusinessActor",
            changes={"name": FieldChange(field="name", old="Alice", new="Alicia")},
        )
        result = MergeResult(
            merged_model=self._make_empty_model(),
            conflicts=(change,),
        )
        html = result._repr_html_()
        # Conflict concept ID or field should appear
        assert actor_alice.id in html or "name" in html

    def test_empty_merge_clean_message(self) -> None:
        result = MergeResult(merged_model=self._make_empty_model())
        html = result._repr_html_()
        assert "Clean merge" in html
