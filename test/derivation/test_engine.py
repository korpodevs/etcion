"""Merged tests: test_feat0510_derivation, test_feat135_cross_layer_derivation."""

from __future__ import annotations

from typing import ClassVar

import pytest

from etcion.derivation.engine import DerivationEngine
from etcion.enums import Aspect, Layer, RelationshipCategory
from etcion.metamodel.application import (
    ApplicationProcess,
    DataObject,
)
from etcion.metamodel.business import (
    BusinessObject,
    BusinessProcess,
)
from etcion.metamodel.concepts import Element, Relationship
from etcion.metamodel.elements import ActiveStructureElement, BehaviorElement
from etcion.metamodel.model import Model
from etcion.metamodel.relationships import Realization, Serving
from etcion.metamodel.technology import (
    Artifact,
    TechnologyProcess,
    TechnologyService,
)

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


class TestCrossLayerRealizationChain:
    """DerivationEngine derives transitive Realization across layers."""

    def test_artifact_dataobject_businessobject(self) -> None:
        """Artifact -> DataObject -> BusinessObject produces derived Artifact -> BusinessObject."""
        art = Artifact(name="deploy.war")
        do = DataObject(name="CustomerData")
        bo = BusinessObject(name="Customer")

        r1 = Realization(name="r1", source=art, target=do)
        r2 = Realization(name="r2", source=do, target=bo)

        model = Model(concepts=[art, do, bo, r1, r2])
        engine = DerivationEngine()
        derived = engine.derive(model)

        assert len(derived) == 1
        d = derived[0]
        assert isinstance(d, Realization)
        assert d.source is art
        assert d.target is bo
        assert d.is_derived is True

    def test_tech_app_business_process_chain(self) -> None:
        """TechProcess -> AppProcess -> BizProcess produces derived TechProcess -> BizProcess."""
        tp = TechnologyProcess(name="Deploy")
        ap = ApplicationProcess(name="ProcessOrder")
        bp = BusinessProcess(name="FulfillOrder")

        r1 = Realization(name="r1", source=tp, target=ap)
        r2 = Realization(name="r2", source=ap, target=bp)

        model = Model(concepts=[tp, ap, bp, r1, r2])
        engine = DerivationEngine()
        derived = engine.derive(model)

        assert len(derived) == 1
        d = derived[0]
        assert isinstance(d, Realization)
        assert d.source is tp
        assert d.target is bp
        assert d.is_derived is True


class TestNoCrossTypeDerivation:
    """Chains of different relationship types do not produce derivations."""

    def test_realization_plus_serving_no_derivation(self) -> None:
        """Realization(A,B) + Serving(B,C) does NOT derive anything."""
        art = Artifact(name="deploy.war")
        do = DataObject(name="CustomerData")
        bp = BusinessProcess(name="FulfillOrder")

        r1 = Realization(name="r1", source=art, target=do)
        s1 = Serving(name="s1", source=do, target=bp)

        model = Model(concepts=[art, do, bp, r1, s1])
        engine = DerivationEngine()
        derived = engine.derive(model)

        assert len(derived) == 0
