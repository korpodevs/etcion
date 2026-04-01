"""Tests for the built-in IngestionMetadata provenance profile and query helpers.

Reference: GitHub Issues #25, #26.
"""

from __future__ import annotations

import pytest

from etcion.metamodel.concepts import Element
from etcion.metamodel.model import Model
from etcion.metamodel.profiles import Profile
from etcion.provenance import (
    INGESTION_PROFILE,
    elements_by_source,
    low_confidence_elements,
    unreviewed_elements,
)

# ---------------------------------------------------------------------------
# Concrete Element stub for tests that need a real element instance.
# ---------------------------------------------------------------------------


class _StubElement(Element):
    @property
    def _type_name(self) -> str:
        return "StubElement"


# ===========================================================================
# INGESTION_PROFILE object structure
# ===========================================================================


class TestIngestionProfile:
    """Verify structural properties of the built-in INGESTION_PROFILE."""

    def test_is_valid_profile(self) -> None:
        """INGESTION_PROFILE must be a Profile instance."""
        assert isinstance(INGESTION_PROFILE, Profile)

    def test_profile_name(self) -> None:
        """Profile name must be 'IngestionMetadata'."""
        assert INGESTION_PROFILE.name == "IngestionMetadata"

    def test_declares_four_attributes(self) -> None:
        """attribute_extensions must declare exactly four attributes for Element."""
        assert Element in INGESTION_PROFILE.attribute_extensions
        attrs = INGESTION_PROFILE.attribute_extensions[Element]
        assert len(attrs) == 4

    def test_attribute_types(self) -> None:
        """Each provenance attribute must map to the correct Python type."""
        attrs = INGESTION_PROFILE.attribute_extensions[Element]
        assert attrs["_provenance_source"] is str
        assert attrs["_provenance_confidence"] is float
        assert attrs["_provenance_reviewed"] is bool
        assert attrs["_provenance_timestamp"] is str


# ===========================================================================
# Profile application and validation on a Model
# ===========================================================================


class TestProvenanceOnModel:
    """Verify INGESTION_PROFILE integrates correctly with Model."""

    def test_apply_profile_succeeds(self) -> None:
        """model.apply_profile(INGESTION_PROFILE) must not raise."""
        model = Model()
        model.apply_profile(INGESTION_PROFILE)
        assert INGESTION_PROFILE in model.profiles

    def test_set_provenance_attributes(self) -> None:
        """An element's extended_attributes can hold all four provenance keys."""
        elem = _StubElement(
            name="Source System",
            extended_attributes={
                "_provenance_source": "etl-pipeline-v1",
                "_provenance_confidence": 0.95,
                "_provenance_reviewed": False,
                "_provenance_timestamp": "2026-03-31T00:00:00Z",
            },
        )
        assert elem.extended_attributes["_provenance_source"] == "etl-pipeline-v1"
        assert elem.extended_attributes["_provenance_confidence"] == 0.95
        assert elem.extended_attributes["_provenance_reviewed"] is False
        assert elem.extended_attributes["_provenance_timestamp"] == "2026-03-31T00:00:00Z"

    def test_validate_with_profile_accepts(self) -> None:
        """Model with profile applied and correct provenance attrs must produce no errors."""
        model = Model()
        model.apply_profile(INGESTION_PROFILE)
        elem = _StubElement(
            name="Source System",
            extended_attributes={
                "_provenance_source": "etl-pipeline-v1",
                "_provenance_confidence": 0.85,
                "_provenance_reviewed": True,
                "_provenance_timestamp": "2026-03-31T00:00:00Z",
            },
        )
        model.add(elem)
        errors = model.validate()
        assert errors == []

    def test_validate_without_profile_rejects(self) -> None:
        """Model without profile applied but with provenance attrs must produce errors.

        model.validate() checks extended_attributes against applied profiles.
        Without INGESTION_PROFILE applied, any provenance key is undeclared.
        """
        model = Model()
        elem = _StubElement(
            name="Source System",
            extended_attributes={
                "_provenance_source": "etl-pipeline-v1",
            },
        )
        model.add(elem)
        errors = model.validate()
        assert len(errors) == 1
        assert "_provenance_source" in str(errors[0])

    def test_validate_wrong_type_rejected(self) -> None:
        """Profile type-check: passing an int for a str attribute must produce an error."""
        model = Model()
        model.apply_profile(INGESTION_PROFILE)
        elem = _StubElement(
            name="Source System",
            extended_attributes={
                "_provenance_confidence": "not-a-float",  # wrong type
            },
        )
        model.add(elem)
        errors = model.validate()
        assert len(errors) == 1
        assert "_provenance_confidence" in str(errors[0])

    def test_ingestion_profile_exported_from_package(self) -> None:
        """INGESTION_PROFILE must be importable directly from the etcion package."""
        import etcion

        assert hasattr(etcion, "INGESTION_PROFILE")
        assert etcion.INGESTION_PROFILE is INGESTION_PROFILE


