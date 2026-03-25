"""Tests for FEAT-15.4: Junction model-level validation."""

from __future__ import annotations

from pyarchi.enums import JunctionType
from pyarchi.exceptions import ValidationError
from pyarchi.metamodel.business import BusinessActor, BusinessProcess, BusinessRole
from pyarchi.metamodel.model import Model
from pyarchi.metamodel.relationships import (
    Assignment,
    Composition,
    Junction,
    Serving,
    Specialization,
)


class TestJunctionHomogeneity:
    def test_mixed_types_produces_error(self) -> None:
        j = Junction(junction_type=JunctionType.AND)
        a1 = BusinessActor(name="a1")
        bp = BusinessProcess(name="bp")
        r1 = Assignment(name="r1", source=a1, target=j)
        r2 = Serving(name="r2", source=j, target=bp)
        model = Model(concepts=[j, a1, bp, r1, r2])
        errors = model.validate()
        junction_errors = [e for e in errors if "Junction" in str(e)]
        assert len(junction_errors) >= 1

    def test_homogeneous_types_no_junction_error(self) -> None:
        j = Junction(junction_type=JunctionType.OR)
        a1 = BusinessActor(name="a1")
        a2 = BusinessActor(name="a2")
        a3 = BusinessActor(name="a3")
        r1 = Specialization(name="r1", source=a1, target=j)
        r2 = Specialization(name="r2", source=a2, target=j)
        r3 = Specialization(name="r3", source=j, target=a3)
        model = Model(concepts=[j, a1, a2, a3, r1, r2, r3])
        errors = model.validate()
        junction_errors = [e for e in errors if "Junction" in str(e)]
        assert len(junction_errors) == 0


class TestJunctionEndpointPermissions:
    def test_endpoint_violation_produces_error(self) -> None:
        """Non-junction endpoints must be permitted for the relationship type."""
        j = Junction(junction_type=JunctionType.AND)
        a1 = BusinessActor(name="a1")
        bp = BusinessProcess(name="bp")
        # Composition between BusinessActor and BusinessProcess is not same-type
        r1 = Composition(name="r1", source=a1, target=j)
        r2 = Composition(name="r2", source=j, target=bp)
        model = Model(concepts=[j, a1, bp, r1, r2])
        errors = model.validate()
        assert len(errors) >= 1
