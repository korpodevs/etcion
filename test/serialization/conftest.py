"""Shared fixtures for the serialization test suite."""

from __future__ import annotations

import pytest

from etcion.metamodel.application import ApplicationComponent
from etcion.metamodel.business import BusinessActor, BusinessProcess
from etcion.metamodel.model import Model
from etcion.metamodel.profiles import Profile
from etcion.metamodel.relationships import Serving


@pytest.fixture
def simple_model() -> Model:
    """One BusinessActor, one BusinessProcess, and a Serving relationship.

    Used across CSV, DataFrame, DuckDB, JSON, Parquet, and XML serialization tests.
    """
    actor = BusinessActor(name="Alice")
    proc = BusinessProcess(name="Order Handling")
    rel = Serving(name="serves", source=actor, target=proc)
    m = Model()
    m.add(actor)
    m.add(proc)
    m.add(rel)
    return m


@pytest.fixture
def profiled_model() -> Model:
    """A model with a Cloud Profile applied to ApplicationComponent.

    Provides specialization and extended_attributes for round-trip tests.
    """
    profile = Profile(
        name="Cloud",
        specializations={ApplicationComponent: ["Microservice", "API Gateway"]},
        attribute_extensions={ApplicationComponent: {"region": str, "cost": float}},
    )
    m = Model()
    m.apply_profile(profile)

    svc = ApplicationComponent(
        name="Order Service",
        specialization="Microservice",
        extended_attributes={"region": "eu-west-1", "cost": 42.0},
    )
    m.add(svc)
    return m
