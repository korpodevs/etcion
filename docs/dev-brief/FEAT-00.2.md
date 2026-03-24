# Technical Brief: FEAT-00.2 Module Layout

**Status:** Ready for Implementation
**ADR Link:** `docs/adr/ADR-002-module-layout.md`
**Epic:** EPIC-000 -- Project Scaffold and Build System
**Date:** 2026-03-23

---

## 1. Feature Summary

FEAT-00.2 creates the internal module structure of the `pyarchi` package: the `metamodel/`, `validation/`, and `derivation/` sub-packages, a centralized `enums.py` with all seven ArchiMate enumerations fully defined, and an `exceptions.py` with the four-class exception hierarchy. This feature must be completed before any metamodel work in EPIC-002+ because every subsequent class, validator, and test depends on these import paths. The module layout establishes a strict one-way dependency graph (`exceptions`/`enums` -> `metamodel` -> `validation` -> `derivation`) that prevents circular imports by construction.

---

## 2. Story-by-Story Implementation Guide

### STORY-00.2.1: Create `src/pyarchi/metamodel/` Sub-package

**Files to create:**

1. `src/pyarchi/metamodel/__init__.py`
2. `src/pyarchi/metamodel/concepts.py`
3. `src/pyarchi/metamodel/mixins.py`
4. `src/pyarchi/metamodel/model.py`
5. `src/pyarchi/metamodel/notation.py`

**File contents:**

`src/pyarchi/metamodel/__init__.py`:
```python
"""pyarchi.metamodel -- ArchiMate 3.2 metamodel type hierarchy.

This sub-package contains the abstract base classes, mixins, concrete element
types, concrete relationship types, and the Model container that together
implement the ArchiMate 3.2 metamodel.

Re-exports will be added here as types are implemented in subsequent epics.
"""

# Re-exports will be added as types are implemented:
# EPIC-002: Concept, Element, Relationship, RelationshipConnector, AttributeMixin, Model
# EPIC-003: NotationMetadata
# EPIC-004: StructureElement, ActiveStructureElement, BehaviorElement, etc.
# EPIC-005: Composition, Aggregation, Serving, etc.
```

`src/pyarchi/metamodel/concepts.py`:
```python
"""Abstract base classes for the ArchiMate 3.2 concept hierarchy.

Defines the root ``Concept`` ABC and its direct abstract subtypes:
``Element``, ``Relationship``, and ``RelationshipConnector``.
"""

# TODO: EPIC-002
```

`src/pyarchi/metamodel/mixins.py`:
```python
"""Mixins providing shared attribute sets for metamodel types.

Defines ``AttributeMixin`` with ``name``, ``description``, and
``documentation_url`` fields shared by both elements and relationships.
"""

# TODO: EPIC-002
```

`src/pyarchi/metamodel/model.py`:
```python
"""The Model container class.

Defines the top-level ``Model`` that holds all ``Concept`` instances
(elements, relationships, and relationship connectors) and provides
traversal and lookup methods.
"""

# TODO: EPIC-002
```

`src/pyarchi/metamodel/notation.py`:
```python
"""Notation metadata for ArchiMate element visualization.

Defines ``NotationMetadata`` capturing corner shape, layer color, and
badge letter for each concrete element type.
"""

# TODO: EPIC-003
```

**Acceptance Criteria:**
- All five files exist under `src/pyarchi/metamodel/`.
- `python -c "import pyarchi.metamodel"` succeeds.
- `mypy src/` reports zero errors.
- `ruff check src/` reports zero violations.

**Gotchas:**
- Do NOT add any imports to `metamodel/__init__.py` yet. There is nothing to import -- the sub-modules are stubs. Importing from empty stub modules would cause `ImportError` or mypy errors.
- The `__init__.py` must exist (even if it contains only a docstring and comments) to make the directory a Python package. Without it, `import pyarchi.metamodel` will fail.
- Ruff's `I` (isort) rules will flag unused imports. Since we add no imports, this is not a concern at this stage.

