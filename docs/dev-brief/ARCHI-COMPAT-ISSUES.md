# Archi Compatibility Issues

Comparison of `examples/from_archi.archimate` (Archi native) vs `examples/pet_shop.archimate` (pyarchi export).

## Critical Finding: Two Different Formats

Archi's native `.archimate` format is **proprietary** and uses namespace `http://www.archimatetool.com/archimate`. The Open Group Exchange Format uses namespace `http://www.opengroup.org/xsd/archimate/3.0/`. These are completely different XML schemas.

**Archi can import the Open Group Exchange Format** via `File > Import > Open Exchange XML Model`, but the file extension should be `.xml`, not `.archimate`.

## Issue Matrix

| # | Issue | Our Format | Archi Native | Archi Exchange Import | Severity |
|---|---|---|---|---|---|
| 1 | **File extension** | `.archimate` | `.archimate` (native) | `.xml` (exchange) | High — rename to `.xml` for import |
| 2 | **Namespace** | `opengroup.org/.../3.0/` | `archimatetool.com/archimate` | `opengroup.org/.../3.0/` | OK for exchange import |
| 3 | **Model name** | Missing | `name="(new model)"` on root | Expected by Exchange Format | Medium |
| 4 | **Model version** | Missing | `version="5.0.0"` | Not required by Exchange Format | Low |
| 5 | **ID attr name** | `identifier` | `id` | `identifier` (Exchange) | OK for exchange |
| 6 | **Element name** | `<name>` sub-element | `name=""` attribute | `<name>` sub-element (Exchange) | OK for exchange |
| 7 | **Type names** | `xsi:type="Influence"` | `xsi:type="archimate:InfluenceRelationship"` | Exchange uses unprefixed, may need "Relationship" suffix | **Needs verification** |
| 8 | **Folder structure** | Flat `<elements>`/`<relationships>` | `<folder type="business">` hierarchy | Exchange uses flat | OK for exchange |
| 9 | **Relationship tag** | `<relationship>` | `<element>` (inside Relations folder) | `<relationship>` (Exchange) | OK for exchange |
| 10 | **Model name element** | Missing `<name>` on model root | N/A | Exchange expects `<name>` sub-element on `<model>` | Medium |
| 11 | **schemaLocation** | Missing | N/A | Recommended for XSD validation | Low |
| 12 | **Property definitions** | Not implemented | N/A | Exchange supports `<propertyDefinitions>` | Low (Phase 4) |

## XSD + Archi Exchange Export Verification (2026-03-25)

Compared `pet_shop.xml` (pyarchi) with `pet_shop-from_archi.xml` (Archi exchange export) and `archimate3_Model.xsd`.

### CONFIRMED CORRECT (no action needed)

| Item | Status |
|---|---|
| `xsi:type` attribute placement | Correct |
| Element type names (`BusinessActor`, etc.) | Match XSD `ElementTypeEnum` exactly |
| Relationship type names (`Influence`, etc.) | Match XSD `RelationshipTypeEnum` exactly — no "Relationship" suffix |
| `accessType` attribute + values (`Read`, `Write`, `ReadWrite`) | Match XSD `AccessTypeEnum` |
| `modifier` attribute on Influence (not `strength`) | Match XSD `InfluenceModifierType` |
| Flat `<elements>`/`<relationships>` structure | Correct for Exchange Format |
| `identifier` attribute name | Matches XSD |
| `source`/`target` on relationships | Correct |
| ID format `id-{uuid-with-hyphens}` | Valid NCName per `xs:ID` type |

### ISSUES REQUIRING FIXES (likely cause of Archi import failure)

| # | Issue | Our Output | Archi Exchange Export | XSD Requirement | Fix |
|---|---|---|---|---|---|
| 1 | **Missing `<name>` on `<model>`** | No `<name>` child | `<name xml:lang="en">(new model)</name>` | `NameGroup` required by `RealElementType` — model inherits from `NamedReferenceableType` | Add `<name>` sub-element |
| 2 | **Missing `xsi:schemaLocation`** | Not present | `xsi:schemaLocation="http://www.opengroup.org/xsd/archimate/3.0/ http://www.opengroup.org/xsd/archimate/3.1/archimate3_Diagram.xsd"` | Recommended | Add attribute |
| 3 | **`<name>` lacks `xml:lang`** | `<name>Pet Shop Owner</name>` | `<name xml:lang="en">Pet Shop Owner</name>` | `LangStringType` has optional `xml:lang` | Add `xml:lang="en"` default |
| 4 | **Missing `<organizations>` section** | Not present | Contains folder/item hierarchy with `identifierRef` | Optional per XSD but Archi may expect it | Investigate |
| 5 | **Empty relationship elements not self-closing** | `<relationship ...>\n    </relationship>` | `<relationship ... />` (self-closing when no children) | Cosmetic | Low priority |

### Likely Root Cause of Import Failure

Issue #1 (missing model `<name>`) is the most probable cause. The XSD's `ModelType` extends `NamedReferenceableType` which requires at least one `<name>` element. Without it, XSD validation fails and Archi rejects the file.

## Recommendations for EPIC-028

### FEAT-28.1 (Exchange Format Fixes — HIGH priority)
1. Add `<name xml:lang="en">` sub-element on `<model>` root
2. Add `xml:lang="en"` to all `<name>` and `<documentation>` sub-elements
3. Add `xsi:schemaLocation` attribute on `<model>` root
4. Bundle the 3 XSD files from `examples/` into `src/pyarchi/serialization/schema/`
5. Validate our output against the bundled XSD before claiming success
6. Update `_deserialize_element` to handle `xml:lang` on `<name>` during read

### FEAT-28.2 (Archi Import Validation)
7. Re-test Archi import after fixes above
8. Investigate whether Archi requires `<organizations>` section
9. Document the import workflow for users
