# Technical Brief: FEAT-18.1 -- Profile Class + Element Field Additions

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-030-epic018-language-customization.md`
**Backlog:** STORY-18.1.1 through STORY-18.1.6

---

## 1. Implementation Scope

### 1a. New File: `src/pyarchi/metamodel/profiles.py`

| Item | Detail |
|---|---|
| Class | `Profile(pydantic.BaseModel)` -- NOT a Concept |
| Pattern | Mirrors `Viewpoint` in `viewpoints.py` |

```python
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from pyarchi.metamodel.concepts import Element


class Profile(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    specializations: dict[type[Element], list[str]] = Field(default_factory=dict)
    attribute_extensions: dict[type[Element], dict[str, type]] = Field(default_factory=dict)
```

**No `__all__` export changes.** Exports are deferred to EPIC-020.

### 1b. Modified File: `src/pyarchi/metamodel/concepts.py`

Add two fields to `Element`:

```python
class Element(AttributeMixin, Concept):
    specialization: str | None = None
    extended_attributes: dict[str, Any] = Field(default_factory=dict)
```

| Field | Type | Default | Purpose |
|---|---|---|---|
| `specialization` | `str \| None` | `None` | Tag-based specialization name |
| `extended_attributes` | `dict[str, Any]` | `{}` | Profile-declared custom attributes |

**Import addition:** `from typing import Any` (add to existing imports).

### 1c. Existing-Test Impact

Adding fields to `Element` does NOT break `extra="forbid"` because the fields become part of the schema. However:

| Risk | Mitigation |
|---|---|
| Tests asserting exact `model_dump()` key sets | None found; low risk |
| Tests asserting exact `model_fields` count | None found on Element; low risk |
| `RelationshipConnector` inherits from `Concept`, not `Element` | No impact -- new fields are on `Element` only |

---

## 2. Validation Logic

**FEAT-18.1 has NO construction-time validation on Profile.** Validation is FEAT-18.2 scope. This feature only ensures the class can be instantiated and the fields accept correct types.

| Rule | Enforcement | Feature |
|---|---|---|
| `name` must be `str` | Pydantic type coercion | 18.1 |
| `specializations` keys must be `type[Element]` | Deferred to FEAT-18.2 | 18.2 |
| No field name conflicts | Deferred to FEAT-18.2 | 18.2 |

---

## 3. Test File: `test/test_feat181_profile_class.py`

```python
"""Tests for FEAT-18.1: Profile class and Element field additions."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from pyarchi.metamodel.concepts import Element
from pyarchi.metamodel.profiles import Profile


# ---------------------------------------------------------------------------
# Helpers -- concrete Element stub for testing
# ---------------------------------------------------------------------------

class _StubElement(Element):
    @property
    def _type_name(self) -> str:
        return "StubElement"


# ===========================================================================
# Profile instantiation
# ===========================================================================


class TestProfileInstantiation:
    """STORY-18.1.1: Profile can be instantiated."""

    def test_minimal_profile(self) -> None:
        """Profile with only a name and empty defaults."""
        p = Profile(name="Empty")
        assert p.name == "Empty"
        assert p.specializations == {}
        assert p.attribute_extensions == {}

    def test_profile_with_specializations(self) -> None:
        """STORY-18.1.5: Profile with custom specializations."""
        p = Profile(
            name="Cloud",
            specializations={_StubElement: ["Microservice", "Serverless"]},
        )
        assert _StubElement in p.specializations
        assert p.specializations[_StubElement] == ["Microservice", "Serverless"]

    def test_profile_with_attribute_extensions(self) -> None:
        """STORY-18.1.6: Profile with attribute extensions."""
        p = Profile(
            name="Costing",
            attribute_extensions={_StubElement: {"cost": float, "owner": str}},
        )
        assert p.attribute_extensions[_StubElement] == {"cost": float, "owner": str}

    def test_profile_with_both(self) -> None:
        """Profile carrying specializations and attribute extensions together."""
        p = Profile(
            name="Full",
            specializations={_StubElement: ["Alpha"]},
            attribute_extensions={_StubElement: {"score": int}},
        )
        assert p.specializations[_StubElement] == ["Alpha"]
        assert p.attribute_extensions[_StubElement] == {"score": int}

    def test_profile_is_not_concept(self) -> None:
        """Profile does not inherit from Concept."""
        from pyarchi.metamodel.concepts import Concept

        p = Profile(name="Test")
        assert not isinstance(p, Concept)

    def test_profile_has_no_id_field(self) -> None:
        """Profile must not expose an 'id' field."""
        assert "id" not in Profile.model_fields


# ===========================================================================
# Element field additions
# ===========================================================================


class TestElementSpecializationField:
    """STORY-18.1.1 (Element side): specialization field on Element."""

    def test_default_is_none(self) -> None:
        e = _StubElement(name="plain")
        assert e.specialization is None

    def test_accepts_string(self) -> None:
        e = _StubElement(name="ms", specialization="Microservice")
        assert e.specialization == "Microservice"

    def test_in_model_fields(self) -> None:
        assert "specialization" in _StubElement.model_fields

    def test_in_model_dump(self) -> None:
        e = _StubElement(name="x", specialization="Foo")
        dump = e.model_dump()
        assert dump["specialization"] == "Foo"

    def test_none_in_model_dump(self) -> None:
        e = _StubElement(name="x")
        dump = e.model_dump()
        assert dump["specialization"] is None


class TestElementExtendedAttributesField:
    """STORY-18.1.1 (Element side): extended_attributes field on Element."""

    def test_default_is_empty_dict(self) -> None:
        e = _StubElement(name="plain")
        assert e.extended_attributes == {}

    def test_accepts_dict(self) -> None:
        e = _StubElement(name="x", extended_attributes={"cost": 42.0})
        assert e.extended_attributes == {"cost": 42.0}

    def test_in_model_fields(self) -> None:
        assert "extended_attributes" in _StubElement.model_fields

    def test_in_model_dump(self) -> None:
        e = _StubElement(name="x", extended_attributes={"k": "v"})
        dump = e.model_dump()
        assert dump["extended_attributes"] == {"k": "v"}

    def test_empty_in_model_dump(self) -> None:
        e = _StubElement(name="x")
        dump = e.model_dump()
        assert dump["extended_attributes"] == {}
```

---

## 4. Files Changed Summary

| File | Action |
|---|---|
| `src/pyarchi/metamodel/profiles.py` | **Create** -- `Profile` class |
| `src/pyarchi/metamodel/concepts.py` | **Modify** -- add `specialization`, `extended_attributes` to `Element`; add `Any` import |
| `test/test_feat181_profile_class.py` | **Create** -- test file above |
