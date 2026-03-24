# Technical Brief: FEAT-01.1 ConformanceProfile

**Status:** Ready for Implementation
**ADR Link:** `docs/adr/ADR-003-conformance-profile.md`
**Epic:** EPIC-001 -- Scope and Conformance
**Date:** 2026-03-23

---

## 1. Feature Summary

FEAT-01.1 creates the `ConformanceProfile` frozen dataclass in `src/pyarchi/conformance.py`, declaring the library's commitment to implementing specific ArchiMate 3.2 features across three compliance levels: `shall` (mandatory, 12 boolean fields defaulting to `True`), `should` (recommended, 2 boolean fields defaulting to `True`), and `may` (optional, 1 boolean field defaulting to `False`). A module-level singleton `CONFORMANCE` is instantiated with all defaults and re-exported from `pyarchi.__init__`. This profile is the machine-readable contract that the conformance test suite (FEAT-01.2) will assert against, and it must exist before any metamodel types are implemented.

---

## 2. Story-by-Story Implementation Guide

### STORY-01.1.1: Define `ConformanceProfile` dataclass in `src/pyarchi/conformance.py`

**Files to create:**
- `/home/kiera/dev/pyarchi/src/pyarchi/conformance.py`

**Content:** See Section 3 below for the complete file.

**Acceptance Criteria:**
- `src/pyarchi/conformance.py` exists at the package root.
- `ConformanceProfile` is a `@dataclass(frozen=True)`.
- `from pyarchi.conformance import ConformanceProfile, CONFORMANCE` succeeds.
- `CONFORMANCE` is an instance of `ConformanceProfile`.
- The dataclass is frozen: assigning to any field raises `dataclasses.FrozenInstanceError`.
- `mypy src/` reports zero errors.
- `ruff check src/` reports zero violations.

**Gotchas:**
- Do NOT import `SPEC_VERSION` from `pyarchi.__init__`. This would create a circular import since `__init__.py` will import from `conformance.py`. Instead, define `spec_version: str = "3.2"` as a literal field default.
- Use `from __future__ import annotations` to enable PEP 604 union syntax and forward references, even though Python 3.12 supports them natively -- this is a project convention for consistency.

---

### STORY-01.1.2: Include attributes for all conformance features

**Files to modify:** None beyond `conformance.py` (created in STORY-01.1.1).

**Acceptance Criteria:**
- `ConformanceProfile` has exactly 16 fields:
  - 1 `str` field: `spec_version`
  - 12 `bool` fields at `shall` level: `language_structure`, `generic_metamodel`, `strategy_elements`, `motivation_elements`, `business_elements`, `application_elements`, `technology_elements`, `physical_elements`, `implementation_migration_elements`, `cross_layer_relationships`, `relationship_permission_table`, `iconography_metadata`
  - 2 `bool` fields at `should` level: `viewpoint_mechanism`, `language_customization`
  - 1 `bool` field at `may` level: `example_viewpoints`
- All `shall` and `should` fields default to `True`.
- The `may` field defaults to `False`.

**Gotchas:**
- The field order matters for documentation and readability. Group by compliance level with section comments.
- Each field should have an inline docstring comment explaining the ArchiMate feature it represents.

---

### STORY-01.1.3: Add class-level constant `SPEC_VERSION = "3.2"` and expose in `__init__.py`

**Files to modify:**
- `/home/kiera/dev/pyarchi/src/pyarchi/__init__.py` (add imports and update `__all__`)

**Content:** See Section 4 below for the complete updated file.

**Acceptance Criteria:**
- `pyarchi.SPEC_VERSION` returns `"3.2"` (already exists).
- `pyarchi.CONFORMANCE.spec_version` returns `"3.2"`.
- `pyarchi.CONFORMANCE.spec_version == pyarchi.SPEC_VERSION` is `True`.
- Both `ConformanceProfile` and `CONFORMANCE` are in `pyarchi.__all__`.
- `from pyarchi import ConformanceProfile, CONFORMANCE` succeeds.

**Gotchas:**
- `SPEC_VERSION` in `__init__.py` and `spec_version` field default in `conformance.py` are both `"3.2"` as literal strings. They are intentionally independent to avoid circular imports. The conformance test suite (FEAT-01.2) will assert their equality.

---

### STORY-01.1.4: Mark optional features with `may` designation

**Files to modify:** None beyond `conformance.py` (already handled in STORY-01.1.2).

**Acceptance Criteria:**
- `CONFORMANCE.example_viewpoints` is `False`.
- The field has a comment indicating it is `may`-level and does not affect conformance checks.
- No test failure or conformance violation is triggered by `example_viewpoints = False`.

**Gotchas:**
- The `may` designation is purely a documentation convention in the field's comment. There is no runtime enforcement mechanism distinguishing `may` from `shall` or `should` -- the compliance level is encoded in the field grouping and comments, not in the type system.

---

