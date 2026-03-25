# Technical Brief: FEAT-17.1 -- Viewpoint Enums and Data Types

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-029-epic017-viewpoint-mechanism.md`
**Spec:** ArchiMate 3.2, Section 13.2

## Scope

| Artifact | Location |
|---|---|
| `PurposeCategory` | `src/pyarchi/enums.py` |
| `ContentCategory` | `src/pyarchi/enums.py` |

## Implementation

Both enums follow the existing `enum.Enum` pattern (NOT `StrEnum`). String values.

```python
class PurposeCategory(Enum):
    DESIGNING = "Designing"
    DECIDING = "Deciding"
    INFORMING = "Informing"

class ContentCategory(Enum):
    DETAILS = "Details"
    COHERENCE = "Coherence"
    OVERVIEW = "Overview"
```

Append after `JunctionType` in `enums.py`.

## Validation

- Exactly 3 members each.
- Values are title-cased strings matching spec terminology.

## Test File: `test/test_feat171_viewpoint_enums.py`

```python
from __future__ import annotations

import pytest

from pyarchi.enums import ContentCategory, PurposeCategory


class TestPurposeCategory:
    def test_member_count(self) -> None:
        assert len(PurposeCategory) == 3

    def test_members_exist(self) -> None:
        assert PurposeCategory.DESIGNING.value == "Designing"
        assert PurposeCategory.DECIDING.value == "Deciding"
        assert PurposeCategory.INFORMING.value == "Informing"

    def test_is_enum_not_str(self) -> None:
        assert not isinstance(PurposeCategory.DESIGNING, str)


class TestContentCategory:
    def test_member_count(self) -> None:
        assert len(ContentCategory) == 3

    def test_members_exist(self) -> None:
        assert ContentCategory.DETAILS.value == "Details"
        assert ContentCategory.COHERENCE.value == "Coherence"
        assert ContentCategory.OVERVIEW.value == "Overview"

    def test_is_enum_not_str(self) -> None:
        assert not isinstance(ContentCategory.DETAILS, str)
```
