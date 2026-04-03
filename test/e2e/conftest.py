"""Shared pytest fixtures for the etcion e2e test suite.

All e2e tests are integration tests and should be marked with
``@pytest.mark.integration``.

Session-scoped fixtures (``petco_model``, ``minimal_model``) are
intentionally read-only.  Tests that need to mutate model state must use
``petco_model_copy`` (function-scoped) instead.
"""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

from etcion import (
    ApplicationComponent,
    Assignment,
    BusinessActor,
    BusinessRole,
    Capability,
    Model,
    Node,
    Realization,
    Requirement,
    Serving,
    SystemSoftware,
    WorkPackage,
)
from etcion.metamodel.viewpoints import Viewpoint

# ---------------------------------------------------------------------------
# Import helper for docs/examples (not on the default pythonpath)
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parent.parent.parent
_BUILD_MODEL_PATH = _REPO_ROOT / "docs" / "examples" / "petco" / "build_model.py"


def _import_build_model() -> Any:
    """Dynamically import docs/examples/petco/build_model.py.

    ``docs/`` is intentionally outside the ``src/`` source tree and is not
    listed in ``pyproject.toml``'s ``pythonpath``.  We use importlib to load
    it without polluting ``sys.path`` for the entire test process.
    """
    spec = importlib.util.spec_from_file_location(
        "petco_build_model",
        _BUILD_MODEL_PATH,
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot locate build_model.py at {_BUILD_MODEL_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


# ---------------------------------------------------------------------------
# petco_model — session-scoped, read-only
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def petco_model() -> tuple[Model, dict[str, Viewpoint]]:
    """Load the PawsPlus Corporation model once per test session.

    Returns a ``(model, viewpoints)`` tuple sourced from
    ``docs/examples/petco/build_model.py``.

    WARNING: Tests MUST NOT mutate this fixture.  Use ``petco_model_copy``
    for any test that needs to modify model state.
    """
    build_model = _import_build_model()
    model, viewpoints = build_model.load_pawsplus_model()
    return model, viewpoints


# ---------------------------------------------------------------------------
# petco_model_copy — function-scoped deep copy
# ---------------------------------------------------------------------------


@pytest.fixture()
def petco_model_copy(
    petco_model: tuple[Model, dict[str, Viewpoint]],
) -> tuple[Model, dict[str, Viewpoint]]:
    """Return a deep copy of the PawsPlus model for tests that need mutation.

    Function-scoped: a fresh copy is created for each test, so mutations do
    not bleed between tests.
    """
    model, viewpoints = petco_model
    return copy.deepcopy(model), copy.deepcopy(viewpoints)


# ---------------------------------------------------------------------------
# minimal_model — session-scoped, covers ≥4 layers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def minimal_model() -> Model:
    """Return a small model with one element per layer plus connecting relationships.

    Covers the Strategy, Business, Application, Technology, and
    Implementation & Migration layers — five distinct layers in total.
    This is useful for format matrix tests where loading the full PawsPlus
    model would be overkill.

    Layer coverage:
        - Strategy      : Capability
        - Business      : BusinessActor, BusinessRole
        - Application   : ApplicationComponent
        - Technology    : Node, SystemSoftware
        - Impl/Migration: WorkPackage
        - Motivation    : Requirement  (bonus — takes total to 6)
    """
    model = Model()

    # Strategy
    cap = Capability(name="Customer Management")
    model.add(cap)

    # Business
    actor = BusinessActor(name="Customer Service Rep")
    role = BusinessRole(name="Service Agent")
    model.add(actor)
    model.add(role)
    model.add(Assignment(name="", source=actor, target=role))

    # Application
    app = ApplicationComponent(name="CRM System")
    model.add(app)
    model.add(Realization(name="", source=app, target=cap))

    # Technology
    node = Node(name="App Server Cluster")
    db = SystemSoftware(name="PostgreSQL")
    model.add(node)
    model.add(db)
    model.add(Serving(name="", source=db, target=app))

    # Implementation & Migration
    wp = WorkPackage(name="CRM Phase 1 Rollout")
    model.add(wp)

    # Motivation
    req = Requirement(name="99.9% Uptime SLA")
    model.add(req)

    return model
