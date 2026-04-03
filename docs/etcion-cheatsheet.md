# etcion API Cheat Sheet

Python library implementing the ArchiMate 3.2 metamodel. Build, query, validate, diff, merge, and serialize enterprise architecture models as first-class Python data structures.

- **Package:** `etcion` (v0.11.0)
- **Python:** >=3.12
- **Core dep:** pydantic >=2.0
- **Spec:** ArchiMate 3.2 (`etcion.SPEC_VERSION == "3.2"`)

## Installation

```bash
pip install etcion                # core only (pydantic)
pip install etcion[xml]           # + lxml (XML Exchange Format)
pip install etcion[graph]         # + networkx (pattern matching, impact analysis, graph export)
pip install etcion[dataframe]     # + pandas
pip install etcion[parquet]       # + pandas + pyarrow
pip install etcion[duckdb]        # + pandas + duckdb
pip install etcion[dev]           # all of the above + pytest, mypy, ruff, etc.
```

---

## Core Type Hierarchy

```
Concept (ABC, BaseModel)          # id: str (default uuid4)
  |-- Element (ABC)               # name, description, documentation_url,
  |     |                         # specialization, extended_attributes
  |     |-- ActiveStructureElement
  |     |-- BehaviorElement
  |     |-- PassiveStructureElement
  |     |-- CompositeElement
  |     |-- MotivationElement
  |     |-- ... (60 concrete types below)
  |
  |-- Relationship (ABC)          # source: Concept, target: Concept,
  |     |                         # name, description, is_derived: bool
  |     |-- StructuralRelationship (category=STRUCTURAL, is_nested: bool)
  |     |-- DependencyRelationship (category=DEPENDENCY)
  |     |-- DynamicRelationship    (category=DYNAMIC)
  |     |-- OtherRelationship      (category=OTHER)
  |
  |-- RelationshipConnector (ABC) # id only, no name
        |-- Junction              # junction_type: JunctionType (AND|OR)
```

All classes are Pydantic BaseModel subclasses. `id` defaults to `str(uuid4())`.

---

## Enums

```python
from etcion import (
    Layer,                  # STRATEGY, MOTIVATION, BUSINESS, APPLICATION,
                            # TECHNOLOGY, PHYSICAL, IMPLEMENTATION_MIGRATION
    Aspect,                 # ACTIVE_STRUCTURE, BEHAVIOR, PASSIVE_STRUCTURE,
                            # MOTIVATION, COMPOSITE
    RelationshipCategory,   # STRUCTURAL, DEPENDENCY, DYNAMIC, OTHER
    AccessMode,             # READ, WRITE, READ_WRITE, UNSPECIFIED
    InfluenceSign,          # STRONG_POSITIVE("++"), POSITIVE("+"), NEUTRAL("0"),
                            # NEGATIVE("-"), STRONG_NEGATIVE("--")
    AssociationDirection,   # UNDIRECTED, DIRECTED
    JunctionType,           # AND, OR
    PurposeCategory,        # DESIGNING, DECIDING, INFORMING
    ContentCategory,        # DETAILS, COHERENCE, OVERVIEW
)
```

---

## Concrete Element Types (60 total)

### Strategy Layer
`Resource`, `Capability`, `ValueStream`, `CourseOfAction`

### Business Layer
`BusinessActor`, `BusinessRole`, `BusinessCollaboration`, `BusinessInterface`,
`BusinessProcess`, `BusinessFunction`, `BusinessInteraction`, `BusinessEvent`,
`BusinessService`, `BusinessObject`, `Contract`, `Representation`, `Product`

### Application Layer
`ApplicationComponent`, `ApplicationCollaboration`, `ApplicationInterface`,
`ApplicationFunction`, `ApplicationInteraction`, `ApplicationProcess`,
`ApplicationEvent`, `ApplicationService`, `DataObject`

