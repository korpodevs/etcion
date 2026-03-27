# Permission Matrix

The ArchiMate 3.2 specification defines a normative **relationship permission
matrix** (Appendix B) that governs which relationships are allowed between
which element types.  etcion encodes this matrix in
`etcion.validation.permissions` and enforces it at model-validation time.

## How to Read the Tables

Each sub-table below corresponds to one relationship type.  The columns are:

| Column | Meaning |
|--------|---------|
| **Source Type** | The element type at the source end of the relationship |
| **Target Type** | The element type at the target end of the relationship |
| **Permitted** | Whether the combination is allowed |

**Universal relationships** are not listed in the tables below because they
apply uniformly:

- **Composition** and **Aggregation** -- permitted between same-type elements.
- **Specialization** -- permitted between same concrete type only.
- **Association** -- always permitted between any two concepts.

## Assignment

| Source Type | Target Type | Permitted |
|-------------|-------------|-----------|
| PassiveStructureElement | BehaviorElement | No |
| BusinessInternalActiveStructureElement | BusinessInternalBehaviorElement | Yes |
| BusinessInternalActiveStructureElement | BusinessService | Yes |
| BusinessInternalActiveStructureElement | BusinessEvent | Yes |
| BusinessInterface | BusinessService | Yes |
| ApplicationInternalActiveStructureElement | ApplicationInternalBehaviorElement | Yes |
| ApplicationInternalActiveStructureElement | ApplicationService | Yes |
| ApplicationInternalActiveStructureElement | ApplicationEvent | Yes |
| ApplicationInterface | ApplicationService | Yes |
| TechnologyInternalActiveStructureElement | TechnologyInternalBehaviorElement | Yes |
| TechnologyInternalActiveStructureElement | TechnologyService | Yes |
| TechnologyInternalActiveStructureElement | TechnologyEvent | Yes |
| TechnologyInterface | TechnologyService | Yes |
| PhysicalActiveStructureElement | TechnologyInternalBehaviorElement | Yes |
| PhysicalActiveStructureElement | TechnologyService | Yes |
| BusinessInternalActiveStructureElement | MotivationElement | Yes |
| BusinessInternalActiveStructureElement | WorkPackage | Yes |
| Resource | Capability | Yes |
| Resource | ValueStream | Yes |
| Resource | CourseOfAction | Yes |

## Access

| Source Type | Target Type | Permitted |
|-------------|-------------|-----------|
| PassiveStructureElement | Element | No |
| BusinessInternalActiveStructureElement | BusinessPassiveStructureElement | Yes |
| BusinessInternalBehaviorElement | BusinessPassiveStructureElement | Yes |
| BusinessService | BusinessPassiveStructureElement | Yes |
| BusinessEvent | BusinessPassiveStructureElement | Yes |
| BusinessInterface | BusinessPassiveStructureElement | Yes |
| ApplicationInternalActiveStructureElement | DataObject | Yes |
| ApplicationInternalBehaviorElement | DataObject | Yes |
| ApplicationService | DataObject | Yes |
| ApplicationEvent | DataObject | Yes |
| ApplicationInterface | DataObject | Yes |
| TechnologyInternalActiveStructureElement | Artifact | Yes |
| TechnologyInternalBehaviorElement | Artifact | Yes |
| TechnologyService | Artifact | Yes |
| TechnologyEvent | Artifact | Yes |
| TechnologyInterface | Artifact | Yes |
| ImplementationEvent | Deliverable | Yes |
| PhysicalActiveStructureElement | Material | Yes |

## Serving

| Source Type | Target Type | Permitted |
|-------------|-------------|-----------|
| PassiveStructureElement | Element | No |
| BusinessService | BusinessInternalBehaviorElement | Yes |
| BusinessService | BusinessService | Yes |
| BusinessInterface | BusinessInternalActiveStructureElement | Yes |
| ApplicationService | ApplicationInternalBehaviorElement | Yes |
| ApplicationService | ApplicationService | Yes |
| ApplicationInterface | ApplicationInternalActiveStructureElement | Yes |
| TechnologyService | TechnologyInternalBehaviorElement | Yes |
| TechnologyService | TechnologyService | Yes |
| TechnologyInterface | TechnologyInternalActiveStructureElement | Yes |
| ApplicationService | BusinessInternalBehaviorElement | Yes |
| ApplicationInterface | BusinessInternalActiveStructureElement | Yes |
| BusinessService | ApplicationInternalBehaviorElement | Yes |
| BusinessInterface | ApplicationInternalActiveStructureElement | Yes |
| TechnologyService | ApplicationInternalBehaviorElement | Yes |
| TechnologyInterface | ApplicationInternalActiveStructureElement | Yes |
| Capability | Capability | Yes |
| ValueStream | Capability | Yes |
| Equipment | Equipment | Yes |
| Facility | Facility | Yes |

