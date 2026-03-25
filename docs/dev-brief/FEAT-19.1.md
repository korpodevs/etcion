# Technical Brief: FEAT-19.1 XML Namespace, Schema Setup, and TypeRegistry

**Status:** Ready for TDD
**ADR:** `docs/adr/ADR-031-epic019-serialization.md`
**Epic:** EPIC-019

---

## Feature Summary

Create the `src/pyarchi/serialization/` package with `__init__.py` and `registry.py`. Define Exchange Format namespace constants, the `TypeDescriptor` dataclass, and the `TypeRegistry` mapping all concrete `Concept` subclasses to their XML tag names. Add the `[xml]` optional dependency to `pyproject.toml`. Add `lxml` to the `[dev]` extra so tests can run.

## Dependencies

| Dependency | Status |
|---|---|
| All concrete Element types (EPIC-004 through EPIC-014) | Done |
| All concrete Relationship types (EPIC-005) | Done |
| ADR-031 Decisions 1, 2, 3 | Accepted |

## Stories -> Acceptance

| Story | Deliverable | Acceptance |
|---|---|---|
| 19.1.1 | Namespace constants in `registry.py` | `ARCHIMATE_NS`, `XSI_NS`, `ARCHIMATE_SCHEMA_LOCATION` strings match Exchange Format spec |
| 19.1.2 | XSD reference path constant | `XSD_PATH` points to `serialization/schema/` (file bundling deferred to FEAT-19.6) |
| 19.1.3 | `TypeDescriptor` dataclass | Fields: `xml_tag: str`, `extra_attrs: dict[str, Callable]` (attribute extractors for type-specific fields) |
| 19.1.4 | `TYPE_REGISTRY: dict[type[Concept], TypeDescriptor]` | Contains all 57 concrete types (elements + relationships + Junction) |
| 19.1.5 | `[xml]` extra in `pyproject.toml` | `lxml>=5.0,<6.0`; also added to `[dev]` |
| 19.1.6 | Tests | All stories verified |

## pyproject.toml Changes

```toml
[project.optional-dependencies]
xml = ["lxml>=5.0,<6.0"]
dev = [
    "pytest>=8.0",
    "mypy>=1.10",
    "pydantic>=2.0,<3.0",
    "ruff>=0.4",
    "lxml>=5.0,<6.0",
]
```

**Note:** `lxml` is NOT currently in `[dev]`. It must be added so XML tests can run without `pytest.importorskip`.

## Implementation

### New File: `src/pyarchi/serialization/__init__.py`

```python
"""Serialization subsystem for pyarchi."""
```

### New File: `src/pyarchi/serialization/registry.py`

