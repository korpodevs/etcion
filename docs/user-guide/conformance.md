# Conformance Profiles

ArchiMate 3.2 defines three compliance levels for tools and libraries: features they **shall** implement (mandatory), **should** implement (recommended), and **may** implement (optional). etcion exposes its conformance declaration as a first-class Python object so that consuming code can inspect and assert it programmatically.

## What is ConformanceProfile?

`ConformanceProfile` is a frozen dataclass that carries boolean flags for every feature etcion commits to implementing. The flags are grouped into three compliance levels:

- **shall** -- mandatory features. All 12 shall-level flags default to `True`.
- **should** -- recommended features. Both should-level flags default to `True`.
- **may** -- optional features that are explicitly out of scope. The sole may-level flag defaults to `False`.

The dataclass is frozen, which means its fields cannot be reassigned after construction. This preserves the library's conformance contract as an immutable record.

```python
from etcion import ConformanceProfile

profile = ConformanceProfile()
print(profile.spec_version)               # "3.2"
print(profile.language_structure)         # True  (shall-level)
print(profile.viewpoint_mechanism)        # True  (should-level)
print(profile.example_viewpoints)         # False (may-level)
```

The full list of fields is documented in the [API reference](../api/index.md).

## The CONFORMANCE Singleton

`CONFORMANCE` is the canonical, pre-constructed instance of `ConformanceProfile`. It is the library's public declaration of what it implements. Import it directly from `etcion`:

```python
import etcion

print(etcion.CONFORMANCE.spec_version)    # "3.2"
print(etcion.CONFORMANCE.generic_metamodel)  # True
```

`CONFORMANCE.spec_version` always equals `etcion.SPEC_VERSION`:

```python
assert etcion.CONFORMANCE.spec_version == etcion.SPEC_VERSION
```

You can also import both names explicitly:

```python
from etcion import CONFORMANCE, SPEC_VERSION

assert CONFORMANCE.spec_version == SPEC_VERSION  # always True
```

## Feature Flags

Each field on `ConformanceProfile` corresponds to one feature group from the ArchiMate 3.2 specification. The table below lists every flag, its compliance level, and the relevant spec section.

### shall-level (mandatory)

| Flag | Spec reference | Default |
|------|---------------|---------|
| `language_structure` | Sections 3.4--3.5: 7 layers, 5 aspects | `True` |
| `generic_metamodel` | Section 3.1: Concept, Element, Relationship, RelationshipConnector ABCs | `True` |
| `strategy_elements` | Chapter 7: Resource, Capability, ValueStream, CourseOfAction | `True` |
| `motivation_elements` | Chapter 6: Stakeholder, Driver, Assessment, Goal, Outcome, Principle, Requirement, Constraint, Meaning, Value | `True` |
| `business_elements` | Chapter 8: BusinessActor, BusinessRole, ... Product (13 types) | `True` |
| `application_elements` | Chapter 9: ApplicationComponent, ... DataObject (9 types) | `True` |
| `technology_elements` | Chapter 10: Node, Device, ... Artifact (13 types) | `True` |
| `physical_elements` | Chapter 11: Equipment, Facility, DistributionNetwork, Material | `True` |
| `implementation_migration_elements` | Chapter 13: WorkPackage, Deliverable, ImplementationEvent, Plateau, Gap | `True` |
| `cross_layer_relationships` | Chapter 5: 11 relationship types + Junction | `True` |
| `relationship_permission_table` | Appendix B: permission matrix + `is_permitted()` | `True` |
| `iconography_metadata` | Appendix A: corner shapes, layer colors, badge letters | `True` |

### should-level (recommended)

| Flag | Spec reference | Default |
|------|---------------|---------|
| `viewpoint_mechanism` | Chapter 14: defining and applying viewpoints | `True` |
| `language_customization` | Chapter 15: Profiles and extension mechanisms | `True` |

### may-level (optional, out of scope)

| Flag | Spec reference | Default |
|------|---------------|---------|
| `example_viewpoints` | Appendix C: Basic, Organization, and other named example viewpoints | `False` |

Inspect all flags at once using `dataclasses.asdict()`:

```python
import dataclasses
from etcion import CONFORMANCE

for field, value in dataclasses.asdict(CONFORMANCE).items():
    print(f"{field}: {value}")
```

## Validation

### Asserting conformance in your code

Because `ConformanceProfile` is a plain dataclass, asserting feature availability is a straightforward attribute check:

```python
from etcion import CONFORMANCE

if not CONFORMANCE.relationship_permission_table:
    raise RuntimeError("etcion does not implement the permission table in this build")
```

For test suites, assert directly:

