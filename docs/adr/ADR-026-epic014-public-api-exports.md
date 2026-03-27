# ADR-026: EPIC-014 -- Public API Exports for Phase 2

## Status

ACCEPTED

## Date

2026-03-25

## Context

Phase 2 (EPICs 006--013) added seven layer modules with concrete element classes and layer-specific ABCs. None of these types are currently exported from `etcion.__init__`. Consumer code must use deep imports like `from etcion.metamodel.business import BusinessActor`, which is inconsistent with the Phase 1 pattern where all types are importable from the top-level package.

EPIC-014 is a single feature (FEAT-14.1) that adds Phase 2 types to `src/etcion/__init__.py` and `__all__`, plus a verification test.

Prior decisions accepted without re-litigation:

- Top-level re-export pattern established in FEAT-05.11 (ADR-017).
- `__all__` as the canonical public API surface.
- Parametrized import test pattern from FEAT-05.11.

## Decisions

### 1. Single Feature, No New Modules

FEAT-14.1 modifies exactly two files: `src/etcion/__init__.py` (imports and `__all__`) and a new test file. No new modules, enums, relationships, or validation changes.

### 2. Export Scope

| Category | Export? | Rationale |
|---|---|---|
| Concrete element classes (all 7 layers) | Yes | Primary consumer API |
| Layer-specific ABCs | Yes | Needed for `isinstance` checks, type annotations |
| Enums (`Layer`, `Aspect`, etc.) | No change | Already exported in Phase 1 |
| Relationship classes | No change | Already exported in Phase 1 |
| Validation / Derivation | No change | Already exported in Phase 1 |

### 3. Types to Export by Module

**`strategy`** -- ABCs: `StrategyStructureElement`, `StrategyBehaviorElement`. Concrete: `Resource`, `Capability`, `ValueStream`, `CourseOfAction`.

**`business`** -- ABCs: `BusinessInternalActiveStructureElement`, `BusinessInternalBehaviorElement`, `BusinessPassiveStructureElement`. Concrete: `BusinessActor`, `BusinessRole`, `BusinessCollaboration`, `BusinessInterface`, `BusinessProcess`, `BusinessFunction`, `BusinessInteraction`, `BusinessEvent`, `BusinessService`, `BusinessObject`, `Contract`, `Representation`, `Product`.

**`application`** -- ABCs: `ApplicationInternalActiveStructureElement`, `ApplicationInternalBehaviorElement`. Concrete: `ApplicationComponent`, `ApplicationCollaboration`, `ApplicationInterface`, `ApplicationFunction`, `ApplicationInteraction`, `ApplicationProcess`, `ApplicationEvent`, `ApplicationService`, `DataObject`.

**`technology`** -- ABCs: `TechnologyInternalActiveStructureElement`, `TechnologyInternalBehaviorElement`. Concrete: `Node`, `Device`, `SystemSoftware`, `TechnologyCollaboration`, `TechnologyInterface`, `Path`, `CommunicationNetwork`, `TechnologyFunction`, `TechnologyProcess`, `TechnologyInteraction`, `TechnologyEvent`, `TechnologyService`, `Artifact`.

**`physical`** -- ABCs: `PhysicalActiveStructureElement`, `PhysicalPassiveStructureElement`. Concrete: `Equipment`, `Facility`, `DistributionNetwork`, `Material`.

**`motivation`** -- No new ABCs (all extend `MotivationElement`, already exported). Concrete: `Stakeholder`, `Driver`, `Assessment`, `Goal`, `Outcome`, `Principle`, `Requirement`, `Constraint`, `Meaning`, `Value`.

**`implementation_migration`** -- No new ABCs. Concrete: `WorkPackage`, `Deliverable`, `ImplementationEvent`, `Plateau`, `Gap`.

### 4. Import Block Organization

Imports in `__init__.py` are grouped by layer module, one `from etcion.metamodel.<layer> import (...)` block per layer. This matches the per-layer module pattern established in Phase 2. Existing Phase 1 import blocks remain unchanged and appear first.

### 5. `__all__` Organization

Phase 2 entries are appended to `__all__` after the existing Phase 1 entries, grouped by layer with a comment per layer (e.g., `# Strategy layer (EPIC-006)`). ABCs and concrete classes are listed together within each layer group -- no separate ABC section.

### 6. Test Approach

A single parametrized test verifies every Phase 2 type name is accessible via `getattr(etcion, name)`. This follows the FEAT-05.11 export test pattern. The test parameter list is the set difference between the new `__all__` and the Phase 1 `__all__`.

## Alternatives Considered

### Separate `etcion.elements` Namespace

Exporting Phase 2 types from a `etcion.elements` sub-namespace instead of the top-level package was considered. Rejected because it breaks the established Phase 1 convention and forces consumers to learn two import patterns.

### Exporting Only Concrete Classes, Not ABCs

Omitting ABCs from the public API was considered. Rejected because consumer code needs ABCs for `isinstance` layer checks (e.g., `isinstance(el, BusinessInternalBehaviorElement)`) and for type annotations in functions that accept any element from a layer category.

## Consequences

### Positive

- All ArchiMate element types importable from `etcion` top-level, consistent with Phase 1 pattern.
- ABCs available for type-safe `isinstance` checks without deep imports.
- `__all__` serves as a single, auditable manifest of the public API surface.

### Negative

- `__init__.py` grows to ~70 additional names. This is acceptable for a metamodel library where the type count is spec-driven and finite.
- Import time increases slightly due to eager loading of all seven layer modules. Lazy loading is deferred to a future performance epic if profiling shows need.
