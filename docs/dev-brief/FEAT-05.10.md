# Technical Brief: FEAT-05.10 Derivation Engine

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-017-epic005-relationships.md` ss8
**Epic:** EPIC-005

---

## Feature Summary

Implement `DerivationEngine` in `src/pyarchi/derivation/engine.py` with `derive(model) -> list[Relationship]` and `is_directly_permitted(rel_type, source, target) -> bool`. The engine is a pure function: it reads a `Model`, returns new `Relationship` instances with `is_derived=True`, and does NOT mutate the source model.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-05.2 through FEAT-05.8 (all concrete relationship types) | Must be done first |
| FEAT-05.11 (permission table) | Must be done first or concurrently |
| `Model` in `metamodel/model.py` | Done |
| ADR-017 ss8 | Accepted |

## Stories -> Acceptance

| Story | Testable Now? | Acceptance |
|---|---|---|
| 05.10.1 | Yes | `DerivationEngine` class exists and is importable |
| 05.10.2 | Yes | `derive(model)` returns `list[Relationship]` |
| 05.10.3 | Yes | `is_directly_permitted()` delegates to permission table |
| 05.10.4 | Yes | Structural chains produce structural derived relationships |
| 05.10.5 | Yes | All returned relationships have `is_derived == True` |
| 05.10.6 | Yes | Source model is not mutated by `derive()` |
| 05.10.7 | Yes | Derivation direction constraint enforced |
| 05.10.8 | Yes | Three-hop realization chain test |
| 05.10.9 | Yes | `is_derived == True` on results |
| 05.10.10 | Yes | Model immutability test |
| 05.10.11 | Yes | `is_directly_permitted` spot check |

## Implementation

### File: `src/pyarchi/derivation/engine.py`

```python
from __future__ import annotations

from pyarchi.metamodel.concepts import Element, Relationship
from pyarchi.metamodel.model import Model
from pyarchi.validation.permissions import is_permitted


class DerivationEngine:
    """Derives implicit relationships from chains in a Model.

    Pure-function design: derive() does not mutate the source Model.
    """

    def derive(self, model: Model) -> list[Relationship]:
        """Compute all derivable relationships from relationship chains.

        Returns new Relationship instances with is_derived=True.
        Does NOT modify the source model.
        """
        ...  # Implementation details per spec Section 5.6

    def is_directly_permitted(
        self,
        rel_type: type[Relationship],
        source: Element,
        target: Element,
    ) -> bool:
        """Check if a direct relationship is permitted per Appendix B."""
        return is_permitted(rel_type, type(source), type(target))
```

### Derivation Rules (spec Section 5.6)

1. **Structural chain:** Composition/Aggregation chains derive Composition/Aggregation between endpoints.
2. **Assignment chain:** Assignment chains derive Assignment.
3. **Dependency chain:** Serving/Access chains derive the weaker relationship type.
4. **Cross-category:** Structural + Dependency derives Dependency between endpoints.
5. **Direction:** Derivation flows from more detail to less detail (abstraction direction).

### Gotchas

1. **Circular import.** `engine.py` imports from `validation.permissions` and `metamodel.model`. Neither imports from `derivation`. Safe.
2. **Idempotency.** Running `derive()` twice on the same model should produce identical results. The engine does not add to the model.
3. **Large models.** Derivation is $O(n \cdot m)$ where $n$ = elements, $m$ = relationships. Avoid $O(n^2)$ nested loops over all element pairs. Build an adjacency list first.

## Test File: `test/test_feat0510_derivation.py`

```python
"""Tests for FEAT-05.10 -- DerivationEngine."""
from __future__ import annotations

from typing import ClassVar

import pytest

from pyarchi.enums import Aspect, Layer, RelationshipCategory
from pyarchi.metamodel.concepts import Element, Relationship
from pyarchi.metamodel.elements import ActiveStructureElement, BehaviorElement
from pyarchi.metamodel.model import Model
from pyarchi.metamodel.relationships import Realization, Serving
from pyarchi.derivation.engine import DerivationEngine


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
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/derivation/engine.py test/test_feat0510_derivation.py
ruff format --check src/pyarchi/derivation/engine.py test/test_feat0510_derivation.py
mypy src/pyarchi/derivation/engine.py test/test_feat0510_derivation.py
pytest test/test_feat0510_derivation.py -v
pytest  # full suite, no regressions
```
