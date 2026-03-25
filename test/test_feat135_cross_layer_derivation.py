"""Tests for FEAT-13.5 -- Cross-layer derivation verification."""

from __future__ import annotations

from pyarchi.derivation.engine import DerivationEngine
from pyarchi.metamodel.application import (
    ApplicationProcess,
    DataObject,
)
from pyarchi.metamodel.business import (
    BusinessObject,
    BusinessProcess,
)
from pyarchi.metamodel.model import Model
from pyarchi.metamodel.relationships import Realization, Serving
from pyarchi.metamodel.technology import (
    Artifact,
    TechnologyProcess,
    TechnologyService,
)


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
