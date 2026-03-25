# Technical Brief: FEAT-09.4 Technology Passive Structure Element

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-021-epic009-technology-layer.md`
**Epic:** EPIC-009

---

## Feature Summary

Define one concrete class in `src/pyarchi/metamodel/technology.py`: `Artifact` extending `PassiveStructureElement` directly. No Technology passive structure ABC is introduced (ADR-021 Decision 10). Wire `NotationMetadata`.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-04.1 (`PassiveStructureElement` in `elements.py`) | Done |
| FEAT-03.1 (`NotationMetadata`) | Done |
| ADR-021 Decisions 3, 10, 11 | Accepted |

## Stories -> Acceptance

| Story | Class | Acceptance |
|---|---|---|
| 09.4.1 | `Artifact(PassiveStructureElement)` | `_type_name == "Artifact"` |
| 09.4.2 | ClassVars | `layer is Layer.TECHNOLOGY`, `aspect is Aspect.PASSIVE_STRUCTURE` |
| 09.4.3 | `NotationMetadata` | `layer_color="#C9E7B7"`, `badge_letter="T"` |
| 09.4.4 | Test | `Artifact` instantiates without error |
| 09.4.5 | Test | `isinstance(Artifact(...), PassiveStructureElement)` is `True` |

## Implementation

### Additions to `src/pyarchi/metamodel/technology.py`

```python
from pyarchi.metamodel.elements import PassiveStructureElement

# ... existing ABCs, active structure, and behavior classes ...


class Artifact(PassiveStructureElement):
    layer: ClassVar[Layer] = Layer.TECHNOLOGY
    aspect: ClassVar[Aspect] = Aspect.PASSIVE_STRUCTURE
    notation: ClassVar[NotationMetadata] = NotationMetadata(
        corner_shape="square",
        layer_color="#C9E7B7",
        badge_letter="T",
    )

    @property
    def _type_name(self) -> str:
        return "Artifact"
```

`Artifact` declares its own `layer` and `aspect` ClassVars because there is no Technology passive structure ABC (ADR-021 Decision 10).

## Test File: `test/test_feat094_technology_passive_structure.py`

```python
"""Tests for FEAT-09.4 -- Technology Passive Structure concrete element."""
from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.elements import PassiveStructureElement
from pyarchi.metamodel.technology import Artifact


class TestInstantiation:
    def test_can_instantiate(self) -> None:
        obj = Artifact(name="test")
        assert obj.name == "test"


class TestTypeName:
    def test_artifact(self) -> None:
        assert Artifact(name="x")._type_name == "Artifact"


class TestInheritance:
    def test_is_passive_structure_element(self) -> None:
        assert issubclass(Artifact, PassiveStructureElement)

    def test_isinstance_passive_structure(self) -> None:
        assert isinstance(Artifact(name="x"), PassiveStructureElement)


class TestClassVars:
    def test_layer_is_technology(self) -> None:
        assert Artifact.layer is Layer.TECHNOLOGY

    def test_aspect_is_passive_structure(self) -> None:
        assert Artifact.aspect is Aspect.PASSIVE_STRUCTURE


class TestNotation:
    def test_layer_color(self) -> None:
        assert Artifact.notation.layer_color == "#C9E7B7"

    def test_badge_letter(self) -> None:
        assert Artifact.notation.badge_letter == "T"

    def test_corner_shape_square(self) -> None:
        assert Artifact.notation.corner_shape == "square"
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/technology.py test/test_feat094_technology_passive_structure.py
ruff format --check src/pyarchi/metamodel/technology.py test/test_feat094_technology_passive_structure.py
mypy src/pyarchi/metamodel/technology.py test/test_feat094_technology_passive_structure.py
pytest test/test_feat094_technology_passive_structure.py -v
pytest  # full suite, no regressions
```
