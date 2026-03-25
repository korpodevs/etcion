# Technical Brief: FEAT-15.4 -- Junction Validation

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-027-epic015-validation-engine.md` (Decision 4)
**Backlog:** STORY-15.4.1 through STORY-15.4.4
**Depends on:** FEAT-15.7 (`Model.validate()` must exist)

## Scope

Implement two Junction constraints inside `Model.validate()`:

1. **Homogeneity** -- all Relationships where `source` or `target` is a given Junction must share the same concrete relationship type.
2. **Endpoint permissions** -- the non-Junction endpoints connected through a Junction must be permitted for the relationship type via `is_permitted()`.

## Implementation

Inside `Model.validate()`, after iterating relationships for `is_permitted()` checks:

```python
# Build junction adjacency index: Junction.id -> list[Relationship]
junction_rels: dict[str, list[Relationship]] = {}
for rel in self.relationships:
    if isinstance(rel.source, RelationshipConnector):
        junction_rels.setdefault(rel.source.id, []).append(rel)
    if isinstance(rel.target, RelationshipConnector):
        junction_rels.setdefault(rel.target.id, []).append(rel)

for jid, rels in junction_rels.items():
    # 1. Homogeneity: all rels must be the same concrete type
    rel_types = {type(r) for r in rels}
    if len(rel_types) > 1:
        errors.append(ValidationError(
            f"Junction '{jid}': mixed relationship types {sorted(t.__name__ for t in rel_types)}"
        ))

    # 2. Endpoint permissions: collect non-junction endpoints, check pairwise
    endpoints = []
    rel_type = next(iter(rel_types))  # use the (expected single) type
    for r in rels:
        ep = r.target if isinstance(r.source, RelationshipConnector) else r.source
        if not isinstance(ep, RelationshipConnector):
            endpoints.append(ep)
    # Check all source-side endpoints vs all target-side endpoints
    # ... (exact pairing logic per spec)
```

The index is **not** cached on Model; it is recomputed each `validate()` call.

## xfail Resolution

| xfail test | File | Action |
|---|---|---|
| `test_mixed_relationship_types_raises` | `test/test_feat059_junction.py` | Remove `@pytest.mark.xfail`, rewrite body |
| `test_endpoint_permission_violation_raises` | `test/test_feat059_junction.py` | Remove `@pytest.mark.xfail`, rewrite body |

Both are placeholder stubs. Rewrite to build a Model with Junction + relationships, call `model.validate()`.

## Test File

```python
# test/test_feat154_junction_validation.py
"""Tests for FEAT-15.4: Junction model-level validation."""
from __future__ import annotations

import pytest

from pyarchi.enums import JunctionType
from pyarchi.exceptions import ValidationError
from pyarchi.metamodel.business import BusinessActor, BusinessProcess, BusinessRole
from pyarchi.metamodel.model import Model
from pyarchi.metamodel.relationships import Assignment, Composition, Junction, Serving


class TestJunctionHomogeneity:
    def test_mixed_types_produces_error(self) -> None:
        j = Junction(junction_type=JunctionType.AND)
        a1 = BusinessActor(name="a1")
        a2 = BusinessActor(name="a2")
        bp = BusinessProcess(name="bp")
        r1 = Assignment(source=a1, target=j)
        r2 = Serving(source=j, target=bp)
        model = Model(concepts=[j, a1, a2, bp, r1, r2])
        errors = model.validate()
        junction_errors = [e for e in errors if "mixed relationship types" in str(e).lower() or "Junction" in str(e)]
        assert len(junction_errors) >= 1

    def test_homogeneous_types_no_junction_error(self) -> None:
        j = Junction(junction_type=JunctionType.OR)
        a1 = BusinessActor(name="a1")
        a2 = BusinessActor(name="a2")
        bp = BusinessProcess(name="bp")
        r1 = Assignment(source=a1, target=j)
        r2 = Assignment(source=a2, target=j)
        r3 = Assignment(source=j, target=bp)
        model = Model(concepts=[j, a1, a2, bp, r1, r2, r3])
        errors = model.validate()
        junction_errors = [e for e in errors if "Junction" in str(e)]
        assert len(junction_errors) == 0


class TestJunctionEndpointPermissions:
    def test_endpoint_violation_produces_error(self) -> None:
        """Non-junction endpoints must be permitted for the relationship type."""
        j = Junction(junction_type=JunctionType.AND)
        a1 = BusinessActor(name="a1")
        a2 = BusinessActor(name="a2")
        # Composition between BusinessActor and BusinessProcess is not same-type
        bp = BusinessProcess(name="bp")
        r1 = Composition(source=a1, target=j)
        r2 = Composition(source=j, target=bp)
        model = Model(concepts=[j, a1, a2, bp, r1, r2])
        errors = model.validate()
        assert len(errors) >= 1
```

### Rewritten xfail tests

**`test/test_feat059_junction.py`** -- replace `test_mixed_relationship_types_raises`:

```python
def test_mixed_relationship_types_raises(self) -> None:
    from pyarchi.enums import JunctionType
    from pyarchi.metamodel.business import BusinessActor, BusinessProcess
    from pyarchi.metamodel.model import Model
    from pyarchi.metamodel.relationships import Assignment, Junction, Serving
    from pyarchi.exceptions import ValidationError

    j = Junction(junction_type=JunctionType.AND)
    a1 = BusinessActor(name="a1")
    bp = BusinessProcess(name="bp")
    r1 = Assignment(source=a1, target=j)
    r2 = Serving(source=j, target=bp)
    model = Model(concepts=[j, a1, bp, r1, r2])
    errors = model.validate()
    assert any(isinstance(e, ValidationError) for e in errors)
```

**`test/test_feat059_junction.py`** -- replace `test_endpoint_permission_violation_raises`:

```python
def test_endpoint_permission_violation_raises(self) -> None:
    from pyarchi.enums import JunctionType
    from pyarchi.metamodel.business import BusinessActor, BusinessProcess
    from pyarchi.metamodel.model import Model
    from pyarchi.metamodel.relationships import Composition, Junction
    from pyarchi.exceptions import ValidationError

    j = Junction(junction_type=JunctionType.AND)
    a1 = BusinessActor(name="a1")
    bp = BusinessProcess(name="bp")
    r1 = Composition(source=a1, target=j)
    r2 = Composition(source=j, target=bp)
    model = Model(concepts=[j, a1, bp, r1, r2])
    errors = model.validate()
    assert any(isinstance(e, ValidationError) for e in errors)
```