```python
"""External TypeRegistry mapping Concept subclasses to XML descriptors.

Reference: ADR-031 Decision 3.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from pyarchi.metamodel.concepts import Concept

# -- Exchange Format namespace constants (Decision 1) --
ARCHIMATE_NS = "http://www.opengroup.org/xsd/archimate/3.0/"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
ARCHIMATE_SCHEMA_LOCATION = (
    "http://www.opengroup.org/xsd/archimate/3.0/ "
    "http://www.opengroup.org/xsd/archimate/3.1/archimate3_Diagram.xsd"
)
NSMAP: dict[str | None, str] = {
    None: ARCHIMATE_NS,
    "xsi": XSI_NS,
}


@dataclass(frozen=True, slots=True)
class TypeDescriptor:
    """Maps a Concept subclass to its Exchange Format XML representation."""

    xml_tag: str
    extra_attrs: dict[str, Callable[[Any], str | None]] = field(default_factory=dict)


def _enum_val(obj: Any, attr: str) -> str | None:
    v = getattr(obj, attr, None)
    return v.value if v is not None else None


TYPE_REGISTRY: dict[type[Concept], TypeDescriptor] = {}


def _register_all() -> None:
    """Populate TYPE_REGISTRY with all concrete types."""
    # -- Elements (no extra_attrs) --
    from pyarchi.metamodel.business import (
        BusinessActor, BusinessRole, BusinessCollaboration,
        BusinessInterface, BusinessProcess, BusinessFunction,
        BusinessInteraction, BusinessEvent, BusinessService,
        BusinessObject, Contract, Representation, Product,
    )
    from pyarchi.metamodel.application import (
        ApplicationComponent, ApplicationCollaboration,
        ApplicationInterface, ApplicationFunction,
        ApplicationInteraction, ApplicationProcess,
        ApplicationEvent, ApplicationService, DataObject,
    )
    from pyarchi.metamodel.technology import (
        Node, Device, SystemSoftware, TechnologyCollaboration,
        TechnologyInterface, Path, CommunicationNetwork,
        TechnologyFunction, TechnologyProcess, TechnologyInteraction,
        TechnologyEvent, TechnologyService, Artifact,
    )
    from pyarchi.metamodel.physical import (
        Equipment, Facility, DistributionNetwork, Material,
    )
    from pyarchi.metamodel.strategy import (
        Resource, Capability, ValueStream, CourseOfAction,
    )
    from pyarchi.metamodel.motivation import (
        Stakeholder, Driver, Assessment, Goal, Outcome,
        Principle, Requirement, Constraint, Meaning, Value,
    )
    from pyarchi.metamodel.implementation_migration import (
        WorkPackage, Deliverable, ImplementationEvent, Plateau, Gap,
    )
    from pyarchi.metamodel.elements import Grouping, Location
    from pyarchi.metamodel.relationships import (
        Composition, Aggregation, Assignment, Realization,
        Serving, Access, Influence, Association,
        Triggering, Flow, Specialization, Junction,
    )

    # All element types: tag = _type_name, no extra attrs
    _simple: list[type[Concept]] = [
        BusinessActor, BusinessRole, BusinessCollaboration,
        BusinessInterface, BusinessProcess, BusinessFunction,
        BusinessInteraction, BusinessEvent, BusinessService,
        BusinessObject, Contract, Representation, Product,
        ApplicationComponent, ApplicationCollaboration,
        ApplicationInterface, ApplicationFunction,
        ApplicationInteraction, ApplicationProcess,
        ApplicationEvent, ApplicationService, DataObject,
        Node, Device, SystemSoftware, TechnologyCollaboration,
        TechnologyInterface, Path, CommunicationNetwork,
        TechnologyFunction, TechnologyProcess, TechnologyInteraction,
        TechnologyEvent, TechnologyService, Artifact,
        Equipment, Facility, DistributionNetwork, Material,
        Resource, Capability, ValueStream, CourseOfAction,
        Stakeholder, Driver, Assessment, Goal, Outcome,
        Principle, Requirement, Constraint, Meaning, Value,
        WorkPackage, Deliverable, ImplementationEvent, Plateau, Gap,
        Grouping, Location,
        # Simple relationships (no extra attrs beyond source/target)
        Composition, Aggregation, Assignment, Realization,
        Serving, Triggering, Specialization,
    ]
    for cls in _simple:
        TYPE_REGISTRY[cls] = TypeDescriptor(xml_tag=cls.__name__)

    # Relationships with extra attrs
    TYPE_REGISTRY[Access] = TypeDescriptor(
        xml_tag="Access",
        extra_attrs={"accessType": lambda r: _enum_val(r, "access_mode")},
    )
    TYPE_REGISTRY[Influence] = TypeDescriptor(
        xml_tag="Influence",
        extra_attrs={
            "modifier": lambda r: _enum_val(r, "sign"),
            "strength": lambda r: r.strength,
        },
    )
    TYPE_REGISTRY[Association] = TypeDescriptor(
        xml_tag="Association",
        extra_attrs={"isDirected": lambda r: str(r.direction.value == "Directed").lower()},
    )
    TYPE_REGISTRY[Flow] = TypeDescriptor(
        xml_tag="Flow",
        extra_attrs={"flowType": lambda r: r.flow_type},
    )
    TYPE_REGISTRY[Junction] = TypeDescriptor(
        xml_tag="Junction",
        extra_attrs={"type": lambda j: j.junction_type.value},
    )


_register_all()
```

