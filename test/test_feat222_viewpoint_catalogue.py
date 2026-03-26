"""Tests for FEAT-22.2: Viewpoint Catalogue integration.

Covers STORY-22.2.1 through STORY-22.2.4.

Note: Parametric structural coverage of all 28 entries (key existence, name,
purpose, content, permitted_concept_types, Concept subclass, caching identity)
is already provided in test_feat221_viewpoint_catalogue.py::TestAllViewpoints.
This file adds the top-level import surface (STORY-22.2.2), immutability and
unknown-key guards on the real catalogue (STORY-22.2.1 / STORY-22.2.3), frozen
Viewpoint mutation resistance, and View integration (STORY-22.2.4).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from pyarchi import VIEWPOINT_CATALOGUE
from pyarchi.metamodel.viewpoints import Viewpoint

# ---------------------------------------------------------------------------
# STORY-22.2.1 / STORY-22.2.3: Catalogue contract on the real singleton
# ---------------------------------------------------------------------------


def test_catalogue_length_is_28() -> None:
    """The catalogue must contain exactly 28 viewpoints (XSD token count)."""
    assert len(VIEWPOINT_CATALOGUE) == 28


def test_catalogue_is_not_mutable() -> None:
    """ViewpointCatalogue is a Mapping, not a MutableMapping.

    It must not expose __setitem__ or __delitem__.
    """
    assert not hasattr(VIEWPOINT_CATALOGUE, "__setitem__")
    assert not hasattr(VIEWPOINT_CATALOGUE, "__delitem__")


def test_unknown_key_raises_key_error() -> None:
    """Accessing a non-existent viewpoint key raises KeyError."""
    with pytest.raises(KeyError):
        VIEWPOINT_CATALOGUE["Nonexistent Viewpoint"]  # noqa: PIE806


# ---------------------------------------------------------------------------
# Caching behaviour (STORY-22.2.1)
# ---------------------------------------------------------------------------


def test_catalogue_caches_viewpoint_instances() -> None:
    """The same key must return the identical object on repeated access."""
    vp1 = VIEWPOINT_CATALOGUE["Organization"]
    vp2 = VIEWPOINT_CATALOGUE["Organization"]
    assert vp1 is vp2


# ---------------------------------------------------------------------------
# Frozen Viewpoint: mutation resistance
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("key", sorted(VIEWPOINT_CATALOGUE.keys()))
def test_viewpoint_is_frozen(key: str) -> None:
    """Every catalogue entry is a frozen Pydantic model — mutation raises."""
    vp = VIEWPOINT_CATALOGUE[key]
    assert isinstance(vp, Viewpoint)
    with pytest.raises(PydanticValidationError):
        vp.name = "mutated"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# STORY-22.2.2: Top-level import surface
# ---------------------------------------------------------------------------


def test_catalogue_importable_from_top_level() -> None:
    """VIEWPOINT_CATALOGUE is importable directly from pyarchi."""
    import pyarchi

    assert hasattr(pyarchi, "VIEWPOINT_CATALOGUE")
    assert pyarchi.VIEWPOINT_CATALOGUE is VIEWPOINT_CATALOGUE


def test_catalogue_in_all() -> None:
    """VIEWPOINT_CATALOGUE is listed in pyarchi.__all__."""
    import pyarchi

    assert "VIEWPOINT_CATALOGUE" in pyarchi.__all__


# ---------------------------------------------------------------------------
# STORY-22.2.4: View integration
# ---------------------------------------------------------------------------


def test_view_accepts_permitted_concept() -> None:
    """A View governed by the Organization viewpoint accepts a BusinessActor."""
    from pyarchi import BusinessActor, Model, View

    model = Model()
    actor = BusinessActor(name="Alice")
    model.add(actor)

    vp = VIEWPOINT_CATALOGUE["Organization"]
    view = View(governing_viewpoint=vp, underlying_model=model)
    view.add(actor)
    assert actor in view.concepts


def test_view_rejects_unpermitted_concept() -> None:
    """A View governed by Organization viewpoint rejects a DataObject."""
    from pyarchi import DataObject, Model, View
    from pyarchi.exceptions import ValidationError

    model = Model()
    obj = DataObject(name="Invoice")
    model.add(obj)

    vp = VIEWPOINT_CATALOGUE["Organization"]
    view = View(governing_viewpoint=vp, underlying_model=model)
    with pytest.raises(ValidationError, match="not permitted"):
        view.add(obj)


def test_view_rejects_concept_not_in_model() -> None:
    """A View rejects a concept that is not in the underlying model.

    This verifies the membership gate in View.add() works with catalogue
    viewpoints, even when the concept type itself would be permitted.
    """
    from pyarchi import BusinessActor, Model, View
    from pyarchi.exceptions import ValidationError

    model = Model()
    orphan = BusinessActor(name="Orphan")
    # Intentionally do NOT add orphan to model.

    vp = VIEWPOINT_CATALOGUE["Organization"]
    view = View(governing_viewpoint=vp, underlying_model=model)
    with pytest.raises(ValidationError):
        view.add(orphan)