### Technology Layer
`Node`, `Device`, `SystemSoftware`, `TechnologyCollaboration`,
`TechnologyInterface`, `Path`, `CommunicationNetwork`, `TechnologyFunction`,
`TechnologyProcess`, `TechnologyInteraction`, `TechnologyEvent`,
`TechnologyService`, `Artifact`

### Physical Layer
`Equipment`, `Facility`, `DistributionNetwork`, `Material`

### Motivation Layer
`Stakeholder`, `Driver`, `Assessment`, `Goal`, `Outcome`, `Principle`,
`Requirement`, `Constraint`, `Meaning`, `Value`

### Implementation & Migration Layer
`WorkPackage`, `Deliverable`, `ImplementationEvent`, `Plateau`, `Gap`

### Generic (no layer)
`Grouping`, `Location`

---

## Relationship Types

| Category   | Type             | Extra fields                                     |
|------------|------------------|--------------------------------------------------|
| Structural | `Composition`    | `is_nested: bool = False`                        |
| Structural | `Aggregation`    | `is_nested: bool = False`                        |
| Structural | `Assignment`     | `is_nested: bool = False`                        |
| Structural | `Realization`    | `is_nested: bool = False`                        |
| Dependency | `Serving`        | --                                               |
| Dependency | `Access`         | `access_mode: AccessMode = UNSPECIFIED`           |
| Dependency | `Influence`      | `sign: InfluenceSign | None`, `strength: str | None` |
| Dependency | `Association`    | `direction: AssociationDirection = UNDIRECTED`     |
| Dynamic    | `Triggering`     | --                                               |
| Dynamic    | `Flow`           | `flow_type: str | None`                           |
| Other      | `Specialization` | --                                               |

All relationships: `source: Concept`, `target: Concept`, `name: str`, `is_derived: bool = False`.

`Association` is universally permitted between any two concepts. Other relationships follow the ArchiMate 3.2 Appendix B permission table, enforced by `is_permitted()` at validation time.

---

## Model (the central container)

```python
from etcion import Model, BusinessActor, Serving, Layer, Aspect

model = Model()                          # or Model(concepts=[...])

# Add concepts
model.add(actor)                         # raises ValueError on duplicate ID

# Retrieve
concept = model[concept_id]              # KeyError if not found
len(model)                               # concept count
list(model)                              # iterate all concepts

# Query
model.concepts                           # list[Concept]
model.elements                           # list[Element]
model.relationships                      # list[Relationship]
model.elements_of_type(BusinessActor)    # includes subclasses
model.elements_by_layer(Layer.BUSINESS)
model.elements_by_aspect(Aspect.BEHAVIOR)
model.elements_by_name("CRM")           # substring match
model.elements_by_name("CRM.*", regex=True)
model.elements_where(lambda e: e.extended_attributes.get("risk") == "high")
model.relationships_of_type(Serving)

# Graph traversal
model.connected_to(concept)              # list[Relationship] touching concept
model.sources_of(concept)               # list[Concept] -> concept
model.targets_of(concept)               # concept -> list[Concept]

# Validation
errors: list[ValidationError] = model.validate()          # collect all
model.validate(strict=True)                                # raise on first

# Networkx (requires etcion[graph])
g = model.to_networkx()                  # networkx.MultiDiGraph (cached)
# node attrs: type, name, layer, aspect, concept
# edge attrs: type, name, rel_id, relationship

# Views
model.add_view(view)
model.views                              # list[View]

# Profiles
model.apply_profile(profile)
model.profiles                           # list[Profile]

# Custom validation rules
model.add_validation_rule(rule)
model.remove_validation_rule(rule)
```

---

## Profiles and Constraints