## Realization

| Source Type | Target Type | Permitted |
|-------------|-------------|-----------|
| Element | BusinessInternalActiveStructureElement | No |
| Deliverable | StructureElement | Yes |
| Deliverable | BehaviorElement | Yes |
| ApplicationInternalBehaviorElement | BusinessInternalBehaviorElement | Yes |
| DataObject | BusinessObject | Yes |
| TechnologyInternalBehaviorElement | ApplicationInternalBehaviorElement | Yes |
| Artifact | DataObject | Yes |
| Artifact | ApplicationComponent | Yes |
| StructureElement | MotivationElement | Yes |
| BehaviorElement | MotivationElement | Yes |
| BehaviorElement | Capability | Yes |
| BehaviorElement | ValueStream | Yes |
| StructureElement | Resource | Yes |

## Influence

| Source Type | Target Type | Permitted |
|-------------|-------------|-----------|
| MotivationElement | MotivationElement | Yes |
| MotivationElement | Element | Yes |
| Element | MotivationElement | Yes |

## Triggering

| Source Type | Target Type | Permitted |
|-------------|-------------|-----------|
| BusinessInternalBehaviorElement | BusinessInternalBehaviorElement | Yes |
| BusinessEvent | BusinessInternalBehaviorElement | Yes |
| BusinessInternalBehaviorElement | BusinessEvent | Yes |
| BusinessEvent | BusinessEvent | Yes |
| ApplicationInternalBehaviorElement | ApplicationInternalBehaviorElement | Yes |
| ApplicationEvent | ApplicationInternalBehaviorElement | Yes |
| ApplicationInternalBehaviorElement | ApplicationEvent | Yes |
| ApplicationEvent | ApplicationEvent | Yes |
| TechnologyInternalBehaviorElement | TechnologyInternalBehaviorElement | Yes |
| TechnologyEvent | TechnologyInternalBehaviorElement | Yes |
| TechnologyInternalBehaviorElement | TechnologyEvent | Yes |
| TechnologyEvent | TechnologyEvent | Yes |
| ImplementationEvent | WorkPackage | Yes |
| ImplementationEvent | Plateau | Yes |
| WorkPackage | ImplementationEvent | Yes |
| Plateau | ImplementationEvent | Yes |
| Capability | Capability | Yes |
| ValueStream | ValueStream | Yes |

## Flow

| Source Type | Target Type | Permitted |
|-------------|-------------|-----------|
| BusinessInternalBehaviorElement | BusinessInternalBehaviorElement | Yes |
| BusinessEvent | BusinessInternalBehaviorElement | Yes |
| BusinessInternalBehaviorElement | BusinessEvent | Yes |
| BusinessEvent | BusinessEvent | Yes |
| ApplicationInternalBehaviorElement | ApplicationInternalBehaviorElement | Yes |
| ApplicationEvent | ApplicationInternalBehaviorElement | Yes |
| ApplicationInternalBehaviorElement | ApplicationEvent | Yes |
| ApplicationEvent | ApplicationEvent | Yes |
| TechnologyInternalBehaviorElement | TechnologyInternalBehaviorElement | Yes |
| TechnologyEvent | TechnologyInternalBehaviorElement | Yes |
| TechnologyInternalBehaviorElement | TechnologyEvent | Yes |
| TechnologyEvent | TechnologyEvent | Yes |
| ValueStream | ValueStream | Yes |

## Usage Example

```python
from etcion.validation.permissions import is_permitted
from etcion.metamodel.relationships import Assignment, Access
from etcion.metamodel.business import (
    BusinessActor,
    BusinessProcess,
    BusinessObject,
)

# Assignment: BusinessActor -> BusinessProcess is permitted
assert is_permitted(Assignment, BusinessActor, BusinessProcess)

# Access: BusinessObject (passive) -> BusinessProcess is NOT permitted
assert not is_permitted(Access, BusinessObject, BusinessProcess)
```

!!! note "Regenerating this page"
    Run `python scripts/generate_permission_matrix.py` to regenerate the
    permission tables from the current `_PERMISSION_TABLE` in source code.