---

### STORY-00.2.2: Create `src/pyarchi/enums.py`

**Files to create:**

1. `src/pyarchi/enums.py`

**File content:**

```python
"""Enumeration types for the ArchiMate 3.2 metamodel.

All enumerations used across the pyarchi library are centralized in this
module to keep them at the bottom of the dependency graph, importable by
any sub-package without circular import risk.
"""

from enum import Enum


class Layer(Enum):
    """The seven layers of the ArchiMate 3.2 framework.

    Reference: ArchiMate 3.2 Specification, Section 3.4.
    """

    STRATEGY = "Strategy"
    MOTIVATION = "Motivation"
    BUSINESS = "Business"
    APPLICATION = "Application"
    TECHNOLOGY = "Technology"
    PHYSICAL = "Physical"
    IMPLEMENTATION_MIGRATION = "Implementation and Migration"


class Aspect(Enum):
    """The five aspects (columns) of the ArchiMate 3.2 framework.

    Reference: ArchiMate 3.2 Specification, Section 3.5.
    """

    ACTIVE_STRUCTURE = "Active Structure"
    BEHAVIOR = "Behavior"
    PASSIVE_STRUCTURE = "Passive Structure"
    MOTIVATION = "Motivation"
    COMPOSITE = "Composite"


class RelationshipCategory(Enum):
    """The four categories of ArchiMate relationships.

    Reference: ArchiMate 3.2 Specification, Section 5.1.
    """

    STRUCTURAL = "Structural"
    DEPENDENCY = "Dependency"
    DYNAMIC = "Dynamic"
    OTHER = "Other"


class AccessMode(Enum):
    """Access modes for the Access relationship.

    Reference: ArchiMate 3.2 Specification, Section 5.2.3.
    """

    READ = "Read"
    WRITE = "Write"
    READ_WRITE = "ReadWrite"
    UNSPECIFIED = "Unspecified"


class InfluenceSign(Enum):
    """Influence strength/direction signs for the Influence relationship.

    The string values use the notation from the ArchiMate specification.

    Reference: ArchiMate 3.2 Specification, Section 5.2.4.
    """

    STRONG_POSITIVE = "++"
    POSITIVE = "+"
    NEUTRAL = "0"
    NEGATIVE = "-"
    STRONG_NEGATIVE = "--"


class AssociationDirection(Enum):
    """Directionality of an Association relationship.

    Reference: ArchiMate 3.2 Specification, Section 5.2.5.
    """

    UNDIRECTED = "Undirected"
    DIRECTED = "Directed"


class JunctionType(Enum):
    """Junction connector types.

    Reference: ArchiMate 3.2 Specification, Section 5.3.
    """

    AND = "And"
    OR = "Or"
```

**Acceptance Criteria:**
- `from pyarchi.enums import Layer, Aspect, RelationshipCategory, AccessMode, InfluenceSign, AssociationDirection, JunctionType` succeeds.
- `Layer` has exactly 7 members.
- `Aspect` has exactly 5 members.
- `RelationshipCategory` has exactly 4 members.
- `AccessMode` has exactly 4 members.
- `InfluenceSign` has exactly 5 members, with values `"++"`, `"+"`, `"0"`, `"-"`, `"--"`.
- `AssociationDirection` has exactly 2 members.
- `JunctionType` has exactly 2 members.
- `mypy src/` reports zero errors.
- `ruff check src/` reports zero violations.

**Gotchas:**
- Use `enum.Enum`, not `enum.StrEnum`. While `StrEnum` would allow direct string comparison (`InfluenceSign.POSITIVE == "+"`), the ArchiMate spec treats these as typed labels, not interchangeable strings. Using `Enum` enforces explicit `.value` access and prevents accidental string comparison, which is the safer default for a typed library.
- `InfluenceSign` members use punctuation characters as values (`"++"`, `"--"`). These are valid Python string literals and valid `Enum` values. No special handling is needed.
- The `IMPLEMENTATION_MIGRATION` layer uses an underscore in the member name but `"Implementation and Migration"` as the string value. This matches the spec's prose name.