```python
from etcion import Profile, ApplicationService

# Bare type form (backward-compatible)
profile = Profile(
    name="MyProfile",
    specializations={ApplicationService: ["Microservice", "API Gateway"]},
    attribute_extensions={
        ApplicationService: {
            "owner": str,
            "tco": float,
        },
    },
)

# Constraint dict form (Issue #52)
profile = Profile(
    name="RiskManagement",
    attribute_extensions={
        ApplicationService: {
            "risk_score": {"type": str, "allowed": ["low", "medium", "high", "critical"]},
            "tco": {"type": float, "min": 0.0, "required": True},
            "owner": {"type": str, "required": True},
        },
    },
)

# Constraint dict keys: type (required), allowed (list), min, max, required (bool)

model.apply_profile(profile)

# Set extended attributes on elements
svc = ApplicationService(
    name="CRM",
    specialization="Microservice",
    extended_attributes={"risk_score": "high", "tco": 50000.0, "owner": "Team A"},
)

# profile.get_constraints(ApplicationService) -> dict[str, AttributeConstraint]
```

---

## Views and Viewpoints

```python
from etcion import Viewpoint, View, Concern, PurposeCategory, ContentCategory

vp = Viewpoint(
    name="Application Cooperation",
    purpose=PurposeCategory.DESIGNING,
    content=ContentCategory.COHERENCE,
    permitted_concept_types=frozenset({ApplicationComponent, Serving, Flow}),
)

view = View(governing_viewpoint=vp, underlying_model=model)
view.add(concept)          # raises ValidationError if type not permitted or not in model

# Materialize as independent model
filtered_model = view.to_model()
filtered_graph = view.to_networkx()      # requires etcion[graph]

# Predefined viewpoint catalogue
from etcion import VIEWPOINT_CATALOGUE   # ViewpointCatalogue instance

# Concern links stakeholders to viewpoints
concern = Concern(description="Data privacy", stakeholders=[...], viewpoints=[...])
```

---

## Pattern Matching (requires `etcion[graph]`)

```python
from etcion import Pattern, BusinessActor, BusinessRole, Assignment, Serving

# Build a pattern
pattern = (
    Pattern()
    .node("actor", BusinessActor)
    .node("role", BusinessRole)
    .edge("actor", "role", Assignment)
)

# With exact-match constraints
pattern = Pattern().node("actor", BusinessActor, name="Alice")

# With arbitrary predicates
pattern = pattern.where("actor", lambda e: e.name.startswith("A"))

# With declarative attr predicates (serializable)
# Operators: ==, !=, <, <=, >, >=, in, not_in
pattern = (
    Pattern()
    .node("svc", ApplicationService)
    .where_attr("svc", "risk_score", "==", "high")
    .where_attr("svc", "tco", ">=", 10000)
)

# Cardinality constraints
pattern = (
    Pattern()
    .node("comp", ApplicationComponent)
    .min_edges("comp", Serving, count=2, direction="outgoing")
    .max_edges("comp", Serving, count=5, direction="outgoing")
)

# Match
matches: list[MatchResult] = pattern.match(model)
for m in matches:
    actor = m["actor"]       # Concept instance (identity, not copy)

# Existence check (stops at first match)
pattern.exists(model)        # bool

# Gap analysis
gaps: list[GapResult] = pattern.gaps(model, anchor="actor")
for gap in gaps:
    gap.element              # the unmatched element
    gap.missing              # list[str] human-readable descriptions

# Composition
combined = pattern_a.compose(pattern_b)

# Serialization (lambdas NOT included)
d = pattern.to_dict()
pattern2 = Pattern.from_dict(d)

# Viewpoint-scoped pattern
pattern = Pattern(viewpoint=vp).node("svc", ApplicationService)

# Validation rules from patterns
from etcion.patterns import PatternValidationRule, RequiredPatternRule, AntiPatternRule

rule = PatternValidationRule(pattern=p, description="Pattern must exist")
rule = RequiredPatternRule(pattern=p, anchor="svc", description="Every svc needs backing")
rule = AntiPatternRule(pattern=p, description="This pattern is forbidden")
model.add_validation_rule(rule)
```

---

## Impact Analysis (requires `etcion[graph]`)

