# Technical Brief: FEAT-05.1 RelationshipCategory Enum

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-017-epic005-relationships.md` ss1
**Epic:** EPIC-005

---

## Feature Summary

`RelationshipCategory` enum already exists in `src/pyarchi/enums.py` with four members. This feature is ratified (ADR-017 ss1). Only tests are needed -- no production code changes.

## Dependencies

| Dependency | Status |
|---|---|
| `RelationshipCategory` in `enums.py` | Done (ADR-002) |
| ADR-017 ss1 (ratification) | Accepted |

## Stories -> Acceptance

| Story | Acceptance |
|---|---|
| 05.1.1 | `RelationshipCategory` exists in `enums.py` with `STRUCTURAL`, `DEPENDENCY`, `DYNAMIC`, `OTHER` |
| 05.1.2 | Test asserts all four values present and accessible |

## Implementation

No production code changes. Enum already exists:

```python
class RelationshipCategory(Enum):
    STRUCTURAL = "Structural"
    DEPENDENCY = "Dependency"
    DYNAMIC = "Dynamic"
    OTHER = "Other"
```

## Test File: `test/test_feat051_relationship_category.py`

```python
"""Tests for FEAT-05.1 -- RelationshipCategory Enum (ratification)."""
from __future__ import annotations

from pyarchi.enums import RelationshipCategory


class TestRelationshipCategoryMembers:
    """All four required members exist with correct values."""

    def test_structural(self) -> None:
        assert RelationshipCategory.STRUCTURAL.value == "Structural"

    def test_dependency(self) -> None:
        assert RelationshipCategory.DEPENDENCY.value == "Dependency"

    def test_dynamic(self) -> None:
        assert RelationshipCategory.DYNAMIC.value == "Dynamic"

    def test_other(self) -> None:
        assert RelationshipCategory.OTHER.value == "Other"

    def test_exactly_four_members(self) -> None:
        assert len(RelationshipCategory) == 4

    def test_iterable(self) -> None:
        names = {m.name for m in RelationshipCategory}
        assert names == {"STRUCTURAL", "DEPENDENCY", "DYNAMIC", "OTHER"}
```

## Verification

```bash
source .venv/bin/activate
ruff check test/test_feat051_relationship_category.py
ruff format --check test/test_feat051_relationship_category.py
mypy test/test_feat051_relationship_category.py
pytest test/test_feat051_relationship_category.py -v
pytest  # full suite, no regressions
```