---

### STORY-00.2.3: Create `src/pyarchi/validation/` Sub-package

**Files to create:**

1. `src/pyarchi/validation/__init__.py`
2. `src/pyarchi/validation/permissions.py`

**File contents:**

`src/pyarchi/validation/__init__.py`:
```python
"""pyarchi.validation -- Relationship permission checking and metamodel constraint enforcement.

This sub-package encodes the normative Appendix B relationship permission
table and provides validation functions for metamodel constraints.

Public API (will be exported once implemented):
- ``is_permitted(rel_type, source_type, target_type) -> bool``
"""

# Re-exports will be added once permissions.py is implemented:
# EPIC-005 (FEAT-05.11): is_permitted
```

`src/pyarchi/validation/permissions.py`:
```python
"""Appendix B relationship permission table and lookup function.

Encodes the normative relationship permission matrix from
ArchiMate 3.2 Specification, Appendix B, and provides the
``is_permitted`` function for validating relationship triplets.
"""

# TODO: EPIC-005 (FEAT-05.11)
```

**Acceptance Criteria:**
- `python -c "import pyarchi.validation"` succeeds.
- `mypy src/` reports zero errors.
- `ruff check src/` reports zero violations.

**Gotchas:**
- The `validation/` sub-package must NEVER be imported by `metamodel/`. The dependency direction is strictly `validation -> metamodel`, not the reverse. This is enforced by convention; a future CI lint may automate it.

---

### STORY-00.2.4: Create `src/pyarchi/derivation/` Sub-package

**Files to create:**

1. `src/pyarchi/derivation/__init__.py`
2. `src/pyarchi/derivation/engine.py`

**File contents:**

`src/pyarchi/derivation/__init__.py`:
```python
"""pyarchi.derivation -- Derived relationship computation engine.

This sub-package implements the ArchiMate derivation rules, computing
derived relationships from chains of existing relationships in a Model.

Public API (will be exported once implemented):
- ``DerivationEngine``
"""

# Re-exports will be added once engine.py is implemented:
# EPIC-005 (FEAT-05.10): DerivationEngine
```

`src/pyarchi/derivation/engine.py`:
```python
"""The DerivationEngine class.

Computes derived relationships by traversing relationship chains in a
Model and applying the ArchiMate 3.2 derivation rules.
"""

# TODO: EPIC-005 (FEAT-05.10)
```

**Acceptance Criteria:**
- `python -c "import pyarchi.derivation"` succeeds.
- `mypy src/` reports zero errors.
- `ruff check src/` reports zero violations.

**Gotchas:**
- The `derivation/` sub-package is a leaf node in the dependency graph. Nothing else should import from it. It imports from `metamodel`, `validation`, `enums`, and `exceptions`.

---

### STORY-00.2.5: Create `src/pyarchi/exceptions.py`

**Files to create:**

1. `src/pyarchi/exceptions.py`

**File content:**

```python
"""Custom exception types for the pyarchi library.

All exceptions inherit from :class:`PyArchiError`, allowing consumers to
catch all library errors with a single ``except PyArchiError`` clause.

This module has no internal imports and sits at the bottom of the
dependency graph -- any sub-package may import from it safely.
"""


class PyArchiError(Exception):
    """Base exception for all pyarchi library errors.

    Catch this type to handle any error raised by pyarchi without
    distinguishing between validation, derivation, and conformance failures.
    """


class ValidationError(PyArchiError):
    """Raised when a metamodel constraint is violated.

    Examples of constraint violations:
    - Creating a relationship with an invalid source/target pair
      (not permitted by Appendix B).
    - Setting ``is_nested = True`` on a non-structural relationship.
    - Missing a required field on an element or relationship.

    This is distinct from ``pydantic.ValidationError``. Pydantic's error
    type handles schema-level validation (field types, missing fields);
    this type handles ArchiMate-specific semantic validation.
    """


class DerivationError(PyArchiError):
    """Raised when the derivation engine encounters an unrecoverable state.

    Examples:
    - A cycle in the relationship graph that prevents derivation termination.
    - An internal inconsistency in the derivation rule application.
    """


class ConformanceError(PyArchiError):
    """Raised when a model fails a conformance check against the ArchiMate 3.2 specification.

    This error indicates that the model as a whole does not satisfy
    one or more mandatory conformance requirements, as opposed to
    :class:`ValidationError` which targets individual constraint violations.
    """
```