```python
from etcion import analyze_impact, chain_impacts, ImpactResult

# Remove scenario
result: ImpactResult = analyze_impact(model, remove=concept)
result: ImpactResult = analyze_impact(model, remove=concept, max_depth=2)
result: ImpactResult = analyze_impact(model, remove=concept, follow_types={Serving, Flow})

# Merge scenario (collapse multiple elements into target)
result = analyze_impact(model, merge=([elem_a, elem_b], target_elem))

# Replace scenario (swap old for new, rewires relationships)
result = analyze_impact(model, replace=(old_elem, new_elem))

# Add relationship scenario
result = analyze_impact(model, add_relationship=new_rel)

# Remove relationship scenario
result = analyze_impact(model, remove_relationship=existing_rel)

# Chain multiple impacts
combined = chain_impacts(result1, result2, result3)

# ImpactResult fields
result.affected              # tuple[ImpactedConcept, ...]
result.broken_relationships  # tuple[Relationship, ...]
result.resulting_model       # Model | None (the what-if model)
result.violations            # tuple[Violation, ...] (permission violations)

# ImpactedConcept fields
ic.concept                   # Concept
ic.depth                     # int (graph distance from changed concept)
ic.path                      # tuple[str, ...] (relationship IDs in path)

# Grouping helpers
result.by_layer()            # dict[Layer | None, list[ImpactedConcept]]
result.by_depth()            # dict[int, list[ImpactedConcept]]
len(result)                  # number of affected concepts
bool(result)                 # True if any affected
result.to_dict()             # JSON-serializable dict
```

---

## ModelBuilder (fluent construction API)

```python
from etcion import ModelBuilder

# Context manager (calls build() on clean exit)
with ModelBuilder() as b:
    crm = b.application_component("CRM System")
    db = b.data_object("Customer Database")
    b.access(crm, db, access_mode=AccessMode.READ_WRITE)
model = b.model

# Standalone
b = ModelBuilder()
crm = b.application_component("CRM System")
model = b.build(validate=True)        # validate=False to skip

# Element factories: b.<snake_case_type>(name, **kwargs) -> Element
# Examples: b.business_actor("Alice"), b.node("Server01"), b.goal("Reduce cost")
# Junction: b.junction(junction_type=JunctionType.AND) (no name arg)

# Relationship factories: b.<snake_case_type>(source, target, *, name="", **kwargs) -> Rel
# source/target can be Element instances or string IDs
# Examples: b.serving(comp, svc), b.access(comp, db, access_mode=AccessMode.READ)

# From dicts
b = ModelBuilder.from_dicts(
    elements=[
        {"type": "ApplicationComponent", "name": "CRM"},
        {"type": "DataObject", "name": "Customer DB", "id": "my-custom-id"},
    ],
    relationships=[
        {"type": "Access", "source": crm_id, "target": db_id, "access_mode": "Read"},
    ],
)
model = b.build()

# From DataFrames (requires etcion[dataframe])
b = ModelBuilder.from_dataframe(elements_df, relationships_df, type_column="type")
model = b.build()
```

All element factory methods (snake_case of class name):
`resource`, `capability`, `value_stream`, `course_of_action`,
`business_actor`, `business_role`, `business_collaboration`, `business_interface`,
`business_process`, `business_function`, `business_interaction`, `business_event`,
`business_service`, `business_object`, `contract`, `representation`, `product`,
`application_component`, `application_collaboration`, `application_interface`,
`application_function`, `application_interaction`, `application_process`,
`application_event`, `application_service`, `data_object`,
`node`, `device`, `system_software`, `technology_collaboration`,
`technology_interface`, `path`, `communication_network`, `technology_function`,
`technology_process`, `technology_interaction`, `technology_event`,
`technology_service`, `artifact`,
`equipment`, `facility`, `distribution_network`, `material`,
`stakeholder`, `driver`, `assessment`, `goal`, `outcome`, `principle`,
`requirement`, `constraint`, `meaning`, `value`,
`work_package`, `deliverable`, `implementation_event`, `plateau`, `gap`,
`grouping`, `location`

Relationship factory methods:
`composition`, `aggregation`, `assignment`, `realization`, `serving`,
`access`, `influence`, `association`, `triggering`, `flow`, `specialization`

