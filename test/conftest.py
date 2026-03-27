"""Shared pytest fixtures for the etcion test suite."""

from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture()
def empty_model() -> dict[str, Any]:
    """Return a minimal model container with no elements or relationships.

    Will be updated to return a `Model` instance once EPIC-002 (FEAT-02.6)
    implements the Model container class.
    """
    return {"elements": [], "relationships": []}


@pytest.fixture()
def sample_element() -> dict[str, Any]:
    """Return a sample element with default attributes.

    Will be updated to return a concrete `Element` subclass instance once
    EPIC-002 implements the element hierarchy.
    """
    return {
        "id": "id-placeholder-element-001",
        "name": "Sample Element",
        "description": None,
        "documentation_url": None,
    }
