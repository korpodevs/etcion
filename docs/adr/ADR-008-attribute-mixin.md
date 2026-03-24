# ADR-008: AttributeMixin

## Status

ACCEPTED

## Date

2026-03-23

## Context

The ArchiMate 3.2 specification defines a common set of descriptive attributes shared by both Elements and Relationships: a human-readable `name`, an optional `description`, and an optional `documentation_url`. These attributes are not defined on `Concept` (the root ABC), because not all Concepts carry them -- `RelationshipConnector` (Junction) is a Concept that has no name or description in the specification.

The shared attributes must be applied to both `Element` and `Relationship` without duplicating the field definitions. Duplication would mean that adding a new shared attribute (if the spec evolves) requires modifying two classes, with the risk that they diverge. A mixin class is the standard Python pattern for sharing field definitions across unrelated branches of an inheritance tree.

The design challenge is that `Element` and `Relationship` are Pydantic `BaseModel` subclasses (via `Concept`, per ADR-006). Pydantic v2's `ModelMetaclass` collects field annotations from all classes in the MRO, including plain Python classes that are not themselves `BaseModel` subclasses. This means a mixin does not need to inherit from `BaseModel` to contribute fields to a Pydantic model -- it only needs to declare type-annotated attributes. However, if the mixin DOES inherit from `BaseModel`, a diamond inheritance problem arises: `Element` would have two `BaseModel` paths in its MRO (`Element -> Concept -> BaseModel` and `Element -> AttributeMixin -> BaseModel`), which can cause metaclass resolution conflicts or unexpected field ordering.

The mixin must be designed so that:

1. Its field annotations are collected by Pydantic when mixed into a `BaseModel` subclass.
2. It does not introduce a second `BaseModel` path in the MRO.
3. It is type-checker friendly -- mypy and pyright recognize the fields as part of the mixed-in class.

## Decision

### Implementation: Plain Python Class

`AttributeMixin` is defined in `src/pyarchi/metamodel/mixins.py` as a plain Python class with annotated attributes:

```python
class AttributeMixin:
    """Shared descriptive attributes for Element and Relationship."""

    name: str
    description: str | None = None
    documentation_url: str | None = None
```

This class does not inherit from `BaseModel`, `ABC`, `dataclass`, or any other framework base class. It is a plain class whose only purpose is to carry type annotations that Pydantic's `ModelMetaclass` will collect when the mixin appears in the MRO of a `BaseModel` subclass.

### Field Specifications

| Field | Type | Default | Required | Description |
|---|---|---|---|---|
| `name` | `str` | (none) | Yes | Human-readable name of the element or relationship. Required because every named ArchiMate concept must have a name; anonymous concepts are not valid in the specification. |
| `description` | `str \| None` | `None` | No | Free-text description providing additional detail. Optional because many modelled concepts have no description. |
| `documentation_url` | `str \| None` | `None` | No | URL pointing to external documentation. Optional; most concepts do not reference external docs. |

`name` is required (no default) because the ArchiMate specification mandates that Elements and Relationships have names. A model with unnamed elements would be non-conformant. Pydantic enforces this at construction time: `BusinessActor()` without a `name` argument raises `ValidationError`.

`description` and `documentation_url` default to `None` rather than empty string to distinguish "no description provided" from "description is an empty string." This is a semantic distinction that matters during serialization: a `None` description is omitted from XML output, while an empty string description produces an empty `<documentation>` tag.

### Why Plain Class, Not BaseModel

If `AttributeMixin` inherited from `BaseModel`, the MRO for `Element` would be:

```
Element -> AttributeMixin -> BaseModel -> Concept -> BaseModel
```

This creates a diamond where `BaseModel` appears twice. Pydantic v2's `ModelMetaclass` can handle some diamond cases, but the behavior is fragile and version-dependent. More importantly, it violates the principle that a class hierarchy should have exactly one `BaseModel` entry point. `Concept` is that entry point (ADR-006); no other class in the hierarchy should independently inherit from `BaseModel`.

Pydantic v2 explicitly supports the plain-mixin pattern. The `ModelMetaclass` scans the entire MRO for annotated attributes and includes them in the model's field set, regardless of whether the declaring class is itself a `BaseModel`. This is documented Pydantic behavior, not an implementation accident.

### Why Plain Class, Not Dataclass

Using `@dataclass` for the mixin was considered. A dataclass would provide `__init__`, `__repr__`, and `__eq__` methods. However:

1. Pydantic `BaseModel` already provides its own `__init__`, `__repr__`, and `__eq__`. The dataclass-generated methods would conflict with or be overridden by Pydantic's, adding confusion without benefit.
2. Combining `@dataclass` with Pydantic `BaseModel` in the MRO produces unpredictable behavior because both frameworks generate `__init__` methods. The interaction is not well-defined in Pydantic's documentation.
3. A plain class with annotations is the simplest construct that achieves the goal. Adding `@dataclass` would introduce complexity (field ordering rules, `__post_init__` semantics) for no gain.

### MRO Placement

When `AttributeMixin` is mixed into a Pydantic class, it must appear before the `BaseModel`-carrying ancestor in the base class list:

```python
class Element(AttributeMixin, Concept):  # Correct: mixin before Concept
    ...
```