---

## Diff and Merge

```python
from etcion import diff_models, merge_models, apply_diff, ModelDiff, MergeResult

# Diff
diff: ModelDiff = diff_models(model_a, model_b)
diff: ModelDiff = diff_models(model_a, model_b, match_by="type_name")  # match by (type, name)

diff.added       # tuple[Concept, ...] (in B but not A)
diff.removed     # tuple[Concept, ...] (in A but not B)
diff.modified    # tuple[ConceptChange, ...]
bool(diff)       # True if any changes
diff.summary()   # "ModelDiff: 3 added, 1 removed, 2 modified"
diff.to_dict()   # JSON-serializable

# ConceptChange
change.concept_id    # str
change.concept_type  # str
change.changes       # dict[str, FieldChange]
# FieldChange: field, old, new

# Merge
result: MergeResult = merge_models(base, fragment)
result = merge_models(base, fragment, strategy="prefer_fragment")
result = merge_models(base, fragment, strategy="fail_on_conflict")  # raises ValueError
result = merge_models(base, fragment, strategy="custom",
                      resolver=lambda base_c, frag_c, change: frag_c)
result = merge_models(base, fragment, match_by="type_name")

result.merged_model   # Model
result.conflicts      # tuple[ConceptChange, ...]
result.violations     # tuple[Violation, ...] (dangling endpoints)
bool(result)          # True if conflicts exist
result.summary()      # human-readable
result.to_dict()      # JSON-serializable

# Apply diff as patch
result: MergeResult = apply_diff(model, diff)
```

---

## Serialization

### XML Exchange Format (requires `etcion[xml]`)

```python
from etcion.serialization.xml import (
    serialize_model,      # (model, *, model_name="Untitled Model") -> etree._ElementTree
    deserialize_model,    # (tree: etree._ElementTree) -> Model
    write_model,          # (model, path, *, model_name="Untitled Model") -> None
    read_model,           # (path) -> Model
    validate_exchange_format,  # (tree) -> list[str]  (empty = valid)
)

write_model(model, "arch.xml", model_name="My Architecture")
model = read_model("arch.xml")
```

### JSON

```python
from etcion.serialization.json import (
    model_to_dict,    # (model, *, include_views=False) -> dict
    model_from_dict,  # (data: dict) -> Model
)

import json
data = model_to_dict(model, include_views=True)
json.dumps(data)  # all values are JSON-serializable
model = model_from_dict(data)
```

### CSV / TSV

```python
from etcion.serialization.csv import from_csv, to_csv

# Export
to_csv(model, "elements.csv", "relationships.csv")
to_csv(model, "elements.tsv", "relationships.tsv", delimiter="\t")

# Import
model = from_csv("elements.csv", "relationships.csv")
model = from_csv("elements.csv", delimiter="\t")

# Element CSV columns: type, id, name, documentation
# Relationship CSV columns: type, source, target, name
```

### DataFrame (requires `etcion[dataframe]`)

```python
from etcion.serialization.dataframe import (
    to_dataframe,        # (model) -> tuple[elements_df, relationships_df]
    from_dataframe,      # (elements_df, relationships_df?, *, type_column="type") -> Model
    to_flat_dataframe,   # (model) -> DataFrame  (denormalized, one row per rel)
    diff_to_dataframe,   # (diff: ModelDiff) -> DataFrame
    impact_to_dataframe, # (result: ImpactResult) -> DataFrame
)
```

### Parquet (requires `etcion[parquet]`)

```python
from etcion.serialization.parquet import to_parquet

to_parquet(model, "output")
# Creates: output_elements.parquet, output_relationships.parquet
```

### DuckDB (requires `etcion[duckdb]`)

```python
from etcion.serialization.duckdb_export import to_duckdb

to_duckdb(model, "arch.duckdb")
# Creates tables: elements, relationships
```

### Graph Export (requires `etcion[graph]`)

