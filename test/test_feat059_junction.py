"""Tests for FEAT-05.9 -- Junction (RelationshipConnector)."""

from __future__ import annotations

import pytest

from pyarchi.enums import JunctionType
from pyarchi.metamodel.concepts import Concept, Relationship, RelationshipConnector
from pyarchi.metamodel.relationships import Junction

# ---------------------------------------------------------------------------
# JunctionType enum ratification
# ---------------------------------------------------------------------------


class TestJunctionTypeEnum:
    def test_and(self) -> None:
        assert JunctionType.AND.value == "And"

    def test_or(self) -> None:
        assert JunctionType.OR.value == "Or"

    def test_exactly_two_members(self) -> None:
        assert len(JunctionType) == 2


# ---------------------------------------------------------------------------
# Junction instantiation
# ---------------------------------------------------------------------------


class TestJunctionInstantiation:
    def test_and_junction(self) -> None:
        j = Junction(junction_type=JunctionType.AND)
        assert j.junction_type is JunctionType.AND

    def test_or_junction(self) -> None:
        j = Junction(junction_type=JunctionType.OR)
        assert j.junction_type is JunctionType.OR

    def test_type_name(self) -> None:
        j = Junction(junction_type=JunctionType.AND)
        assert j._type_name == "Junction"

    def test_has_id(self) -> None:
        j = Junction(junction_type=JunctionType.AND)
        assert isinstance(j.id, str)
        assert len(j.id) > 0

    def test_missing_junction_type_raises(self) -> None:
        with pytest.raises(Exception):  # noqa: B017
            Junction()  # type: ignore[call-arg]

    def test_no_name_attribute(self) -> None:
        j = Junction(junction_type=JunctionType.AND)
        assert not hasattr(j, "name")


# ---------------------------------------------------------------------------
# Inheritance
# ---------------------------------------------------------------------------


class TestJunctionInheritance:
    def test_is_relationship_connector(self) -> None:
        j = Junction(junction_type=JunctionType.AND)
        assert isinstance(j, RelationshipConnector)

    def test_is_concept(self) -> None:
        j = Junction(junction_type=JunctionType.AND)
        assert isinstance(j, Concept)

    def test_is_not_relationship(self) -> None:
        j = Junction(junction_type=JunctionType.AND)
        assert not isinstance(j, Relationship)  # type: ignore[unreachable]


# ---------------------------------------------------------------------------
# Validation xfails (model-level, deferred per ADR-017 ss5/ss6)
# ---------------------------------------------------------------------------


class TestDeferredValidation:
    def test_mixed_relationship_types_raises(self) -> None:
        from pyarchi.enums import JunctionType
        from pyarchi.exceptions import ValidationError
        from pyarchi.metamodel.business import BusinessActor, BusinessProcess
        from pyarchi.metamodel.model import Model
        from pyarchi.metamodel.relationships import Assignment, Junction, Serving

        j = Junction(junction_type=JunctionType.AND)
        a1 = BusinessActor(name="a1")
        bp = BusinessProcess(name="bp")
        r1 = Assignment(name="r1", source=a1, target=j)
        r2 = Serving(name="r2", source=j, target=bp)
        model = Model(concepts=[j, a1, bp, r1, r2])
        errors = model.validate()
        assert any(isinstance(e, ValidationError) for e in errors)

    def test_endpoint_permission_violation_raises(self) -> None:
        from pyarchi.enums import JunctionType
        from pyarchi.exceptions import ValidationError
        from pyarchi.metamodel.business import BusinessActor, BusinessProcess
        from pyarchi.metamodel.model import Model
        from pyarchi.metamodel.relationships import Composition, Junction

        j = Junction(junction_type=JunctionType.AND)
        a1 = BusinessActor(name="a1")
        bp = BusinessProcess(name="bp")
        r1 = Composition(name="r1", source=a1, target=j)
        r2 = Composition(name="r2", source=j, target=bp)
        model = Model(concepts=[j, a1, bp, r1, r2])
        errors = model.validate()
        assert any(isinstance(e, ValidationError) for e in errors)
