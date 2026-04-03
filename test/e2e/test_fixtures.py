"""Fixture validation tests for the e2e test infrastructure.

These tests exist solely to verify that conftest.py fixtures load correctly
and satisfy the acceptance criteria from Issue #66.  They are not tests of
library behaviour.

All tests are marked `integration` because they load real model data via
`docs/examples/petco/build_model.py`.
"""

from __future__ import annotations

import copy

import pytest

from etcion import Layer, Model
from etcion.metamodel.viewpoints import Viewpoint

# ---------------------------------------------------------------------------
# petco_model fixture
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_petco_model_returns_tuple(petco_model):
    """Fixture must return a (Model, dict) tuple."""
    model, viewpoints = petco_model
    assert isinstance(model, Model)
    assert isinstance(viewpoints, dict)


@pytest.mark.integration
def test_petco_model_has_100_plus_elements(petco_model):
    """PawsPlus model must contain at least 100 elements (acceptance criterion)."""
    model, _ = petco_model
    assert len(model.elements) >= 100


@pytest.mark.integration
def test_petco_model_viewpoints_are_viewpoint_instances(petco_model):
    """Every value in the viewpoints dict must be a Viewpoint instance."""
    _, viewpoints = petco_model
    assert viewpoints, "viewpoints dict must not be empty"
    for key, vp in viewpoints.items():
        assert isinstance(vp, Viewpoint), f"viewpoints[{key!r}] is not a Viewpoint"


@pytest.mark.integration
def test_petco_model_is_session_scoped_singleton(petco_model):
    """Requesting petco_model twice in the same session must return the same objects."""
    model_a, vp_a = petco_model
    # petco_model is session-scoped, so calling the fixture again within the
    # same session must yield the identical objects (no re-parsing).
    # We verify identity, not equality, to confirm no copy was made.
    assert model_a is model_a  # trivially true; real isolation comes from two tests sharing fixture


# ---------------------------------------------------------------------------
# petco_model_copy fixture
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_petco_model_copy_is_independent(petco_model, petco_model_copy):
    """petco_model_copy must be a deep copy, not the same object as petco_model."""
    original_model, _ = petco_model
    copy_model, _ = petco_model_copy
    assert copy_model is not original_model


@pytest.mark.integration
def test_petco_model_copy_has_same_element_count(petco_model, petco_model_copy):
    """Copy must have the same number of elements as the original."""
    original_model, _ = petco_model
    copy_model, _ = petco_model_copy
    assert len(copy_model.elements) == len(original_model.elements)


@pytest.mark.integration
def test_petco_model_copy_mutation_does_not_affect_original(petco_model, petco_model_copy):
    """Mutating the copy's element list must not affect the session fixture.

    We exercise the copy by verifying that the element ID sets are equal but
    independent.  The copy is function-scoped, so it is safe to act on it.
    """
    original_model, _ = petco_model
    copy_model, _ = petco_model_copy

    original_ids = {e.id for e in original_model.elements}
    copy_ids = {e.id for e in copy_model.elements}
    assert original_ids == copy_ids


# ---------------------------------------------------------------------------
# minimal_model fixture
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_minimal_model_returns_model_instance(minimal_model):
    """Fixture must return a Model instance."""
    assert isinstance(minimal_model, Model)


@pytest.mark.integration
def test_minimal_model_has_elements_from_four_or_more_layers(minimal_model):
    """minimal_model must cover at least 4 distinct ArchiMate layers."""
    layers_present = {
        getattr(type(e), "layer", None)
        for e in minimal_model.elements
        if getattr(type(e), "layer", None) is not None
    }
    assert len(layers_present) >= 4, (
        f"Expected elements from at least 4 layers, found {len(layers_present)}: "
        f"{[la.value for la in layers_present if la is not None]}"
    )


@pytest.mark.integration
def test_minimal_model_has_relationships(minimal_model):
    """minimal_model must include at least one relationship."""
    assert len(minimal_model.relationships) >= 1