## 3. `src/pyarchi/conformance.py` -- Complete Reference

```python
"""Conformance profile for the pyarchi ArchiMate 3.2 implementation.

This module declares which features of the ArchiMate 3.2 specification the
library commits to implementing.  The :class:`ConformanceProfile` dataclass
carries boolean flags grouped by the specification's three compliance levels:

* **shall** -- mandatory features for a conformant implementation.
* **should** -- recommended features the library plans to support.
* **may** -- optional features explicitly out of scope.

The module-level :data:`CONFORMANCE` singleton is the canonical instance.
It is re-exported from ``pyarchi.__init__`` so consumers can inspect the
library's conformance declaration via ``pyarchi.CONFORMANCE``.

.. note::
   This module does **not** import ``SPEC_VERSION`` from ``pyarchi.__init__``
   to avoid a circular import.  The ``spec_version`` field uses the literal
   ``"3.2"`` as its default.  The conformance test suite asserts that this
   value equals ``pyarchi.SPEC_VERSION``.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__: list[str] = [
    "ConformanceProfile",
    "CONFORMANCE",
]


@dataclass(frozen=True)
class ConformanceProfile:
    """Machine-readable declaration of ArchiMate 3.2 conformance scope.

    Every field defaults to the library's declared intent.  ``shall``-level
    and ``should``-level fields default to ``True`` (the library commits to
    implementing them).  The sole ``may``-level field defaults to ``False``
    (explicitly out of scope).

    The dataclass is frozen to prevent accidental mutation of the library's
    conformance contract.
    """

    # --- spec version ---

    # The ArchiMate specification version this profile targets.
    spec_version: str = "3.2"

    # --- shall-level (mandatory for conformance) ---

    # Full classification framework: layers (7) and aspects (5).
    # Reference: ArchiMate 3.2 Specification, Sections 3.4--3.5.
    language_structure: bool = True

    # Abstract element hierarchy: Concept, Element, Relationship,
    # RelationshipConnector ABCs.
    # Reference: ArchiMate 3.2 Specification, Section 3.1.
    generic_metamodel: bool = True

    # Strategy layer element types: Resource, Capability, ValueStream,
    # CourseOfAction.
    # Reference: ArchiMate 3.2 Specification, Chapter 7.
    strategy_elements: bool = True

    # Motivation layer element types: Stakeholder, Driver, Assessment, Goal,
    # Outcome, Principle, Requirement, Constraint, Meaning, Value.
    # Reference: ArchiMate 3.2 Specification, Chapter 6.
    motivation_elements: bool = True

    # Business layer element types: BusinessActor, BusinessRole,
    # BusinessCollaboration, BusinessInterface, BusinessProcess,
    # BusinessFunction, BusinessInteraction, BusinessEvent,
    # BusinessService, BusinessObject, Contract, Representation, Product.
    # Reference: ArchiMate 3.2 Specification, Chapter 8.
    business_elements: bool = True

    # Application layer element types: ApplicationComponent,
    # ApplicationCollaboration, ApplicationInterface, ApplicationFunction,
    # ApplicationInteraction, ApplicationProcess, ApplicationEvent,
    # ApplicationService, DataObject.
    # Reference: ArchiMate 3.2 Specification, Chapter 9.
    application_elements: bool = True

    # Technology layer element types: Node, Device, SystemSoftware,
    # TechnologyCollaboration, TechnologyInterface, Path,
    # CommunicationNetwork, TechnologyFunction, TechnologyProcess,
    # TechnologyInteraction, TechnologyEvent, TechnologyService, Artifact.
    # Reference: ArchiMate 3.2 Specification, Chapter 10.
    technology_elements: bool = True

    # Physical layer element types: Equipment, Facility,
    # DistributionNetwork, Material.
    # Reference: ArchiMate 3.2 Specification, Chapter 11.
    physical_elements: bool = True

    # Implementation & Migration layer element types: WorkPackage,
    # Deliverable, ImplementationEvent, Plateau, Gap.
    # Reference: ArchiMate 3.2 Specification, Chapter 13.
    implementation_migration_elements: bool = True

    # Support for relationships that cross layer boundaries, including all
    # 11 concrete relationship types and the Junction connector.
    # Reference: ArchiMate 3.2 Specification, Chapter 5.
    cross_layer_relationships: bool = True

    # Full Appendix B relationship permission matrix encoding and the
    # ``is_permitted`` lookup function.
    # Reference: ArchiMate 3.2 Specification, Appendix B.
    relationship_permission_table: bool = True

    # Notation metadata: corner shapes, default layer colors, and badge
    # letters for each concrete element type.
    # Reference: ArchiMate 3.2 Specification, Appendix A.
    iconography_metadata: bool = True

    # --- should-level (recommended, not mandatory) ---

    # Defining and applying viewpoints to filter model views.
    # Reference: ArchiMate 3.2 Specification, Chapter 14.
    viewpoint_mechanism: bool = True

    # Profile and extension mechanisms for customizing the language.
    # Reference: ArchiMate 3.2 Specification, Chapter 15.
    language_customization: bool = True

    # --- may-level (optional, out of scope) ---

    # Appendix C example viewpoints (Basic, Organization, etc.).
    # This feature does not affect conformance checks.
    # Reference: ArchiMate 3.2 Specification, Appendix C.
    example_viewpoints: bool = False


CONFORMANCE: ConformanceProfile = ConformanceProfile()
"""The canonical conformance profile singleton for the pyarchi library.

Query this instance to inspect the library's declared conformance scope::

    >>> from pyarchi import CONFORMANCE
    >>> CONFORMANCE.business_elements
    True
    >>> CONFORMANCE.example_viewpoints
    False
"""
```

