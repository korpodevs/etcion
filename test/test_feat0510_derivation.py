"""Tests for FEAT-05.10 -- DerivationEngine."""

from __future__ import annotations

from typing import ClassVar

import pytest

from pyarchi.derivation.engine import DerivationEngine
from pyarchi.enums import Aspect, Layer, RelationshipCategory
from pyarchi.metamodel.concepts import Element, Relationship
from pyarchi.metamodel.elements import ActiveStructureElement, BehaviorElement
from pyarchi.metamodel.model import Model
from pyarchi.metamodel.relationships import Realization, Serving

# ---------------------------------------------------------------------------
# Test-local concrete element stubs
# ---------------------------------------------------------------------------


class _ConcreteActive(ActiveStructureElement):
    layer: ClassVar[Layer] = Layer.APPLICATION
    aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE

    @property
    def _type_name(self) -> str:
        return "StubActive"


class _ConcreteBehavior(BehaviorElement):
    layer: ClassVar[Layer] = Layer.APPLICATION
    aspect: ClassVar[Aspect] = Aspect.BEHAVIOR

    @property
    def _type_name(self) -> str:
        return "StubBehavior"


# ---------------------------------------------------------------------------
# Engine existence and interface
# ---------------------------------------------------------------------------


class TestDerivationEngineInterface:
    def test_engine_importable(self) -> None:
        assert DerivationEngine is not None

    def test_derive_returns_list(self) -> None:
        engine = DerivationEngine()
        model = Model(concepts=[])
        result = engine.derive(model)
        assert isinstance(result, list)

    def test_derive_empty_model_returns_empty(self) -> None:
        engine = DerivationEngine()
        model = Model(concepts=[])
        assert engine.derive(model) == []


# ---------------------------------------------------------------------------
# Derived relationships have is_derived=True
# ---------------------------------------------------------------------------


class TestDerivedFlag:
    def test_three_hop_realization_chain(self) -> None:
        a = _ConcreteActive(name="a")
        b = _ConcreteActive(name="b")
        c = _ConcreteActive(name="c")
        r1 = Realization(name="r1", source=a, target=b)
        r2 = Realization(name="r2", source=b, target=c)
        model = Model(concepts=[a, b, c, r1, r2])
        engine = DerivationEngine()
        derived = engine.derive(model)
        # Should derive Realization(a -> c)
        assert len(derived) >= 1
        for r in derived:
            assert r.is_derived is True


# ---------------------------------------------------------------------------
# Model immutability
# ---------------------------------------------------------------------------


class TestModelImmutability:
    def test_derive_does_not_mutate_model(self) -> None:
        a = _ConcreteActive(name="a")
        b = _ConcreteActive(name="b")
        c = _ConcreteActive(name="c")
        r1 = Realization(name="r1", source=a, target=b)
        r2 = Realization(name="r2", source=b, target=c)
        model = Model(concepts=[a, b, c, r1, r2])
        original_count = len(model.concepts)
        engine = DerivationEngine()
        engine.derive(model)
        assert len(model.concepts) == original_count


# ---------------------------------------------------------------------------
# is_directly_permitted
# ---------------------------------------------------------------------------


class TestIsDirectlyPermitted:
    def test_spot_check(self) -> None:
        engine = DerivationEngine()
        a = _ConcreteActive(name="a")
        b = _ConcreteBehavior(name="b")
        # This is a representative check; actual result depends on permission table
        result = engine.is_directly_permitted(Serving, a, b)
        assert isinstance(result, bool)