# ===========================================================================
# Shared fixture factory for query-helper tests (Issue #26)
# ===========================================================================


def _make_model() -> tuple[Model, dict[str, _StubElement]]:
    """Return a Model and a labelled dict of elements with varied provenance states.

    Elements
    --------
    reviewed      -- has all four provenance attrs; _provenance_reviewed=True
    unreviewed    -- has all four provenance attrs; _provenance_reviewed=False
    missing_flag  -- has _provenance_source but NO _provenance_reviewed key
    no_provenance -- empty extended_attributes (not provenance-tracked)
    high_conf     -- _provenance_confidence=0.9, _provenance_reviewed=False
    low_conf      -- _provenance_confidence=0.3, _provenance_reviewed=False
    cmdb_source   -- _provenance_source="cmdb"
    gpt4o_source  -- _provenance_source="gpt4o"
    """
    model = Model()
    model.apply_profile(INGESTION_PROFILE)

    elements: dict[str, _StubElement] = {}

    elements["reviewed"] = _StubElement(
        name="Reviewed",
        extended_attributes={
            "_provenance_source": "cmdb",
            "_provenance_confidence": 0.9,
            "_provenance_reviewed": True,
            "_provenance_timestamp": "2026-01-01T00:00:00Z",
        },
    )
    elements["unreviewed"] = _StubElement(
        name="Unreviewed",
        extended_attributes={
            "_provenance_source": "cmdb",
            "_provenance_confidence": 0.8,
            "_provenance_reviewed": False,
            "_provenance_timestamp": "2026-01-01T00:00:00Z",
        },
    )
    elements["missing_flag"] = _StubElement(
        name="MissingFlag",
        extended_attributes={
            "_provenance_source": "cmdb",
            "_provenance_timestamp": "2026-01-01T00:00:00Z",
        },
    )
    elements["no_provenance"] = _StubElement(
        name="NoProvenance",
        extended_attributes={},
    )
    elements["high_conf"] = _StubElement(
        name="HighConf",
        extended_attributes={
            "_provenance_source": "gpt4o",
            "_provenance_confidence": 0.9,
            "_provenance_reviewed": False,
        },
    )
    elements["low_conf"] = _StubElement(
        name="LowConf",
        extended_attributes={
            "_provenance_source": "gpt4o",
            "_provenance_confidence": 0.3,
            "_provenance_reviewed": False,
        },
    )
    elements["cmdb_source"] = _StubElement(
        name="CmdbSource",
        extended_attributes={
            "_provenance_source": "cmdb",
            "_provenance_confidence": 0.7,
            "_provenance_reviewed": True,
        },
    )
    elements["gpt4o_source"] = _StubElement(
        name="Gpt4oSource",
        extended_attributes={
            "_provenance_source": "gpt4o",
            "_provenance_confidence": 0.6,
            "_provenance_reviewed": False,
        },
    )

    for elem in elements.values():
        model.add(elem)

    return model, elements


# ===========================================================================
# TestUnreviewedElements (Issue #26)
# ===========================================================================