---

## 4. Updated `src/pyarchi/__init__.py` -- Complete Reference

```python
"""pyarchi -- Python implementation of the ArchiMate 3.2 metamodel."""

from pyarchi.conformance import CONFORMANCE, ConformanceProfile
from pyarchi.exceptions import (
    ConformanceError,
    DerivationError,
    PyArchiError,
    ValidationError,
)

SPEC_VERSION: str = "3.2"
"""The ArchiMate specification version implemented by this library."""

__all__: list[str] = [
    "SPEC_VERSION",
    # exceptions (FEAT-00.2)
    "PyArchiError",
    "ValidationError",
    "DerivationError",
    "ConformanceError",
    # conformance (FEAT-01.1)
    "ConformanceProfile",
    "CONFORMANCE",
    #
    # EPIC-002: Root Type Hierarchy
    # - Concept, Element, Relationship, RelationshipConnector
    # - AttributeMixin
    # - Model
    #
    # EPIC-003: Language Structure and Classification
    # - Layer, Aspect, NotationMetadata
    #
    # EPIC-004: Generic Metamodel -- Abstract Element Hierarchy
    # - StructureElement, ActiveStructureElement, PassiveStructureElement
    # - BehaviorElement, MotivationElement, CompositeElement
    # - Grouping, Location
    #
    # EPIC-005: Relationships and Relationship Connectors
    # - Composition, Aggregation, Assignment, Realization
    # - Serving, Access, Influence, Association
    # - Triggering, Flow, Specialization
    # - Junction
    # - DerivationEngine
]
```

---

## 5. Verification Checklist

Run these commands sequentially from the repository root after completing all four stories. Every command must exit with code 0.

```bash
# 0. Activate the virtual environment
source .venv/bin/activate

# 1. Verify conformance.py is importable
python -c "from pyarchi.conformance import ConformanceProfile, CONFORMANCE; print('OK: conformance module')"

# 2. Verify CONFORMANCE is a ConformanceProfile instance
python -c "from pyarchi import CONFORMANCE, ConformanceProfile; assert isinstance(CONFORMANCE, ConformanceProfile); print('OK: isinstance')"

# 3. Verify spec_version consistency
python -c "from pyarchi import CONFORMANCE, SPEC_VERSION; assert CONFORMANCE.spec_version == SPEC_VERSION == '3.2'; print('OK: spec_version')"

# 4. Verify all shall-level fields are True
python -c "
from pyarchi import CONFORMANCE
shall_fields = [
    'language_structure', 'generic_metamodel', 'strategy_elements',
    'motivation_elements', 'business_elements', 'application_elements',
    'technology_elements', 'physical_elements',
    'implementation_migration_elements', 'cross_layer_relationships',
    'relationship_permission_table', 'iconography_metadata',
]
for f in shall_fields:
    assert getattr(CONFORMANCE, f) is True, f'{f} is not True'
print('OK: all shall fields True')
"

# 5. Verify should-level fields are True
python -c "from pyarchi import CONFORMANCE; assert CONFORMANCE.viewpoint_mechanism is True; assert CONFORMANCE.language_customization is True; print('OK: should fields True')"

# 6. Verify may-level field is False
python -c "from pyarchi import CONFORMANCE; assert CONFORMANCE.example_viewpoints is False; print('OK: may field False')"

# 7. Verify frozen
python -c "
import dataclasses
from pyarchi import CONFORMANCE
try:
    CONFORMANCE.language_structure = False
    raise AssertionError('Should have raised FrozenInstanceError')
except dataclasses.FrozenInstanceError:
    print('OK: frozen')
"

# 8. Verify __all__ exports
python -c "import pyarchi; assert 'ConformanceProfile' in pyarchi.__all__; assert 'CONFORMANCE' in pyarchi.__all__; print('OK: __all__')"

# 9. Ruff linter -- zero violations
ruff check src/ test/

# 10. Ruff formatter -- zero violations
ruff format --check src/ test/

# 11. mypy strict -- zero errors
mypy src/

# 12. pytest -- existing tests pass
pytest
```
