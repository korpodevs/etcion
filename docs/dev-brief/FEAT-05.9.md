# Technical Brief: FEAT-05.9 Junction (Relationship Connector)

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-017-epic005-relationships.md` ss2, ss5, ss6
**Epic:** EPIC-005

---

## Feature Summary

Define `Junction(RelationshipConnector)` as a concrete class with mandatory `junction_type: JunctionType`. `JunctionType` enum already exists in `enums.py` (ratified ADR-017 ss2). Junction is NOT a `Relationship`. Homogeneous-type and endpoint-permission validations (STORY-05.9.3, 05.9.4, 05.9.5, 05.9.7, 05.9.10) are model-level concerns and deferred.

## Dependencies

| Dependency | Status |
|---|---|
| `RelationshipConnector` ABC in `concepts.py` | Done |
| `JunctionType` in `enums.py` | Done (ratified ADR-017 ss2) |
| FEAT-05.2 (`relationships.py` exists) | Must be done first |

## Stories -> Acceptance

| Story | Testable Now? | Acceptance |
|---|---|---|
| 05.9.1 | Tests only | `JunctionType` exists with `AND`, `OR` |
| 05.9.2 | Yes | `Junction` instantiates with mandatory `junction_type` |
| 05.9.3 | No -- xfail | Homogeneous-type constraint is model-level |
| 05.9.4 | No -- xfail | Endpoint permission checking is model-level |
| 05.9.5 | No -- xfail | Topology validation is model-level |
| 05.9.6 | Yes | `Junction()` without `junction_type` raises validation error |
| 05.9.7 | No -- xfail | Mixed-type rejection is model-level |
| 05.9.8 | Yes | `isinstance(Junction(...), RelationshipConnector)` is `True` |
| 05.9.9 | Yes | `isinstance(Junction(...), Relationship)` is `False` |
| 05.9.10 | No -- xfail | Endpoint permission checking is model-level |

## Implementation

### Addition to `src/pyarchi/metamodel/relationships.py`

```python
from pyarchi.enums import JunctionType
from pyarchi.metamodel.concepts import RelationshipConnector


class Junction(RelationshipConnector):
    junction_type: JunctionType

    @property
    def _type_name(self) -> str:
        return "Junction"
```

`junction_type` has no default -- it is mandatory. Pydantic will raise `ValidationError` if omitted.

### Gotchas

1. **`Junction` is in `relationships.py` despite not being a `Relationship`.** It is co-located per ADR-017 ss9 because it participates in relationship chains. Imports `RelationshipConnector` from `concepts.py`.
2. **No `name` field.** `Junction` extends `RelationshipConnector(Concept)` which does NOT mix in `AttributeMixin`. It has `id` but not `name`.
3. **No `source`/`target`.** `Junction` does not have `source` or `target` fields. Connection topology is a model-level concern.

## Test File: `test/test_feat059_junction.py`

```python
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
        with pytest.raises(Exception):
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
        assert not isinstance(j, Relationship)


# ---------------------------------------------------------------------------
# Validation xfails (model-level, deferred per ADR-017 ss5/ss6)
# ---------------------------------------------------------------------------


class TestDeferredValidation:
    @pytest.mark.xfail(
        strict=False,
        reason="Homogeneous-type constraint deferred to model-level (ADR-017 ss5/ss6)",
    )
    def test_mixed_relationship_types_raises(self) -> None:
        pytest.fail("Model-level validation not yet implemented")

    @pytest.mark.xfail(
        strict=False,
        reason="Endpoint permission checking deferred to model-level (ADR-017 ss5/ss6)",
    )
    def test_endpoint_permission_violation_raises(self) -> None:
        pytest.fail("Model-level validation not yet implemented")
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/relationships.py test/test_feat059_junction.py
ruff format --check src/pyarchi/metamodel/relationships.py test/test_feat059_junction.py
mypy src/pyarchi/metamodel/relationships.py test/test_feat059_junction.py
pytest test/test_feat059_junction.py -v
pytest  # full suite, no regressions
```