**Key design note:** `_type_name` is a property on instances, but the registry uses `cls.__name__` which happens to match `_type_name` for all current concrete types. The registry key is the class itself (`type[Concept]`), looked up via `type(concept)`.

## Test File: `test/test_feat191_registry.py`

```python
"""Tests for FEAT-19.1 -- XML namespace constants and TypeRegistry."""
from __future__ import annotations

import pytest

from pyarchi.serialization.registry import (
    ARCHIMATE_NS,
    NSMAP,
    TYPE_REGISTRY,
    TypeDescriptor,
    XSI_NS,
)


class TestNamespaceConstants:
    def test_archimate_ns_is_opengroup_uri(self):
        assert "opengroup.org" in ARCHIMATE_NS
        assert "archimate" in ARCHIMATE_NS

    def test_xsi_ns(self):
        assert XSI_NS == "http://www.w3.org/2001/XMLSchema-instance"

    def test_nsmap_default_key(self):
        assert None in NSMAP
        assert NSMAP[None] == ARCHIMATE_NS


class TestTypeDescriptor:
    def test_frozen(self):
        td = TypeDescriptor(xml_tag="Foo")
        with pytest.raises(AttributeError):
            td.xml_tag = "Bar"  # type: ignore[misc]

    def test_extra_attrs_default_empty(self):
        td = TypeDescriptor(xml_tag="Foo")
        assert td.extra_attrs == {}


class TestTypeRegistry:
    def test_registry_is_not_empty(self):
        assert len(TYPE_REGISTRY) > 0

    def test_all_element_types_registered(self):
        from pyarchi.metamodel.business import BusinessActor
        from pyarchi.metamodel.application import DataObject
        from pyarchi.metamodel.technology import Artifact
        from pyarchi.metamodel.motivation import Goal
        from pyarchi.metamodel.strategy import Capability
        from pyarchi.metamodel.physical import Equipment
        from pyarchi.metamodel.implementation_migration import Plateau
        from pyarchi.metamodel.elements import Grouping

        for cls in [BusinessActor, DataObject, Artifact, Goal, Capability,
                    Equipment, Plateau, Grouping]:
            assert cls in TYPE_REGISTRY, f"{cls.__name__} not in registry"

    def test_all_relationship_types_registered(self):
        from pyarchi.metamodel.relationships import (
            Composition, Access, Influence, Flow, Junction,
        )
        for cls in [Composition, Access, Influence, Flow, Junction]:
            assert cls in TYPE_REGISTRY, f"{cls.__name__} not in registry"

    def test_access_has_extra_attrs(self):
        from pyarchi.metamodel.relationships import Access
        desc = TYPE_REGISTRY[Access]
        assert "accessType" in desc.extra_attrs

    def test_influence_has_modifier_and_strength(self):
        from pyarchi.metamodel.relationships import Influence
        desc = TYPE_REGISTRY[Influence]
        assert "modifier" in desc.extra_attrs
        assert "strength" in desc.extra_attrs

    def test_junction_has_type_attr(self):
        from pyarchi.metamodel.relationships import Junction
        desc = TYPE_REGISTRY[Junction]
        assert "type" in desc.extra_attrs

    def test_registry_count_at_least_57(self):
        """57 concrete types: ~52 elements + ~12 relationships/junction - overlaps."""
        assert len(TYPE_REGISTRY) >= 57

    def test_xml_tag_matches_class_name_for_simple_types(self):
        from pyarchi.metamodel.business import BusinessActor
        assert TYPE_REGISTRY[BusinessActor].xml_tag == "BusinessActor"
```

## Verification

```bash
source .venv/bin/activate
pip install -e ".[dev]"
ruff check src/pyarchi/serialization/ test/test_feat191_registry.py
ruff format --check src/pyarchi/serialization/ test/test_feat191_registry.py
mypy src/pyarchi/serialization/registry.py
pytest test/test_feat191_registry.py -v
```
