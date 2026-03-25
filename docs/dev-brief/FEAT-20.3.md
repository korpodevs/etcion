# Technical Brief: FEAT-20.3 -- Phase 3 Exports in `__init__.py`

**Status:** Ready for TDD
**ADR Link:** `docs/adr/ADR-032-epic020-conformance-cleanup.md` (Decision 3)
**Depends on:** Nothing (implement first)

## Scope

Add Phase 3 types to `src/pyarchi/__init__.py` imports and `__all__`.

### Imports to Add

| Symbol | Source Module |
|---|---|
| `Viewpoint` | `pyarchi.metamodel.viewpoints` |
| `View` | `pyarchi.metamodel.viewpoints` |
| `Concern` | `pyarchi.metamodel.viewpoints` |
| `Profile` | `pyarchi.metamodel.profiles` |
| `PurposeCategory` | `pyarchi.enums` |
| `ContentCategory` | `pyarchi.enums` |

### Changes to `src/pyarchi/__init__.py`

1. Add import block after line 161 (after `is_permitted` import), grouped under `# Phase 3`:

```python
# Phase 3: Viewpoints (EPIC-017)
from pyarchi.metamodel.viewpoints import Concern, View, Viewpoint

# Phase 3: Language customization (EPIC-018)
from pyarchi.metamodel.profiles import Profile

# Phase 3: Enums (viewpoint categories)
# PurposeCategory and ContentCategory already defined in pyarchi.enums;
# add them to the existing enums import block.
```

2. Add `PurposeCategory` and `ContentCategory` to the existing `from pyarchi.enums import (...)` block (line 5-13).

3. Append to `__all__` list after `"Gap"` (line 302):

```python
    # Viewpoints & Language Customization (Phase 3)
    "Viewpoint",
    "View",
    "Concern",
    "Profile",
    "PurposeCategory",
    "ContentCategory",
```

### Exclusions (per ADR-031 Decision 11)

Serialization functions (`serialize_model`, `deserialize_model`, `write_model`, `read_model`, `model_to_dict`, `model_from_dict`) are NOT exported.

## Test File

Create `test/test_feat203_exports.py`:

```python
"""Tests for FEAT-20.3: Phase 3 public API exports."""

from __future__ import annotations

import pytest

import pyarchi

PHASE_3_EXPORTS = [
    "Viewpoint",
    "View",
    "Concern",
    "Profile",
    "PurposeCategory",
    "ContentCategory",
]


class TestPhase3Exports:
    @pytest.mark.parametrize("name", PHASE_3_EXPORTS)
    def test_symbol_importable_from_pyarchi(self, name: str) -> None:
        assert hasattr(pyarchi, name), f"{name} not found in pyarchi namespace"

    @pytest.mark.parametrize("name", PHASE_3_EXPORTS)
    def test_symbol_in_all(self, name: str) -> None:
        assert name in pyarchi.__all__, f"{name} not in pyarchi.__all__"

    def test_no_serialization_functions_in_all(self) -> None:
        forbidden = {
            "serialize_model",
            "deserialize_model",
            "write_model",
            "read_model",
            "model_to_dict",
            "model_from_dict",
        }
        leaked = forbidden & set(pyarchi.__all__)
        assert leaked == set(), f"Serialization functions leaked into __all__: {leaked}"
```

## Verification

```bash
pytest test/test_feat203_exports.py -v
```