**Acceptance Criteria:**
- `from pyarchi.exceptions import PyArchiError, ValidationError, DerivationError, ConformanceError` succeeds.
- `issubclass(ValidationError, PyArchiError)` is `True`.
- `issubclass(DerivationError, PyArchiError)` is `True`.
- `issubclass(ConformanceError, PyArchiError)` is `True`.
- `issubclass(PyArchiError, Exception)` is `True`.
- `mypy src/` reports zero errors.
- `ruff check src/` reports zero violations.

**Gotchas:**
- Do NOT inherit from `pydantic.ValidationError`. The pyarchi `ValidationError` is intentionally distinct. Pydantic's `ValidationError` has a different constructor signature (it requires a list of error details) and cannot be subclassed cleanly.
- Exception classes with only a docstring and no `__init__` override are valid Python. No `pass` statement is needed after the docstring.
- Ruff ANN rules do not require type annotations on exception class bodies (there are no functions to annotate). These classes are annotation-clean as written.

---

### STORY-00.2.6: Update `CLAUDE.md`

**Status:** No-op (already completed in FEAT-00.1)

**Action for the developer:** Mark this story as complete in `docs/BACKLOG.md` by changing `- [ ]` to `- [x]`. No file changes are needed. The `CLAUDE.md` was updated with build, test, and lint commands as part of FEAT-00.1 / ADR-001. ADR-002 explicitly marks this story as superseded.

---

## 3. Updated `src/pyarchi/__init__.py`

After FEAT-00.2 is complete, update `src/pyarchi/__init__.py` to import and re-export `ValidationError` (the only non-stub, real code that consumers need immediately). The enums are not re-exported from the top level yet -- they will be added to `__all__` when the types that use them are implemented in EPIC-003+.

```python
"""pyarchi -- Python implementation of the ArchiMate 3.2 metamodel."""

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
    # EPIC-001: Scope and Conformance
    # - ConformanceProfile
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

## 4. `src/pyarchi/enums.py` -- Complete Reference

```python
"""Enumeration types for the ArchiMate 3.2 metamodel.

All enumerations used across the pyarchi library are centralized in this
module to keep them at the bottom of the dependency graph, importable by
any sub-package without circular import risk.
"""

from enum import Enum


class Layer(Enum):
    """The seven layers of the ArchiMate 3.2 framework.

    Reference: ArchiMate 3.2 Specification, Section 3.4.
    """

    STRATEGY = "Strategy"
    MOTIVATION = "Motivation"
    BUSINESS = "Business"
    APPLICATION = "Application"
    TECHNOLOGY = "Technology"
    PHYSICAL = "Physical"
    IMPLEMENTATION_MIGRATION = "Implementation and Migration"


class Aspect(Enum):
    """The five aspects (columns) of the ArchiMate 3.2 framework.

    Reference: ArchiMate 3.2 Specification, Section 3.5.
    """

    ACTIVE_STRUCTURE = "Active Structure"
    BEHAVIOR = "Behavior"
    PASSIVE_STRUCTURE = "Passive Structure"
    MOTIVATION = "Motivation"
    COMPOSITE = "Composite"