```python
from etcion import CONFORMANCE

def test_permission_table_is_supported():
    assert CONFORMANCE.relationship_permission_table is True

def test_example_viewpoints_are_out_of_scope():
    assert CONFORMANCE.example_viewpoints is False
```

### Verifying spec version alignment

`CONFORMANCE.spec_version` lets you guard code that depends on a specific ArchiMate version:

```python
from etcion import CONFORMANCE

REQUIRED_VERSION = "3.2"
if CONFORMANCE.spec_version != REQUIRED_VERSION:
    raise RuntimeError(
        f"This code requires ArchiMate {REQUIRED_VERSION}, "
        f"but etcion targets {CONFORMANCE.spec_version}"
    )
```

### Constructing a custom profile for testing

`ConformanceProfile` is frozen but not a singleton. You can construct a fresh instance with different flag values to test code that branches on feature availability:

```python
from etcion import ConformanceProfile

# Simulate a build that has not yet implemented the viewpoint mechanism
partial = ConformanceProfile(viewpoint_mechanism=False)
assert partial.viewpoint_mechanism is False

# The global singleton is unaffected
from etcion import CONFORMANCE
assert CONFORMANCE.viewpoint_mechanism is True
```

This pattern is useful in unit tests that need to probe feature-conditional logic without modifying the library's own declaration.

### Immutability guarantee

Attempting to set any field on `CONFORMANCE` raises `dataclasses.FrozenInstanceError`:

```python
import dataclasses
from etcion import CONFORMANCE

try:
    CONFORMANCE.language_structure = False  # type: ignore[misc]
except dataclasses.FrozenInstanceError:
    print("ConformanceProfile is immutable")
```

## Common Patterns

### Listing all unsupported features

```python
import dataclasses
from etcion import CONFORMANCE

unsupported = [
    field.name
    for field in dataclasses.fields(CONFORMANCE)
    if field.name != "spec_version" and not getattr(CONFORMANCE, field.name)
]
print("Out-of-scope features:", unsupported)
# Out-of-scope features: ['example_viewpoints']
```

### Logging the conformance summary on startup

```python
import dataclasses
import logging
from etcion import CONFORMANCE

logger = logging.getLogger(__name__)

def log_conformance_summary() -> None:
    logger.info("etcion ArchiMate conformance: spec_version=%s", CONFORMANCE.spec_version)
    for field in dataclasses.fields(CONFORMANCE):
        if field.name == "spec_version":
            continue
        value = getattr(CONFORMANCE, field.name)
        level = "SUPPORTED" if value else "OUT_OF_SCOPE"
        logger.debug("  %-40s %s", field.name, level)
```

### Checking a specific feature flag before calling an API

```python
from etcion import CONFORMANCE, is_permitted, Serving, ApplicationService, BusinessService

if CONFORMANCE.relationship_permission_table:
    allowed = is_permitted(Serving, ApplicationService, BusinessService)
    print(f"Serving ApplicationService -> BusinessService: {allowed}")
```

## API Summary

| Name | Kind | Description |
|------|------|-------------|
| `ConformanceProfile` | frozen dataclass | Machine-readable conformance declaration with 16 fields |
| `CONFORMANCE` | `ConformanceProfile` instance | Canonical singleton; re-exported from `etcion` |
| `ConformanceProfile.spec_version` | `str` | ArchiMate spec version targeted (`"3.2"`) |
| `ConformanceProfile.language_structure` | `bool` | 7 layers and 5 aspects |
| `ConformanceProfile.generic_metamodel` | `bool` | Abstract element hierarchy ABCs |
| `ConformanceProfile.strategy_elements` | `bool` | Strategy layer types |
| `ConformanceProfile.motivation_elements` | `bool` | Motivation layer types |
| `ConformanceProfile.business_elements` | `bool` | Business layer types |
| `ConformanceProfile.application_elements` | `bool` | Application layer types |
| `ConformanceProfile.technology_elements` | `bool` | Technology layer types |
| `ConformanceProfile.physical_elements` | `bool` | Physical layer types |
| `ConformanceProfile.implementation_migration_elements` | `bool` | Implementation & Migration layer types |
| `ConformanceProfile.cross_layer_relationships` | `bool` | All 11 relationship types + Junction |
| `ConformanceProfile.relationship_permission_table` | `bool` | Appendix B matrix + `is_permitted()` |
| `ConformanceProfile.iconography_metadata` | `bool` | Notation shapes, colors, and badge letters |
| `ConformanceProfile.viewpoint_mechanism` | `bool` | Viewpoint definition and application |
| `ConformanceProfile.language_customization` | `bool` | Profiles and extension mechanisms |
| `ConformanceProfile.example_viewpoints` | `bool` | Appendix C named viewpoints (out of scope, `False`) |

See also: [API reference](../api/index.md)
