# Technical Brief: FEAT-13.5 Cross-Layer Derivation Verification

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-025-epic013-cross-layer-rules.md`
**Epic:** EPIC-013

---

## Feature Summary

**Test-only feature.** Verify that `DerivationEngine.derive()` correctly produces derived relationships from multi-hop cross-layer Realization chains. No code changes to the engine or permissions module. Per ADR-025 Decision 8, the engine is layer-agnostic and should already handle these chains.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-13.3 (Realization permissions -- needed for `is_permitted` calls in tests) | Must be done first |
| FEAT-13.4 (Realization prohibitions) | Must be done first |
| EPIC-006 (`DerivationEngine`) | Done |
| EPIC-005 (`Model`) | Done |
| ADR-025 Decision 8 | Accepted |

## Stories -> Acceptance

| Story | Scenario | Acceptance |
|---|---|---|
| 13.5.1 | Three-element chain: `Artifact -> DataObject -> BusinessObject` via Realization | `derive()` returns derived `Realization(Artifact, BusinessObject)` with `is_derived=True` |
| 13.5.2 | Three-element chain: `TechnologyProcess -> ApplicationProcess -> BusinessProcess` via Realization | `derive()` returns derived `Realization(TechnologyProcess, BusinessProcess)` with `is_derived=True` |
| 13.5.3 | No false derivation across different relationship types | Chain of `Realization` + `Serving` does NOT produce a derived relationship |

## Implementation

No source code changes. Test-only.

## Test File: `test/test_feat135_cross_layer_derivation.py`

```python
"""Tests for FEAT-13.5 -- Cross-layer derivation verification."""
from __future__ import annotations

import pytest

from pyarchi.metamodel.application import (
    ApplicationProcess,
    DataObject,
)
from pyarchi.metamodel.business import (
    BusinessObject,
    BusinessProcess,
)
from pyarchi.metamodel.technology import (
    Artifact,
    TechnologyProcess,
    TechnologyService,
)
from pyarchi.metamodel.model import Model
from pyarchi.metamodel.relationships import Realization, Serving
from pyarchi.derivation.engine import DerivationEngine


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
```

## Verification

```bash
source .venv/bin/activate
ruff check test/test_feat135_cross_layer_derivation.py
ruff format --check test/test_feat135_cross_layer_derivation.py
mypy test/test_feat135_cross_layer_derivation.py
pytest test/test_feat135_cross_layer_derivation.py -v
pytest  # full suite, no regressions
```
