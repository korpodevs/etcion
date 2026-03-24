"""Tests for FEAT-03.5 -- Nesting Rendering Hint.

STORY-03.5.1 has no production code changes.  The is_nested field is an
EPIC-005 contract documented in ADR-015.

STORY-03.5.2 adds extra="forbid" to Concept.model_config.  The
TestExtraForbidOnConcept class tests this change directly using test-local
concrete stubs.  These tests are NOT xfail -- they pass immediately once
the production code change is applied.

STORY-03.5.3 and STORY-03.5.4 test the is_nested field on concrete
relationship types that do not yet exist (Composition, Triggering).
These are marked xfail until EPIC-005 ships.
"""

from __future__ import annotations

from typing import ClassVar

import pytest
from pydantic import ValidationError

from pyarchi.enums import RelationshipCategory
from pyarchi.metamodel.concepts import (
    Concept,
    Element,
    Relationship,
    RelationshipConnector,
)

# ---------------------------------------------------------------------------
# Test-local helpers: minimal concrete subclasses for testing extra="forbid"
# ---------------------------------------------------------------------------


class _StubElement(Element):
    """Minimal concrete Element for testing extra field rejection."""

    @property
    def _type_name(self) -> str:
        return "StubElement"


class _StubRelationship(Relationship):
    """Minimal concrete Relationship for testing extra field rejection."""

    category: ClassVar[RelationshipCategory] = RelationshipCategory.OTHER

    @property
    def _type_name(self) -> str:
        return "StubRelationship"


class _StubConnector(RelationshipConnector):
    """Minimal concrete RelationshipConnector for testing extra field rejection."""

    @property
    def _type_name(self) -> str:
        return "StubConnector"


# ---------------------------------------------------------------------------
# TestExtraForbidOnConcept -- immediately passing tests for STORY-03.5.2
# ---------------------------------------------------------------------------


class TestExtraForbidOnConcept:
    """Verify that extra="forbid" on Concept rejects unknown kwargs on all
    branches of the hierarchy.

    These tests validate STORY-03.5.2: the extra="forbid" change to
    Concept.model_config.  They are NOT xfail -- they must pass once the
    production code change is applied.
    """

    def test_element_rejects_unknown_kwarg(self) -> None:
        """Passing an unknown kwarg to a concrete Element raises ValidationError."""
        with pytest.raises(ValidationError):
            _StubElement(name="test", bogus_field=True)  # type: ignore[call-arg]

    def test_relationship_rejects_unknown_kwarg(self) -> None:
        """Passing an unknown kwarg to a concrete Relationship raises ValidationError."""
        source = _StubElement(name="src")
        target = _StubElement(name="tgt")
        with pytest.raises(ValidationError):
            _StubRelationship(
                name="test",
                source=source,
                target=target,
                bogus_field=True,  # type: ignore[call-arg]
            )

    def test_connector_rejects_unknown_kwarg(self) -> None:
        """Passing an unknown kwarg to a concrete RelationshipConnector raises ValidationError."""
        with pytest.raises(ValidationError):
            _StubConnector(bogus_field=True)  # type: ignore[call-arg]

    def test_element_rejects_is_nested_kwarg(self) -> None:
        """is_nested is not a field on Element; extra="forbid" rejects it."""
        with pytest.raises(ValidationError):
            _StubElement(name="test", is_nested=True)  # type: ignore[call-arg]

    def test_relationship_rejects_is_nested_kwarg(self) -> None:
        """is_nested is not a field on base Relationship; extra="forbid" rejects it.

        Once StructuralRelationship exists (EPIC-005), is_nested will be
        accepted on structural subclasses but still rejected on non-structural.
        """
        source = _StubElement(name="src")
        target = _StubElement(name="tgt")
        with pytest.raises(ValidationError):
            _StubRelationship(
                name="test",
                source=source,
                target=target,
                is_nested=True,  # type: ignore[call-arg]
            )

    def test_extra_forbid_in_concept_model_config(self) -> None:
        """Confirm extra="forbid" is set in Concept.model_config."""
        assert Concept.model_config.get("extra") == "forbid"


# ---------------------------------------------------------------------------
# TestIsNestedOnStructuralRelationship -- xfail until EPIC-005
# ---------------------------------------------------------------------------


class TestIsNestedOnStructuralRelationship:
    """Test that is_nested=True on Composition does not raise.

    Requires Composition class from EPIC-005 (FEAT-05.2).
    """

    def test_composition_accepts_is_nested_true(self) -> None:
        """Composition(is_nested=True) must not raise ValidationError."""
        from pyarchi import Composition

        source = _StubElement(name="whole")
        target = _StubElement(name="part")
        comp = Composition(name="nesting", source=source, target=target, is_nested=True)
        assert comp.is_nested is True

    def test_composition_is_nested_defaults_false(self) -> None:
        """Composition() without is_nested must default to False."""
        from pyarchi import Composition

        source = _StubElement(name="whole")
        target = _StubElement(name="part")
        comp = Composition(name="default", source=source, target=target)
        assert comp.is_nested is False


# ---------------------------------------------------------------------------
# TestIsNestedRejectedOnNonStructural -- xfail until EPIC-005
# ---------------------------------------------------------------------------


class TestIsNestedRejectedOnNonStructural:
    """Test that is_nested=True on Triggering raises ValidationError.

    Requires Triggering class from EPIC-005 (FEAT-05.7).
    """

    def test_triggering_rejects_is_nested(self) -> None:
        """Triggering(is_nested=True) must raise ValidationError."""
        from pyarchi import Triggering

        source = _StubElement(name="src")
        target = _StubElement(name="tgt")
        with pytest.raises(ValidationError):
            Triggering(
                name="bad",
                source=source,
                target=target,
                is_nested=True,
            )
