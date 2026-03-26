# Technical Brief: FEAT-26.3 -- Architecture Documentation

**Status:** Ready for Implementation
**ADR:** `docs/adr/ADR-039-epic026-documentation-api-reference.md`

## Stories

| Story | Description | File |
|-------|-------------|------|
| STORY-26.3.1 | ADR index page | `docs/architecture/adr-index.md` |
| STORY-26.3.2 | Class hierarchy diagram | `docs/architecture/overview.md` |
| STORY-26.3.3 | Permission matrix page | `docs/architecture/permission-matrix.md` |

## Page Content Outlines

### docs/architecture/overview.md

Sections:
- **Module Map** -- table mapping each `src/pyarchi/` module to its responsibility
- **Class Hierarchy** -- Mermaid diagram showing inheritance tree

Module map table:

| Module | Responsibility |
|--------|---------------|
| `metamodel/concepts.py` | Root ABCs: Concept, Element, Relationship |
| `metamodel/elements.py` | Abstract element hierarchy (ActiveStructure, Behavior, etc.) |
| `metamodel/business.py` | Business layer concrete elements |
| `metamodel/application.py` | Application layer concrete elements |
| `metamodel/technology.py` | Technology layer concrete elements |
| `metamodel/physical.py` | Physical layer concrete elements |
| `metamodel/strategy.py` | Strategy layer concrete elements |
| `metamodel/motivation.py` | Motivation layer concrete elements |
| `metamodel/implementation_migration.py` | Implementation & Migration layer elements |
| `metamodel/relationships.py` | All 11 relationship types + Junction |
| `metamodel/model.py` | Model container, QueryBuilder |
| `metamodel/viewpoints.py` | Viewpoint, View, Concern |
| `metamodel/viewpoint_catalogue.py` | Predefined viewpoint definitions |
| `metamodel/profiles.py` | Profile, Specialization, extended attributes |
| `metamodel/notation.py` | NotationMetadata |
| `metamodel/mixins.py` | Shared mixins |
| `validation/permissions.py` | Appendix B permission table, is_permitted() |
| `validation/rules.py` | ValidationRule base |
| `derivation/engine.py` | DerivationEngine |
| `serialization/xml.py` | XML serialization (Exchange Format) |
| `serialization/json.py` | JSON serialization |
| `serialization/registry.py` | Type registry for deserialization |
| `comparison.py` | diff_models(), ModelDiff, ConceptChange |
| `conformance.py` | ConformanceProfile |
| `enums.py` | Layer, Aspect, AccessMode, etc. |
| `exceptions.py` | PyArchiError hierarchy |

Mermaid class hierarchy diagram (use `pymdownx.superfences` with mermaid fence):

```
Concept
  +-- Element
  |     +-- ActiveStructureElement
  |     |     +-- ExternalActiveStructureElement
  |     |     +-- InternalActiveStructureElement
  |     +-- BehaviorElement
  |     |     +-- ExternalBehaviorElement
  |     |     +-- InternalBehaviorElement
  |     |     +-- Event
  |     +-- PassiveStructureElement
  |     +-- CompositeElement
  |     +-- MotivationElement
  |     +-- StructureElement
  +-- Relationship
  |     +-- StructuralRelationship
  |     +-- DependencyRelationship
  |     +-- DynamicRelationship
  |     +-- OtherRelationship
  +-- RelationshipConnector
        +-- Junction
```

Render this as a Mermaid `classDiagram` with concrete elements shown as leaves under each abstract node. Keep the diagram to two levels deep for readability; link to API reference for full details.

### docs/architecture/adr-index.md

Sections:
- **Overview** -- one paragraph explaining ADR practice
- **Index** -- auto-generated table from `docs/adr/` directory

Table columns:

| ID | Title | Status | Date |
|----|-------|--------|------|

**Generation approach:** Write a simple Python script (`scripts/generate_adr_index.py`) that:
1. Globs `docs/adr/ADR-*.md`
2. Extracts ID from filename, title from first `# ` line
3. Scans for `## Decision` or `## Status` to determine status (default: Accepted)
4. Outputs a markdown table

Alternatively, hand-maintain the table (31 ADRs is manageable). Prefer the script for accuracy.

ADR files to index (current count): all `docs/adr/ADR-*.md` files.

### docs/architecture/permission-matrix.md

Sections:
- **Overview** -- explanation of Appendix B and how pyarchi enforces it
- **How to Read the Matrix** -- legend for P (permitted), D (derived), blank
- **Permission Table** -- rendered from `validation/permissions.py` data
- **Usage** -- code example calling `is_permitted(source_type, rel_type, target_type)`

Table structure: rows = source element types, columns = relationship types, cells = P/D/blank. This is a large table (58 source types x 11 relationship types). Use a scrollable `div` or split into sub-tables by layer.

**Generation approach:** Write a script (`scripts/generate_permission_matrix.py`) that:
1. Imports the permission data from `pyarchi.validation.permissions`
2. Iterates all concrete element types and relationship types
3. Outputs a markdown table per layer

Alternatively, render the table statically in the markdown file. Prefer the script so the page stays in sync with code.

## mkdocs.yml Addition

Add Mermaid support to `mkdocs.yml` (in `markdown_extensions` and `plugins`):

```yaml
markdown_extensions:
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
```

## Files to Create

| File | Type |
|------|------|
| `docs/architecture/overview.md` | Markdown with Mermaid diagram |
| `docs/architecture/adr-index.md` | Markdown table (hand-written or generated) |
| `docs/architecture/permission-matrix.md` | Markdown with large table(s) |
| `scripts/generate_adr_index.py` | Optional helper script |
| `scripts/generate_permission_matrix.py` | Optional helper script |

## Verification

```bash
mkdocs build --strict   # all pages render, mermaid fences accepted
mkdocs serve             # visual review of diagram and tables
```
