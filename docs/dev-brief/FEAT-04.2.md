# Technical Brief: FEAT-04.2 BehaviorElement Hierarchy

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-016-epic004-generic-metamodel.md`
**Epic:** EPIC-004

---

## Feature Summary

Add seven abstract classes to `src/pyarchi/metamodel/elements.py`. `Interaction` has a `model_validator` and `assigned_elements` field. `Event` has a `time` field. All remain abstract.

## Dependencies

| Dependency | Status |
|---|---|
| FEAT-04.1 (StructureElement hierarchy in `elements.py`) | Must be done first |
| ADR-016 ss5, ss6 | Accepted |

## Implementation

### Additions to `src/pyarchi/metamodel/elements.py`

```python
from datetime import datetime

from pydantic import Field, model_validator

# ... existing structure classes ...


class BehaviorElement(Element): ...

class InternalBehaviorElement(BehaviorElement): ...

class Process(InternalBehaviorElement): ...

class Function(InternalBehaviorElement): ...

class Interaction(InternalBehaviorElement):
    assigned_elements: list[ActiveStructureElement] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_assigned_elements(self) -> Interaction:
        if len(self.assigned_elements) < 2:
            msg = (
                f"{type(self).__name__} requires >= 2 assigned "
                f"ActiveStructureElement instances, got {len(self.assigned_elements)}"
            )
            raise ValueError(msg)
        return self

class ExternalBehaviorElement(BehaviorElement): ...

class Event(BehaviorElement):
    time: datetime | str | None = None
```

### Stories -> Acceptance

| Story | Class | Key Detail |
|---|---|---|
| 04.2.1 | `BehaviorElement(Element)` | `TypeError` on instantiation |
| 04.2.2 | `InternalBehaviorElement(BehaviorElement)` | `TypeError` |
| 04.2.3 | `Process(InternalBehaviorElement)` | `TypeError` |
| 04.2.4 | `Function(InternalBehaviorElement)` | `TypeError` |
| 04.2.5 | `Interaction(InternalBehaviorElement)` | `TypeError`; validator on ABC |
| 04.2.6 | `ExternalBehaviorElement(BehaviorElement)` | `TypeError` |
| 04.2.7 | `Event(BehaviorElement)` | `TypeError`; `time` field present |
| 04.2.8 | Tests | All seven raise `TypeError` |

### Gotchas

1. **Mutable default on `assigned_elements`**: Use `Field(default_factory=list)`, NOT `= []`.
2. **Validator on abstract class**: `_validate_assigned_elements` is defined on `Interaction` (abstract). It fires only when a concrete subclass is instantiated. Test with a test-local concrete subclass.
3. **`from __future__ import annotations`**: Already at top of `elements.py` from FEAT-04.1. The string annotation `-> Interaction` in the validator return type works because of PEP 563.

## Test File: `test/test_feat042_behavior_elements.py`

```python
"""Tests for FEAT-04.2 -- BehaviorElement Hierarchy."""
from __future__ import annotations

from datetime import datetime
from typing import ClassVar

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.concepts import Element
from pyarchi.metamodel.elements import (
    ActiveStructureElement,
    BehaviorElement,
    Event,
    ExternalBehaviorElement,
    Function,
    InternalBehaviorElement,
    Interaction,
    Process,
)


class TestBehaviorElementHierarchyABC:
    """Each ABC raises TypeError on direct instantiation."""

    @pytest.mark.parametrize(
        "cls",
        [
            BehaviorElement,
            InternalBehaviorElement,
            Process,
            Function,
            Interaction,
            ExternalBehaviorElement,
            Event,
        ],
    )
    def test_cannot_instantiate(self, cls: type) -> None:
        with pytest.raises(TypeError):
            cls(name="test")


class TestBehaviorElementInheritance:
    """Verify issubclass relationships."""

    def test_behavior_is_element(self) -> None:
        assert issubclass(BehaviorElement, Element)

    def test_internal_behavior_is_behavior(self) -> None:
        assert issubclass(InternalBehaviorElement, BehaviorElement)

    def test_process_is_internal_behavior(self) -> None:
        assert issubclass(Process, InternalBehaviorElement)

    def test_function_is_internal_behavior(self) -> None:
        assert issubclass(Function, InternalBehaviorElement)

    def test_interaction_is_internal_behavior(self) -> None:
        assert issubclass(Interaction, InternalBehaviorElement)

    def test_external_behavior_is_behavior(self) -> None:
        assert issubclass(ExternalBehaviorElement, BehaviorElement)

    def test_event_is_behavior(self) -> None:
        assert issubclass(Event, BehaviorElement)


class TestInteractionValidatorOnConcreteSubclass:
    """Interaction.model_validator fires on concrete subclass only."""

    class _ConcreteInteraction(Interaction):
        layer: ClassVar[Layer] = Layer.BUSINESS
        aspect: ClassVar[Aspect] = Aspect.BEHAVIOR

        @property
        def _type_name(self) -> str:
            return "ConcreteInteraction"

    class _ConcreteActiveStructure(ActiveStructureElement):
        layer: ClassVar[Layer] = Layer.BUSINESS
        aspect: ClassVar[Aspect] = Aspect.ACTIVE_STRUCTURE

        @property
        def _type_name(self) -> str:
            return "ConcreteActiveStructure"

    def test_fewer_than_two_raises_validation_error(self) -> None:
        actor = self._ConcreteActiveStructure(name="a1")
        with pytest.raises(ValueError, match="requires >= 2"):
            self._ConcreteInteraction(name="i", assigned_elements=[actor])

    def test_zero_assigned_raises_validation_error(self) -> None:
        with pytest.raises(ValueError, match="requires >= 2"):
            self._ConcreteInteraction(name="i")

    def test_two_assigned_is_valid(self) -> None:
        a1 = self._ConcreteActiveStructure(name="a1")
        a2 = self._ConcreteActiveStructure(name="a2")
        interaction = self._ConcreteInteraction(
            name="i", assigned_elements=[a1, a2]
        )
        assert len(interaction.assigned_elements) == 2


class TestEventTimeField:
    """Event.time is present on concrete subclass."""

    class _ConcreteEvent(Event):
        layer: ClassVar[Layer] = Layer.BUSINESS
        aspect: ClassVar[Aspect] = Aspect.BEHAVIOR

        @property
        def _type_name(self) -> str:
            return "ConcreteEvent"

    def test_time_defaults_to_none(self) -> None:
        e = self._ConcreteEvent(name="ev")
        assert e.time is None

    def test_time_accepts_datetime(self) -> None:
        dt = datetime(2026, 1, 1, 12, 0)
        e = self._ConcreteEvent(name="ev", time=dt)
        assert e.time == dt

    def test_time_accepts_string(self) -> None:
        e = self._ConcreteEvent(name="ev", time="Q3 2026")
        assert e.time == "Q3 2026"
```

## Verification

```bash
source .venv/bin/activate
ruff check src/pyarchi/metamodel/elements.py test/test_feat042_behavior_elements.py
ruff format --check src/pyarchi/metamodel/elements.py test/test_feat042_behavior_elements.py
mypy src/pyarchi/metamodel/elements.py test/test_feat042_behavior_elements.py
pytest test/test_feat042_behavior_elements.py -v
pytest  # full suite, no regressions
```