class RelationshipCategory(Enum):
    """The four categories of ArchiMate relationships.

    Reference: ArchiMate 3.2 Specification, Section 5.1.
    """

    STRUCTURAL = "Structural"
    DEPENDENCY = "Dependency"
    DYNAMIC = "Dynamic"
    OTHER = "Other"


class AccessMode(Enum):
    """Access modes for the Access relationship.

    Reference: ArchiMate 3.2 Specification, Section 5.2.3.
    """

    READ = "Read"
    WRITE = "Write"
    READ_WRITE = "ReadWrite"
    UNSPECIFIED = "Unspecified"


class InfluenceSign(Enum):
    """Influence strength/direction signs for the Influence relationship.

    The string values use the notation from the ArchiMate specification.

    Reference: ArchiMate 3.2 Specification, Section 5.2.4.
    """

    STRONG_POSITIVE = "++"
    POSITIVE = "+"
    NEUTRAL = "0"
    NEGATIVE = "-"
    STRONG_NEGATIVE = "--"


class AssociationDirection(Enum):
    """Directionality of an Association relationship.

    Reference: ArchiMate 3.2 Specification, Section 5.2.5.
    """

    UNDIRECTED = "Undirected"
    DIRECTED = "Directed"


class JunctionType(Enum):
    """Junction connector types.

    Reference: ArchiMate 3.2 Specification, Section 5.3.
    """

    AND = "And"
    OR = "Or"
```

---

## 5. `src/pyarchi/exceptions.py` -- Complete Reference

```python
"""Custom exception types for the pyarchi library.

All exceptions inherit from :class:`PyArchiError`, allowing consumers to
catch all library errors with a single ``except PyArchiError`` clause.

This module has no internal imports and sits at the bottom of the
dependency graph -- any sub-package may import from it safely.
"""


class PyArchiError(Exception):
    """Base exception for all pyarchi library errors.

    Catch this type to handle any error raised by pyarchi without
    distinguishing between validation, derivation, and conformance failures.
    """


class ValidationError(PyArchiError):
    """Raised when a metamodel constraint is violated.

    Examples of constraint violations:
    - Creating a relationship with an invalid source/target pair
      (not permitted by Appendix B).
    - Setting ``is_nested = True`` on a non-structural relationship.
    - Missing a required field on an element or relationship.

    This is distinct from ``pydantic.ValidationError``. Pydantic's error
    type handles schema-level validation (field types, missing fields);
    this type handles ArchiMate-specific semantic validation.
    """


class DerivationError(PyArchiError):
    """Raised when the derivation engine encounters an unrecoverable state.

    Examples:
    - A cycle in the relationship graph that prevents derivation termination.
    - An internal inconsistency in the derivation rule application.
    """


class ConformanceError(PyArchiError):
    """Raised when a model fails a conformance check against the ArchiMate 3.2 specification.

    This error indicates that the model as a whole does not satisfy
    one or more mandatory conformance requirements, as opposed to
    :class:`ValidationError` which targets individual constraint violations.
    """
```

---

## 6. Verification Checklist

Run these commands sequentially from the repository root after completing all six stories. Every command must exit with code 0.

```bash
# 0. Activate the virtual environment
source .venv/bin/activate

# 1. Install the package in editable mode (if not already done)
pip install -e ".[dev]"

# 2. Verify sub-packages are importable
python -c "import pyarchi.metamodel; print('OK: pyarchi.metamodel')"
python -c "import pyarchi.validation; print('OK: pyarchi.validation')"
python -c "import pyarchi.derivation; print('OK: pyarchi.derivation')"

# 3. Verify enums are fully defined
python -c "from pyarchi.enums import Layer, Aspect, RelationshipCategory; print('OK')"
python -c "from pyarchi.enums import AccessMode, InfluenceSign, AssociationDirection, JunctionType; print('OK')"
python -c "from pyarchi.enums import Layer; assert len(Layer) == 7; print('OK: Layer has 7 members')"
python -c "from pyarchi.enums import InfluenceSign; assert InfluenceSign.STRONG_POSITIVE.value == '++'; print('OK: InfluenceSign values')"

