# ADR-033: EPIC-028 -- Archi Tool Interoperability

## Status

PROPOSED

## Date

2026-03-25

## Context

pyarchi produces Exchange Format XML that is namespace-correct and structurally valid per ADR-031, but Archi (the reference open-source ArchiMate tool) rejects it on import. A side-by-side comparison of `pet_shop.xml` (pyarchi) against `pet_shop-from_archi.xml` (Archi exchange export) and the bundled XSD reveals a small number of spec-compliance gaps. The full analysis is in `docs/dev-brief/ARCHI-COMPAT-ISSUES.md`.

The root cause is clear: `ModelType` extends `NamedReferenceableType`, which restricts `NameGroup` to `minOccurs="1"`. Our `serialize_model()` emits no `<name>` child on `<model>`, so the output is invalid against the XSD. FEAT-19.4 implemented `serialize_model` without consulting the XSD definition of `ModelType`, treating the model root as an anonymous container rather than a `NamedReferenceableType`.

Secondary gaps (missing `xml:lang`, missing `xsi:schemaLocation`, unbundled XSD files) do not individually block import but collectively reduce interoperability confidence and prevent programmatic XSD validation.

## Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | **Add `<name>` child to `<model>` root.** `serialize_model()` accepts an optional `model_name` parameter (default `"Untitled Model"`) and emits `<name xml:lang="en">{model_name}</name>` as the first child of `<model>`. | XSD `NamedReferenceableType` requires `NameGroup` with `minOccurs="1"`. This is the blocking defect. |
| 2 | **Default `xml:lang="en"` on all `<name>` and `<documentation>` elements.** The `LangStringType` in the XSD defines an optional `xml:lang` attribute. Archi always emits it. pyarchi will emit `xml:lang="en"` by default. A future API could expose locale control; for now, a module-level constant suffices. | Best practice for i18n. Matches Archi's output. Minimizes diff noise when round-tripping through both tools. |
| 3 | **Add `xsi:schemaLocation` to `<model>` root.** Use the value already defined in `registry.ARCHIMATE_SCHEMA_LOCATION`. | Enables downstream XML tools to locate the schema. Archi emits it; matching their output reduces false differences. |
| 4 | **Bundle the three XSD files in `src/pyarchi/serialization/schema/`.** Files: `archimate3_Model.xsd`, `archimate3_View.xsd`, `archimate3_Diagram.xsd`. Copied from `examples/` at build time or committed directly. | `validate_exchange_format()` (ADR-031 Decision 8) currently raises `FileNotFoundError` because the schema directory is empty. Bundling makes validation self-contained with no network dependency. |
| 5 | **Validation-before-export is opt-in, not automatic.** Consistent with ADR-031 Decision 8. However, the `pet_shop` example script should demonstrate calling `validate_exchange_format()` after serialization as a best-practice pattern. | Automatic validation on every write adds latency and couples the write path to XSD parsing. Opt-in keeps the fast path fast while making correctness easy to verify. |
| 6 | **`<organizations>` section: preserve on round-trip, omit on fresh export.** The XSD makes `<organizations>` optional. Archi emits a folder hierarchy in this section, but it accepts imports without one. Existing opaque-XML preservation (ADR-031 Decision 7) already handles round-trip. No generation logic needed. | Generating a synthetic folder hierarchy adds complexity with no interop benefit. Archi creates its own folder structure on import regardless. |
| 7 | **Archi native `.archimate` format is out of scope.** The native format uses namespace `http://www.archimatetool.com/archimate` and a completely different element structure (attributes instead of sub-elements, `archimate:` type prefixes, folder-based layout). A separate serializer would be required. Deferred to a future epic. | EPIC-028 targets the Open Group Exchange Format, which is the standard interop channel. Supporting a proprietary format is a distinct concern. |
| 8 | **Deserialization tolerates `xml:lang` on `<name>` elements.** `_deserialize_element` and `_deserialize_relationship` already extract `name_node.text` and ignore attributes. No structural change needed, but the opaque-preservation skip-list in `deserialize_model` must continue to include `"name"` so model-level `<name>` nodes are not captured as opaque XML. | Files exported by Archi (and now by pyarchi itself) carry `xml:lang`. The deserializer must not choke on it or misinterpret it. |

## Consequences

### Positive

- pyarchi output will pass XSD validation, removing the blocking import failure in Archi.
- `validate_exchange_format()` becomes functional, giving users a self-service correctness check.
- `xml:lang` emission aligns with i18n best practices and reduces diff noise against Archi exports.
- No changes to the metamodel layer or public API surface. All fixes are contained within `pyarchi.serialization`.

### Negative

- Bundling three XSD files adds approximately 100 KB to the package distribution.
- The `xml:lang="en"` default is an assumption. Models authored in other languages will need a future API to override the locale. This is acceptable for an initial release.
- `serialize_model()` gains a new parameter (`model_name`), which is a minor API addition that existing callers do not need to change (default value preserves backward compatibility).