class TestUnreviewedElements:
    """Verify unreviewed_elements() filters correctly on _provenance_reviewed."""

    def test_returns_unreviewed(self) -> None:
        """Elements with _provenance_reviewed=False must be returned."""
        model, elems = _make_model()
        result = unreviewed_elements(model)
        assert elems["unreviewed"] in result

    def test_includes_missing_reviewed(self) -> None:
        """Elements with provenance attrs but no _provenance_reviewed key are unreviewed."""
        model, elems = _make_model()
        result = unreviewed_elements(model)
        assert elems["missing_flag"] in result

    def test_excludes_reviewed(self) -> None:
        """Elements with _provenance_reviewed=True must NOT be returned."""
        model, elems = _make_model()
        result = unreviewed_elements(model)
        assert elems["reviewed"] not in result

    def test_skips_non_provenance_elements(self) -> None:
        """Elements with empty extended_attributes (no provenance attrs) are skipped."""
        model, elems = _make_model()
        result = unreviewed_elements(model)
        assert elems["no_provenance"] not in result

    def test_exported_from_package(self) -> None:
        """unreviewed_elements must be importable directly from the etcion package."""
        import etcion

        assert hasattr(etcion, "unreviewed_elements")
        assert etcion.unreviewed_elements is unreviewed_elements


# ===========================================================================
# TestElementsBySource (Issue #26)
# ===========================================================================


class TestElementsBySource:
    """Verify elements_by_source() filters by _provenance_source value."""

    def test_returns_matching_source(self) -> None:
        """Elements whose _provenance_source matches the query are returned."""
        model, elems = _make_model()
        result = elements_by_source(model, "cmdb")
        assert elems["cmdb_source"] in result
        assert elems["unreviewed"] in result
        assert elems["reviewed"] in result
        assert elems["missing_flag"] in result

    def test_excludes_different_source(self) -> None:
        """Elements with a different _provenance_source are excluded."""
        model, elems = _make_model()
        result = elements_by_source(model, "cmdb")
        assert elems["gpt4o_source"] not in result
        assert elems["high_conf"] not in result
        assert elems["low_conf"] not in result

    def test_skips_no_provenance(self) -> None:
        """Elements with empty extended_attributes are skipped regardless of query."""
        model, elems = _make_model()
        result = elements_by_source(model, "cmdb")
        assert elems["no_provenance"] not in result

    def test_exported_from_package(self) -> None:
        """elements_by_source must be importable directly from the etcion package."""
        import etcion

        assert hasattr(etcion, "elements_by_source")
        assert etcion.elements_by_source is elements_by_source


# ===========================================================================
# TestLowConfidenceElements (Issue #26)
# ===========================================================================


class TestLowConfidenceElements:
    """Verify low_confidence_elements() filters by _provenance_confidence threshold."""

    def test_returns_below_threshold(self) -> None:
        """Elements with confidence strictly below the threshold are returned."""
        model, elems = _make_model()
        result = low_confidence_elements(model, threshold=0.7)
        assert elems["low_conf"] in result
        assert elems["gpt4o_source"] in result

    def test_excludes_above_threshold(self) -> None:
        """Elements with confidence >= threshold are excluded."""
        model, elems = _make_model()
        result = low_confidence_elements(model, threshold=0.7)
        assert elems["reviewed"] not in result
        assert elems["high_conf"] not in result

    def test_default_threshold(self) -> None:
        """Default threshold is 0.5 -- only elements below 0.5 are returned."""
        model, elems = _make_model()
        result = low_confidence_elements(model)
        assert elems["low_conf"] in result
        # gpt4o_source has confidence=0.6, which is >= 0.5 default
        assert elems["gpt4o_source"] not in result

    def test_skips_no_provenance(self) -> None:
        """Elements with empty extended_attributes are skipped."""
        model, elems = _make_model()
        result = low_confidence_elements(model, threshold=1.0)
        assert elems["no_provenance"] not in result

    def test_skips_missing_confidence_key(self) -> None:
        """Elements with provenance attrs but no _provenance_confidence key are skipped."""
        model, elems = _make_model()
        # missing_flag has no _provenance_confidence
        result = low_confidence_elements(model, threshold=1.0)
        assert elems["missing_flag"] not in result

    def test_exported_from_package(self) -> None:
        """low_confidence_elements must be importable directly from the etcion package."""
        import etcion

        assert hasattr(etcion, "low_confidence_elements")
        assert etcion.low_confidence_elements is low_confidence_elements
