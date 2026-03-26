# Technical Brief: FEAT-23.1 -- Element Query Methods
**Status:** Ready for TDD
**ADR Link:** `docs/adr/ADR-036-epic023-model-querying.md`

## Story Disposition

| Story | Status | Maps To |
|---|---|---|
| STORY-23.1.1 (`QueryBuilder`) | **Rejected** (ADR D1) | N/A |
| STORY-23.1.2 (`of_type`) | Accepted | `Model.elements_of_type()` |
| STORY-23.1.3 (`in_layer`) | Accepted | `Model.elements_by_layer()` |
| STORY-23.1.4 (`with_aspect`) | Accepted | `Model.elements_by_aspect()` |
| STORY-23.1.5 (`named` glob) | Modified (ADR D3) | `Model.elements_by_name()` -- substring + regex, no glob |
| STORY-23.1.6 (`.all()` / `.first()`) | **Rejected** (ADR D1) | N/A |
| STORY-23.1.7 (test: of_type) | Accepted | See test file below |
| STORY-23.1.8 (test: chained) | Modified | Compose via list comprehension instead of chain |

## Method Signatures

All methods added to `Model` in `src/pyarchi/metamodel/model.py`.

```python
import re
from pyarchi.enums import Layer, Aspect

def elements_of_type(self, cls: type[Element]) -> list[Element]:
    """Return elements that are instances of *cls* (includes subclasses)."""
    return [e for e in self.elements if isinstance(e, cls)]

def elements_by_layer(self, layer: Layer) -> list[Element]:
    """Return elements whose class-level ``layer`` ClassVar matches."""
    return [e for e in self.elements if getattr(type(e), 'layer', None) is layer]

def elements_by_aspect(self, aspect: Aspect) -> list[Element]:
    """Return elements whose class-level ``aspect`` ClassVar matches."""
    return [e for e in self.elements if getattr(type(e), 'aspect', None) is aspect]

def elements_by_name(self, pattern: str, *, regex: bool = False) -> list[Element]:
    """Return elements whose name contains *pattern* (substring).

    When *regex* is ``True``, uses ``re.search(pattern, name)`` instead.
    """
    if regex:
        compiled = re.compile(pattern)
        return [e for e in self.elements if e.name and compiled.search(e.name)]
    return [e for e in self.elements if e.name and pattern in e.name]
```

## New Import

Add `import re` to the top of `model.py`. Add `from pyarchi.enums import Layer, Aspect` (or inline in TYPE_CHECKING -- but since used at runtime, must be a real import).

## Test File

`test/test_feat231_element_queries.py`

