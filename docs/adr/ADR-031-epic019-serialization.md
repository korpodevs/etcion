# ADR-031: EPIC-019 -- Open Group Exchange Format Serialization

## Status

PROPOSED

## Date

2026-03-25

## Context

EPIC-019 introduces the primary persistence layer: reading and writing ArchiMate models in the Open Group ArchiMate Model Exchange File Format. A secondary JSON serialization path is also in scope. No serialization code exists in the codebase today.

The metamodel is fully built out through EPIC-018. `Concept.id` uses UUID4 strings (ADR-006). `Model` is a plain Python class with `add()`, `__getitem__`, and `validate()` (ADR-010). All concrete element and relationship types are Pydantic `BaseModel` subclasses with `_type_name` properties. `lxml` is not currently a dependency.

Prior decisions accepted without re-litigation:

- `Concept` as root ABC; `Element` and `Relationship` as direct subtypes (ADR-006, ADR-007).
- `Model` as the top-level container (ADR-010).
- Pydantic `BaseModel` as the foundation for all domain types (ADR-006).
- Exports deferred to EPIC-020 (ADR-026 pattern).

Spec reference: [Open Group ArchiMate Model Exchange File Format](https://publications.opengroup.org/standards/archimate), ArchiMate 3.2.

## Decisions

### 1. File Placement

| Artifact | Location |
|---|---|
| Package root | `src/etcion/serialization/__init__.py` |
| XML serializer | `src/etcion/serialization/xml.py` |
| JSON serializer | `src/etcion/serialization/json.py` |
| Type registry | `src/etcion/serialization/registry.py` |

Serialization is an infrastructure concern orthogonal to the metamodel. A dedicated package keeps it isolated from `etcion.metamodel`.

### 2. XML Library: `lxml` as Optional Dependency

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| `xml.etree.ElementTree` (stdlib) | Zero dependencies | No XSD validation, limited XPath, slower on large trees | **Rejected** |
| `lxml` | XSD validation, full XPath, C-speed parsing, namespace-aware | External C dependency | **Accepted** |

`lxml` is added as an optional dependency: `pip install etcion[xml]`. The `etcion.serialization.xml` module raises `ImportError` with a descriptive message (`pip install etcion[xml]`) if `lxml` is not installed. The core library remains dependency-light.

`pyproject.toml` gains:

```toml
[project.optional-dependencies]
xml = ["lxml>=5.0,<6.0"]
```

### 3. External Type Registry (Not Methods on Domain Classes)

| Approach | Description | Verdict |
|---|---|---|
| `to_xml()` / `from_xml()` on each class | Serialization logic lives inside metamodel classes | **Rejected** -- violates single-responsibility; metamodel classes should not know about XML |
| Visitor / strategy pattern | Double-dispatch through accept/visit | **Rejected** -- over-engineered for a mapping that is fundamentally a lookup table |
| External registry | A `TypeRegistry` maps `type[Concept]` to XML tag names and attribute extractors | **Accepted** |

The registry is a module-level dict in `serialization/registry.py` mapping `type[Concept]` to dataclass descriptors containing: XML tag name, attribute extraction callables, and attribute injection callables (for deserialization). Concrete types self-register via a decorator or explicit registration calls during module import. The metamodel classes remain unaware of serialization.

### 4. Identifier Format: Internal UUID, Exchange Format on Serialization

The Exchange Format uses `id-XXXXXXXX-XXXX-...` prefixed identifiers. `Concept.id` currently stores bare UUID4 strings (ADR-006).

Decision: the serializer maintains a bidirectional `dict[str, str]` mapping between internal UUIDs and Exchange Format IDs during serialization/deserialization. On write, IDs lacking the `id-` prefix are wrapped as `id-{uuid}`. On read, the `id-` prefix is stripped if present, or the raw identifier is preserved. This keeps the internal ID format stable while producing spec-compliant output.

### 5. Standalone Functions, Not Model Methods

| Approach | Verdict |
|---|---|
| `Model.to_xml()` / `Model.from_xml()` | **Rejected** -- couples Model to lxml, forces the optional dependency into the core |
| Standalone functions in `etcion.serialization.xml` | **Accepted** |

Public API:

```python
def serialize_model(model: Model) -> etree._ElementTree: ...
def deserialize_model(tree: etree._ElementTree) -> Model: ...
```

`Model` remains a plain container with no serialization knowledge.

### 6. File I/O Convenience Functions

```python
def write_model(model: Model, path: str | Path) -> None: ...
def read_model(path: str | Path) -> Model: ...
```

Both live in `etcion.serialization.xml`. `write_model` emits UTF-8 encoded XML with `<?xml version="1.0"?>` declaration and 2-space indentation. `read_model` delegates to `lxml.etree.parse` then `deserialize_model`.

### 7. Round-Trip Fidelity

| Data category | Guarantee |
|---|---|
| Elements (type, id, name, documentation) | **Full** -- lossless round-trip |
| Relationships (type, source, target, type-specific fields) | **Full** -- `access_mode`, `sign`, `direction`, etc. preserved |
| Profiles and specializations | **Full** -- serialized as Exchange Format property definitions |
| Visual/diagrammatic data (views, coordinates, bendpoints) | **Best-effort** -- stored as opaque `lxml` subtrees, re-emitted verbatim on write |

Unknown XML elements encountered during read are preserved as raw `lxml.etree.Element` nodes attached to the `Model` (via an internal `_opaque_xml: list[etree._Element]` field) and re-emitted during write. This prevents data loss when round-tripping files produced by tools with proprietary extensions.

### 8. XSD Validation: Optional, Explicit

```python
def validate_exchange_format(tree: etree._ElementTree) -> list[str]: ...
```

Validates a serialized tree against the Exchange Format XSD. Returns a list of error strings (empty on success). Not invoked automatically on read or write -- the caller opts in. The XSD is bundled in `src/etcion/serialization/schema/` or loaded from a configurable path.

### 9. JSON Serialization: Pydantic-Native

JSON serialization lives in `etcion.serialization.json` and leverages Pydantic's `model_dump()` / `model_validate()` with a custom encoder that emits `type[Concept]` references as `_type_name` strings. No `lxml` dependency.

```python
def model_to_dict(model: Model) -> dict[str, Any]: ...
def model_from_dict(data: dict[str, Any]) -> Model: ...
```

This is a secondary format for programmatic interchange (APIs, databases), not for ArchiMate tool interop.

### 10. Unknown Element Handling on Read

When the XML deserializer encounters an element type not present in the registry, it logs a `warnings.warn()` at `UserWarning` level and skips the element. This enables forward compatibility: files produced by tools implementing newer spec versions can still be partially loaded. The skipped element's raw XML is preserved in `_opaque_xml` (Decision 7) so it survives round-trip.

### 11. Exports Deferred to EPIC-020

Consistent with ADR-026, serialization functions are not added to `etcion.__init__.__all__` in EPIC-019. Users import directly from `etcion.serialization.xml` or `etcion.serialization.json`.

### 12. Dependency Gating Pattern

The `lxml` import is guarded at module level in `etcion.serialization.xml`:

```python
try:
    from lxml import etree
except ImportError as exc:
    raise ImportError(
        "lxml is required for XML serialization. "
        "Install it with: pip install etcion[xml]"
    ) from exc
```

`etcion.serialization.json` has no additional dependencies beyond Pydantic.

## Alternatives Considered

### Methods on Domain Classes

Adding `to_xml()` and `from_xml()` to `Element` and `Relationship`. Rejected because:

1. Introduces an `lxml` dependency into the metamodel package, breaking the optional-dependency boundary.
2. Every new element type must implement serialization methods, scattering XML concerns across dozens of files.
3. Testing metamodel logic requires `lxml` to be installed even when serialization is not needed.

### Model Methods Delegating to Serialization Module

Adding `Model.to_xml()` that internally imports from `etcion.serialization.xml`. Rejected because:

1. The `Model` class gains API surface that only works when an optional dependency is installed, violating least surprise.
2. Type checkers and IDE autocompletion would show `to_xml()` even when `lxml` is absent, leading to confusing runtime errors.
3. Standalone functions make the dependency boundary explicit at the import site.

### XML Round-Trip via Dict Intermediate

Serializing Model to dict (via Pydantic), then dict to XML. Rejected because:

1. Double serialization overhead.
2. Loss of XML-specific concerns (namespaces, attribute ordering, processing instructions) that must be controlled directly.
3. The dict format (Decision 9) serves a different purpose and should not be coupled to XML output.

## Consequences

### Positive

- The metamodel package remains free of serialization dependencies. `lxml` is only required when XML features are used.
- The external registry centralizes the type-to-XML mapping in one place, making it straightforward to add new element types without touching serialization infrastructure.
- Standalone functions make the dependency boundary visible at the import site and are easily composable in pipelines.
- Best-effort visual data preservation prevents data loss when round-tripping through etcion, even for XML structures the library does not interpret.

### Negative

- Users must import from `etcion.serialization.xml` rather than calling `model.to_xml()`. This is less discoverable but consistent with the library's separation of concerns.
- The type registry must be kept in sync with the metamodel class hierarchy. A missing registration is a silent bug until a serialization test catches it.
- Opaque XML preservation (`_opaque_xml`) adds memory overhead proportional to unrecognized content. For models with large view sections, this could be significant.