# 4. Verify exceptions are importable and hierarchy is correct
python -c "from pyarchi.exceptions import ValidationError; print('OK')"
python -c "from pyarchi.exceptions import PyArchiError, ValidationError, DerivationError, ConformanceError; assert issubclass(ValidationError, PyArchiError); assert issubclass(DerivationError, PyArchiError); assert issubclass(ConformanceError, PyArchiError); print('OK: exception hierarchy')"

# 5. Verify top-level re-exports
python -c "import pyarchi; assert 'ValidationError' in pyarchi.__all__; print('OK')"
python -c "from pyarchi import ValidationError; print('OK: top-level re-export')"

# 6. Ruff linter -- zero violations
ruff check src/ test/

# 7. Ruff formatter -- zero violations
ruff format --check src/ test/

# 8. mypy strict -- zero errors
mypy src/

# 9. pytest -- all existing tests pass, no new failures
pytest

# 10. Verify the dependency graph is not violated (no reverse imports)
python -c "
import ast, pathlib, sys
# metamodel must not import from validation or derivation
for f in pathlib.Path('src/pyarchi/metamodel').rglob('*.py'):
    tree = ast.parse(f.read_text())
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mod = getattr(node, 'module', '') or ''
            for alias in getattr(node, 'names', []):
                mod_name = getattr(alias, 'name', '')
                assert 'validation' not in mod and 'validation' not in mod_name, f'{f}: imports validation'
                assert 'derivation' not in mod and 'derivation' not in mod_name, f'{f}: imports derivation'
print('OK: no dependency graph violations')
"
```

---

## 7. Mypy Stub File Gotcha

**Question:** What is the correct minimum content for a stub `.py` file that is mypy-clean under strict mode?

**Answer:** A module docstring alone is sufficient. A file containing only:

```python
"""Module docstring describing the future contents."""

# TODO: EPIC-002
```

is valid Python and passes mypy strict mode with zero errors. Here is why:

1. **No `pass` needed at module scope.** The `pass` statement is only required inside compound statements (`class`, `def`, `if`, `for`, etc.) that would otherwise have an empty body. At module scope, Python does not require any statements -- a module can be completely empty and still be valid.

2. **No imports needed.** Mypy strict mode flags issues like `disallow_untyped_defs` and `disallow_any_generics`, but these rules only apply when definitions (functions, classes) exist. A module with no definitions triggers none of these checks.

3. **A docstring is a string literal expression.** Python treats it as a valid statement. The module is syntactically complete.

4. **A comment after the docstring is ignored by all tools.** Comments are not statements and do not affect parsing, type checking, or linting.

The only scenario where a stub file could fail tooling checks is if an `__init__.py` attempts to import a name from it that does not exist. This is why STORY-00.2.1 explicitly states that `metamodel/__init__.py` should NOT import anything from the stub modules.

---

## File Inventory

After FEAT-00.2, the following files will exist under `src/pyarchi/`:

```
src/pyarchi/
    __init__.py              (updated -- re-exports exceptions)
    py.typed                 (unchanged)
    enums.py                 (NEW -- complete, all 7 enums)
    exceptions.py            (NEW -- complete, all 4 exception classes)
    metamodel/
        __init__.py          (NEW -- docstring + comments only)
        concepts.py          (NEW -- stub)
        mixins.py            (NEW -- stub)
        model.py             (NEW -- stub)
        notation.py          (NEW -- stub)
    validation/
        __init__.py          (NEW -- docstring + comments only)
        permissions.py       (NEW -- stub)
    derivation/
        __init__.py          (NEW -- docstring + comments only)
        engine.py            (NEW -- stub)
```

Total new files: 11
Modified files: 1 (`src/pyarchi/__init__.py`)
