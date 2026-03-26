# Technical Brief: FEAT-26.2 -- User Guide

**Status:** Ready for Implementation
**ADR:** `docs/adr/ADR-039-epic026-documentation-api-reference.md`

## Stories

| Story | Description | File |
|-------|-------------|------|
| STORY-26.2.1 | Getting Started guide | `docs/getting-started.md` |
| STORY-26.2.2 | Serialization guide | `docs/user-guide/serialization.md` |
| STORY-26.2.3 | Validation guide | `docs/user-guide/validation.md` |
| STORY-26.2.4 | Viewpoints guide | `docs/user-guide/viewpoints.md` |
| STORY-26.2.5 | Language Customization guide | `docs/user-guide/profiles.md` |

## Additional Pages (from ADR-039 D3, no separate stories)

| File | Topic |
|------|-------|
| `docs/index.md` | Landing page (mirrors README quick start) |
| `docs/user-guide/building-models.md` | Elements, relationships, Junction, Model container |
| `docs/user-guide/querying.md` | QueryBuilder, filtering, traversal |
| `docs/user-guide/diffing.md` | diff_models(), ConceptChange, FieldChange |
| `docs/user-guide/extending.md` | Plugin system, custom validators |
| `docs/examples/index.md` | Example gallery with links |

## Page Content Outlines

### docs/index.md
- Project tagline and badges
- Feature bullet list (copy from README)
- Install snippet
- Quick Start code block (copy from README)
- Links to Getting Started, API Reference, User Guide

### docs/getting-started.md
- **Installation** -- `pip install pyarchi`, `pip install pyarchi[xml]`
- **Your First Model** -- create Model, add BusinessActor, BusinessService, Serving
- **Validating** -- `model.validate()`, handling ValidationError
- **Exporting to XML** -- `serialize_xml(model)`, viewing output
- **Next Steps** -- links to user guide sections

### docs/user-guide/building-models.md
- **Model Container** -- `Model()`, `model.elements`, `model.relationships`
- **Adding Elements** -- element types by layer, required fields (`name`)
- **Adding Relationships** -- source/target by ID, relationship types
- **Junction** -- combining relationships, JunctionType enum
- **Grouping and Location** -- cross-cutting elements
- Cross-ref: `examples/quick_start.py`

### docs/user-guide/validation.md
- **Model.validate()** -- what it checks (permission matrix, mandatory fields)
- **is_permitted()** -- standalone relationship check
- **ValidationError** -- inspecting error details
- **ValidationRule** -- custom rules
- Cross-ref: `examples/validation_demo.py`

### docs/user-guide/serialization.md
- **XML Export** -- `serialize_xml(model)`, Exchange Format compliance
- **XML Import** -- `deserialize_xml(path)`, round-trip guarantee
- **JSON Export/Import** -- `serialize_json(model)`, `deserialize_json(data)`
- **Archi Compatibility** -- notes on Archi tool interop
- Cross-ref: `examples/xml_roundtrip.py`

### docs/user-guide/viewpoints.md
- **Viewpoint** -- creating, setting allowed element/relationship types
- **View** -- associating elements with a viewpoint
- **Concern** -- linking concerns to viewpoints
- **Predefined Catalogue** -- `VIEWPOINT_CATALOGUE`, listing predefined viewpoints
- Cross-ref: `examples/viewpoint_filter.py`

### docs/user-guide/profiles.md
- **Profile** -- creating a profile, adding specializations
- **Specializations** -- extending element types with custom attributes
- **Extended Attributes** -- defining and accessing custom fields
- Cross-ref: `examples/profile_extension.py`

### docs/user-guide/querying.md
- **QueryBuilder** -- chaining filters on Model
- **Filter by Layer** -- `.layer(Layer.Business)`
- **Filter by Type** -- `.of_type(BusinessActor)`
- **Filter by Relationship** -- traversal queries
- Cross-ref: `examples/query_builder.py`

### docs/user-guide/diffing.md
- **diff_models()** -- comparing two Model instances
- **ModelDiff** -- interpreting added/removed/changed
- **ConceptChange / FieldChange** -- granular field-level diffs
- Cross-ref: `examples/model_diff.py`

### docs/user-guide/extending.md
- **Custom Validators** -- implementing ValidationRule
- **Registering Rules** -- adding to Model validation pipeline
- **Custom Element Types** -- subclassing (caveats and guidance)

### docs/examples/index.md

Table linking to each example file:

| Example | File | Features |
|---------|------|----------|
| Pet Shop | `examples/pet_shop.py` | Full model, all layers |
| Quick Start | `examples/quick_start.py` | Minimal 4-element model |
| Validation Demo | `examples/validation_demo.py` | Invalid model, error inspection |
| XML Round-Trip | `examples/xml_roundtrip.py` | Export, reimport, diff |
| Viewpoint Filter | `examples/viewpoint_filter.py` | Apply predefined viewpoint |
| Profile Extension | `examples/profile_extension.py` | Custom specialization |
| Query Builder | `examples/query_builder.py` | Filter chains |
| Model Diff | `examples/model_diff.py` | Compare versions |

## Example Scripts to Create

| File | Lines (approx) | Description |
|------|----------------|-------------|
| `examples/quick_start.py` | 30 | Model + 4 elements + 3 relationships |
| `examples/validation_demo.py` | 40 | Invalid relationship, catch error, print details |
| `examples/xml_roundtrip.py` | 35 | Serialize, deserialize, assert equality |
| `examples/viewpoint_filter.py` | 35 | Load catalogue viewpoint, check allowed types |
| `examples/profile_extension.py` | 40 | Create profile, add specialization, use extended attrs |
| `examples/query_builder.py` | 35 | Build queries, print results |
| `examples/model_diff.py` | 40 | Two model versions, diff, print changes |

Note: `examples/pet_shop.py` already exists.

## Verification

```bash
mkdocs build --strict          # all pages render without warnings
mkdocs serve                   # visual review at http://127.0.0.1:8000
python examples/quick_start.py # each example runs without error
```