```python
"""Tests for FEAT-23.1 -- Element query methods on Model."""
from __future__ import annotations

import pytest

from pyarchi.enums import Aspect, Layer
from pyarchi.metamodel.business import (
    BusinessActor,
    BusinessFunction,
    BusinessObject,
    BusinessRole,
    BusinessService,
    Product,
)
from pyarchi.metamodel.application import (
    ApplicationComponent,
    ApplicationService,
)
from pyarchi.metamodel.model import Model


@pytest.fixture
def model() -> Model:
    m = Model()
    m.add(BusinessActor(name="Alice"))
    m.add(BusinessActor(name="Bob"))
    m.add(BusinessRole(name="Manager"))
    m.add(BusinessFunction(name="Hiring"))
    m.add(BusinessObject(name="Contract Doc"))
    m.add(BusinessService(name="HR Service"))
    m.add(ApplicationComponent(name="CRM System"))
    m.add(ApplicationService(name="CRM API"))
    m.add(Product(name="Enterprise Suite"))
    return m


# -- elements_of_type ---------------------------------------------------------

class TestElementsOfType:
    def test_exact_type(self, model: Model) -> None:
        result = model.elements_of_type(BusinessActor)
        assert len(result) == 2
        assert all(isinstance(e, BusinessActor) for e in result)

    def test_subclass_included(self, model: Model) -> None:
        """BusinessObject is parent of Contract; but here we just check
        that isinstance-based matching works with the hierarchy."""
        from pyarchi.metamodel.concepts import Element
        result = model.elements_of_type(Element)
        assert len(result) == len(model.elements)

    def test_no_matches(self, model: Model) -> None:
        from pyarchi.metamodel.technology import Node
        assert model.elements_of_type(Node) == []

    def test_returns_list(self, model: Model) -> None:
        result = model.elements_of_type(BusinessActor)
        assert isinstance(result, list)


# -- elements_by_layer --------------------------------------------------------

class TestElementsByLayer:
    def test_business_layer(self, model: Model) -> None:
        result = model.elements_by_layer(Layer.BUSINESS)
        names = {e.name for e in result}
        assert "Alice" in names
        assert "Manager" in names
        assert "Enterprise Suite" in names  # Product is Business layer
        assert "CRM System" not in names

    def test_application_layer(self, model: Model) -> None:
        result = model.elements_by_layer(Layer.APPLICATION)
        names = {e.name for e in result}
        assert names == {"CRM System", "CRM API"}

    def test_empty_layer(self, model: Model) -> None:
        assert model.elements_by_layer(Layer.TECHNOLOGY) == []


# -- elements_by_aspect -------------------------------------------------------

class TestElementsByAspect:
    def test_active_structure(self, model: Model) -> None:
        result = model.elements_by_aspect(Aspect.ACTIVE_STRUCTURE)
        names = {e.name for e in result}
        assert "Alice" in names
        assert "Manager" in names
        assert "CRM System" in names

    def test_behavior(self, model: Model) -> None:
        result = model.elements_by_aspect(Aspect.BEHAVIOR)
        names = {e.name for e in result}
        assert "Hiring" in names
        assert "HR Service" in names
        assert "CRM API" in names

    def test_passive_structure(self, model: Model) -> None:
        result = model.elements_by_aspect(Aspect.PASSIVE_STRUCTURE)
        assert len(result) == 1
        assert result[0].name == "Contract Doc"

    def test_composite(self, model: Model) -> None:
        result = model.elements_by_aspect(Aspect.COMPOSITE)
        assert len(result) == 1
        assert result[0].name == "Enterprise Suite"


# -- elements_by_name ---------------------------------------------------------

class TestElementsByName:
    def test_substring_match(self, model: Model) -> None:
        result = model.elements_by_name("CRM")
        assert len(result) == 2

    def test_substring_no_match(self, model: Model) -> None:
        assert model.elements_by_name("zzz_nonexistent") == []

    def test_substring_case_sensitive(self, model: Model) -> None:
        result = model.elements_by_name("crm")
        assert result == []

    def test_regex_mode(self, model: Model) -> None:
        result = model.elements_by_name(r"^Business", regex=True)
        assert result == []  # names are "Alice", "Bob", etc., not "BusinessActor"

    def test_regex_case_insensitive(self, model: Model) -> None:
        result = model.elements_by_name(r"(?i)crm", regex=True)
        assert len(result) == 2

    def test_regex_pattern(self, model: Model) -> None:
        result = model.elements_by_name(r"Al(ice|ex)", regex=True)
        assert len(result) == 1
        assert result[0].name == "Alice"

    def test_elements_with_none_name_skipped(self) -> None:
        m = Model()
        m.add(BusinessActor(name="Alice"))
        m.add(BusinessActor())  # name defaults to "" or None
        result = m.elements_by_name("Alice")
        assert len(result) == 1


# -- composition (replaces chained QueryBuilder tests) ------------------------

class TestComposition:
    def test_layer_then_name(self, model: Model) -> None:
        """Compose elements_by_layer + list comprehension for name filter."""
        biz = model.elements_by_layer(Layer.BUSINESS)
        result = [e for e in biz if e.name and "Service" in e.name]
        assert len(result) == 1
        assert result[0].name == "HR Service"

    def test_type_then_aspect(self, model: Model) -> None:
        from pyarchi.metamodel.concepts import Element
        active = model.elements_by_aspect(Aspect.ACTIVE_STRUCTURE)
        biz_active = [e for e in active if getattr(type(e), 'layer', None) is Layer.BUSINESS]
        names = {e.name for e in biz_active}
        assert "Alice" in names
        assert "CRM System" not in names
```