This ordering ensures that `AttributeMixin`'s annotations are processed before `Concept`'s annotations. In practice, Pydantic collects all annotations from the entire MRO and orders them by class hierarchy (most-derived first), so the field ordering in the model is: `name`, `description`, `documentation_url` (from `AttributeMixin`), then `id` (from `Concept`). This ordering is logical: descriptive fields appear before the technical identifier.

### Not Exported from `__init__.py`

`AttributeMixin` is NOT re-exported from `src/pyarchi/__init__.py`. It is an internal implementation detail of the metamodel hierarchy. Consumers interact with `Element` and `Relationship`, which carry the mixin's fields. There is no use case for importing `AttributeMixin` directly -- it cannot be instantiated (it is a plain class with no `__init__`), and it provides no methods or behavior.

If a future need arises for consumers to check whether a class has the shared attributes (e.g., `isinstance(obj, AttributeMixin)`), the mixin can be exported at that point. For now, YAGNI applies.

## Alternatives Considered

### Declaring Fields Directly on Both `Element` and `Relationship`

The simplest approach: copy-paste the three field annotations onto both classes. This was rejected because:

1. It violates DRY. Adding or modifying a shared attribute requires changing two classes in lockstep.
2. It creates a risk of divergence: one class might get `documentation_url` renamed to `doc_url` while the other retains the original name.
3. The ArchiMate specification defines these attributes as a shared concept (the "named and documented" pattern), and the code should reflect that structural sharing.

### `BaseModel` Mixin with `model_config = ConfigDict()`

Making `AttributeMixin(BaseModel)` with its own `model_config` was considered for cases where the mixin needs its own Pydantic configuration. This was rejected because:

1. The diamond inheritance problem described above.
2. `AttributeMixin` has no configuration needs. Its fields are simple types (`str`, `str | None`) that require no custom validators, serializers, or schema overrides.
3. All configuration lives on `Concept` (ADR-006) and is inherited by the entire hierarchy.

### Protocol-Based Mixin with `typing.Protocol`

Defining `AttributeMixin` as a `typing.Protocol` with `name`, `description`, and `documentation_url` as protocol members was considered. This would provide structural typing: any class with those attributes would satisfy the protocol. This was rejected because:

1. A Protocol does not contribute field annotations to Pydantic's `ModelMetaclass`. Pydantic does not scan Protocol members when building the field set. The fields would need to be re-declared on `Element` and `Relationship` anyway, making the Protocol decorative rather than functional.
2. The mixin's purpose is to inject field definitions, not to define an interface. A Protocol defines what methods/attributes a class must have; a mixin provides the actual implementation (in this case, the annotations and defaults). These are different design intents.

### Abstract Base Class Mixin

Making `AttributeMixin(abc.ABC)` with abstract properties for each field was considered. This would force subclasses to explicitly implement each attribute. This was rejected because:

1. Pydantic fields are not properties. Declaring `@property @abstractmethod def name(self) -> str` conflicts with Pydantic's field system, which expects `name` to be a class-level annotation, not a property method.
2. `Concept` already has an abstract property (`_type_name`) for the instantiation guard. Additional abstract members on the mixin are redundant for the guard and harmful for Pydantic compatibility.

## Consequences

### Positive

- **Single source of truth for shared fields**: `name`, `description`, and `documentation_url` are defined once in `AttributeMixin` and inherited by both `Element` and `Relationship`. Changes propagate automatically.
- **Clean MRO**: No diamond inheritance, no metaclass conflicts. The `BaseModel` entry point is `Concept` only, and `AttributeMixin` is a lightweight annotation carrier.
- **Pydantic-native**: The fields contributed by `AttributeMixin` are indistinguishable from fields declared directly on the consuming class. They appear in `model_fields`, `model_dump()`, JSON schema, and all Pydantic APIs.
- **mypy compatible**: mypy recognizes annotated attributes on plain classes in the MRO and includes them in the type signature of the consuming class. `Element.name` is typed as `str` in mypy's analysis.
- **Minimal code**: The mixin is three lines of annotations. No methods, no metaclass, no decorators.

### Negative

- **Plain class is not self-documenting as a mixin**: Unlike `class AttributeMixin(SomeMixinBase)`, a plain class `class AttributeMixin:` does not signal "I am a mixin" through its type hierarchy. The naming convention (`*Mixin`) and the docstring are the only indicators. This is a Python convention limitation, not a library design flaw.
- **No standalone instantiation**: `AttributeMixin()` produces a bare Python object with no `__init__` parameters -- the annotations are not enforced without Pydantic's `ModelMetaclass`. This is intentional (the mixin is not meant to be instantiated), but a confused contributor might try to instantiate it and get a useless object. The class docstring and the decision not to export it mitigate this.
- **Implicit field injection**: A contributor reading `class Element(AttributeMixin, Concept)` must look at `AttributeMixin` to discover that `Element` has a `name` field. This is the standard trade-off of mixin-based design. IDE "go to definition" and Pydantic's `Element.model_fields` mitigate discoverability.

## Compliance

This ADR provides the architectural rationale for each story in FEAT-02.5:

| Story | Decision Implemented |
|---|---|
| STORY-02.5.1 | `AttributeMixin` defined in `src/pyarchi/metamodel/mixins.py` as a plain class with `name: str`, `description: str \| None = None`, `documentation_url: str \| None = None` |
| STORY-02.5.2 | Mixin is applied to both `Element` and `Relationship` via MRO inheritance; test confirms fields are present on concrete instances of both |