```python
from etcion import to_cytoscape_json, to_echarts_graph, LAYER_COLORS, ELEMENT_ICONS

graph = model.to_networkx()

# Cytoscape.js format
cyto = to_cytoscape_json(graph)
cyto = to_cytoscape_json(graph, color_map={"Business": "#FF0"})
# Returns: {"elements": {"nodes": [...], "edges": [...]}}

# Apache ECharts format
echarts = to_echarts_graph(graph)
# Returns: {"nodes": [...], "links": [...], "categories": [...]}

# LAYER_COLORS: dict[Layer, str]
# {Layer.STRATEGY: "#F5DEAA", Layer.BUSINESS: "#FFFFB5",
#  Layer.APPLICATION: "#B5FFFF", Layer.TECHNOLOGY: "#C9E7B7",
#  Layer.PHYSICAL: "#C9E7B7", Layer.MOTIVATION: "#CCCCFF",
#  Layer.IMPLEMENTATION_MIGRATION: "#FFE0E0"}

# ELEMENT_ICONS: dict[type[Element], str]
# Maps each concrete Element subclass to a short icon identifier string
# e.g. ApplicationComponent -> "component", BusinessActor -> "actor"
```

---

## Provenance

```python
from etcion import (
    INGESTION_PROFILE,           # Pre-built Profile for provenance attrs
    unreviewed_elements,         # (model) -> list[Element]
    elements_by_source,          # (model, source: str) -> list[Element]
    low_confidence_elements,     # (model, threshold=0.5) -> list[Element]
)

model.apply_profile(INGESTION_PROFILE)

elem = BusinessActor(
    name="Source System",
    extended_attributes={
        "_provenance_source": "cmdb-sync",
        "_provenance_confidence": 0.85,
        "_provenance_reviewed": False,
        "_provenance_timestamp": "2026-03-31T00:00:00Z",
    },
)
model.add(elem)

unreviewed = unreviewed_elements(model)
from_cmdb = elements_by_source(model, "cmdb-sync")
low_conf = low_confidence_elements(model, threshold=0.7)
```

---

## Validation

```python
from etcion import is_permitted, warm_cache, ValidationRule

# Check if a relationship is structurally permitted
is_permitted(Serving, ApplicationComponent, ApplicationService)  # True/False
warm_cache()  # pre-load the permission table (optional perf optimization)

# Custom validation rules implement the ValidationRule protocol:
# class ValidationRule(Protocol):
#     def validate(self, model: Model) -> list[ValidationError]: ...

model.add_validation_rule(rule)
errors = model.validate()
```

---

## Exceptions

```python
from etcion import PyArchiError, ValidationError, DerivationError, ConformanceError

# PyArchiError          -- base for all etcion errors
# ValidationError       -- relationship permission violations, profile violations
# DerivationError       -- relationship derivation errors
# ConformanceError      -- conformance profile violations
```

---

## Common Recipes

```python
# Build a model from scratch
with ModelBuilder() as b:
    app = b.application_component("Payment Service")
    svc = b.application_service("Process Payment")
    db = b.data_object("Transaction Log")
    b.serving(app, svc)
    b.access(app, db)
model = b.model

# Find all ApplicationComponents not serving anything
pattern = (
    Pattern()
    .node("comp", ApplicationComponent)
    .node("svc", ApplicationService)
    .edge("comp", "svc", Serving)
)
gaps = pattern.gaps(model, anchor="comp")

# What happens if we remove a component?
result = analyze_impact(model, remove=app)
for ic in result.affected:
    print(f"  {ic.concept.name} (depth {ic.depth})")

# Merge a fragment from another source
result = merge_models(model, fragment, strategy="prefer_fragment")
merged = result.merged_model

# Round-trip through JSON
from etcion.serialization.json import model_to_dict, model_from_dict
data = model_to_dict(model)
restored = model_from_dict(data)

# Export for BI
from etcion.serialization.dataframe import to_flat_dataframe
df = to_flat_dataframe(model)
```
