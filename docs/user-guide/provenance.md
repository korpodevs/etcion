# Provenance Metadata

Automated ingestion pipelines — ETL jobs, CMDB exports, LLM-assisted discovery — produce elements whose origin and reliability are not always clear from the model alone. The `etcion.provenance` module solves this by providing a ready-made profile that stamps every ingested element with four standard attributes, and three query helpers that let you filter the model by those attributes.

## What Is INGESTION_PROFILE?

`INGESTION_PROFILE` is a pre-built `Profile` instance named `"IngestionMetadata"`. Applying it to a model registers four extended attributes on all `Element` subclasses:

| Attribute | Type | Purpose |
|---|---|---|
| `_provenance_source` | `str` | Identifier of the pipeline or data source (e.g. `"cmdb"`, `"etl-pipeline-v2"`) |
| `_provenance_confidence` | `float` | Confidence score in the range `0.0`–`1.0` |
| `_provenance_reviewed` | `bool` | Whether a human reviewer has approved this element |
| `_provenance_timestamp` | `str` | ISO 8601 ingestion timestamp (e.g. `"2026-03-31T00:00:00Z"`) |

Because `INGESTION_PROFILE` uses the standard `Profile` mechanism, `model.validate()` type-checks every provenance attribute value automatically — no extra wiring required.

## Basic Usage

### Applying the Profile

Import `INGESTION_PROFILE` and apply it to the model before adding any elements that carry provenance metadata:

```python
from etcion import Model, BusinessActor
from etcion.provenance import INGESTION_PROFILE

model = Model()
model.apply_profile(INGESTION_PROFILE)
```

Both names are also exported from the top-level `etcion` package:

```python
from etcion import INGESTION_PROFILE
```

### Stamping an Element

Pass the four attributes in `extended_attributes` when constructing the element:

```python
actor = BusinessActor(
    name="Customer Record System",
    extended_attributes={
        "_provenance_source": "cmdb",
        "_provenance_confidence": 0.85,
        "_provenance_reviewed": False,
        "_provenance_timestamp": "2026-03-31T09:15:00Z",
    },
)
model.add(actor)

errors = model.validate()
assert errors == []
```

### What Happens Without the Profile

If you add an element with provenance attributes to a model that does not have `INGESTION_PROFILE` applied, `model.validate()` will report each undeclared attribute as an error:

```python
model_no_profile = Model()
actor = BusinessActor(
    name="Customer Record System",
    extended_attributes={"_provenance_source": "cmdb"},
)
model_no_profile.add(actor)

errors = model_no_profile.validate()
# errors == ["extended attribute '_provenance_source' is not declared in any profile"]
```

## The Four Standard Attributes

### `_provenance_source`

A free-form string identifying the system or pipeline that produced the element. Keep identifiers stable across runs so that `elements_by_source()` returns consistent results:

```python
# Good: stable identifiers
"_provenance_source": "cmdb"
"_provenance_source": "etl-pipeline-v2"

# Avoid: run-specific or ephemeral strings
"_provenance_source": "run_20260401_143512"
```

### `_provenance_confidence`

A float in the range `0.0`–`1.0`. Use it to express how reliable the ingested data is. There is no enforced range constraint at construction time; `low_confidence_elements()` works with whatever numeric scale you choose, but convention is `0.0` (no confidence) to `1.0` (certain):

```python
"_provenance_confidence": 0.95  # high confidence, likely correct
"_provenance_confidence": 0.4   # low confidence, needs review
```

### `_provenance_reviewed`

A boolean. Set it to `True` once a human has inspected the element and confirmed it is accurate. `unreviewed_elements()` treats both `False` and a missing key as unreviewed:

```python
"_provenance_reviewed": False  # pending human review
"_provenance_reviewed": True   # signed off
```

### `_provenance_timestamp`

An ISO 8601 string recording when the element was ingested. The library stores it as a plain `str` and does not parse or validate the format:

```python
"_provenance_timestamp": "2026-03-31T00:00:00Z"      # UTC
"_provenance_timestamp": "2026-03-31T10:30:00+01:00" # with offset
```

## Query Helpers

The three query helpers in `etcion.provenance` (and re-exported from `etcion`) all share the same filtering contract: elements with **no provenance attributes at all** are silently skipped. Only elements that carry at least one `_provenance_*` key are considered.

### `unreviewed_elements(model)`

Returns every provenance-tracked element that has not yet been reviewed:

```python
from etcion.provenance import unreviewed_elements

pending = unreviewed_elements(model)
print(f"{len(pending)} elements awaiting review")
for elem in pending:
    print(f"  {elem.name} — source: {elem.extended_attributes.get('_provenance_source')}")
```

An element is unreviewed when `_provenance_reviewed` is `False` **or** when the key is absent entirely. This means an element stamped with only `_provenance_source` and `_provenance_timestamp` is treated as unreviewed until someone explicitly sets `_provenance_reviewed: True`.

### `elements_by_source(model, source)`

Returns every provenance-tracked element whose `_provenance_source` matches the given string exactly:

```python
from etcion.provenance import elements_by_source

cmdb_elements = elements_by_source(model, "cmdb")
gpt_elements  = elements_by_source(model, "gpt4o")

print(f"Imported from CMDB: {len(cmdb_elements)}")
print(f"Generated by GPT-4o: {len(gpt_elements)}")
```

The match is case-sensitive and exact. There is no wildcard or prefix matching; use a list comprehension if you need partial matching:

```python
etl_elements = [
    e for e in model.elements
    if e.extended_attributes.get("_provenance_source", "").startswith("etl-")
]
```

### `low_confidence_elements(model, threshold=0.5)`

Returns every provenance-tracked element whose `_provenance_confidence` is strictly below `threshold`. The default threshold is `0.5`. Elements that have no `_provenance_confidence` key are skipped:

```python
from etcion.provenance import low_confidence_elements

# Use the default 0.5 threshold
uncertain = low_confidence_elements(model)

# Use a stricter threshold
very_uncertain = low_confidence_elements(model, threshold=0.7)

for elem in uncertain:
    score = elem.extended_attributes["_provenance_confidence"]
    print(f"  {elem.name}: confidence={score:.2f}")
```

## Common Patterns

### Full Ingestion Pipeline

A typical automated ingestion loop applies the profile once, then stamps each imported element:

```python
from etcion import Model, ApplicationComponent
from etcion.provenance import INGESTION_PROFILE

model = Model()
model.apply_profile(INGESTION_PROFILE)

TIMESTAMP = "2026-04-01T08:00:00Z"

raw_records = [
    {"name": "Auth Service",    "confidence": 0.90},
    {"name": "Billing Service", "confidence": 0.45},
    {"name": "Email Service",   "confidence": 0.30},
]

for record in raw_records:
    component = ApplicationComponent(
        name=record["name"],
        extended_attributes={
            "_provenance_source":     "cmdb",
            "_provenance_confidence": record["confidence"],
            "_provenance_reviewed":   False,
            "_provenance_timestamp":  TIMESTAMP,
        },
    )
    model.add(component)

errors = model.validate()
assert errors == []
```

### Triage Workflow

After ingestion, use the query helpers together to prioritise human review effort:

```python
from etcion.provenance import (
    low_confidence_elements,
    unreviewed_elements,
    elements_by_source,
)

# 1. Find everything still needing a reviewer
pending = unreviewed_elements(model)
print(f"Total unreviewed: {len(pending)}")

# 2. Prioritise uncertain ones first
urgent = low_confidence_elements(model, threshold=0.6)
print(f"Urgent (confidence < 0.6): {len(urgent)}")

# 3. Inspect a single source
cmdb_elements = elements_by_source(model, "cmdb")
print(f"From CMDB: {len(cmdb_elements)}")
```

### Marking Elements as Reviewed

The library does not provide a dedicated review API. Update `extended_attributes` directly after a human confirms an element:

```python
for elem in unreviewed_elements(model):
    # ... present elem for human approval ...
    elem.extended_attributes["_provenance_reviewed"] = True

# Confirm nothing is pending
assert unreviewed_elements(model) == []
```

### Combining with Standard Queries

The query helpers return plain lists of `Element` instances, so they compose naturally with list comprehensions and `model.elements_of_type()`:

```python
from etcion import BusinessActor
from etcion.provenance import low_confidence_elements

# Low-confidence Business Actors only
uncertain_actors = [
    e for e in low_confidence_elements(model, threshold=0.7)
    if isinstance(e, BusinessActor)
]
```

## API Summary

All names below are importable from `etcion.provenance` and from the top-level `etcion` package.

`INGESTION_PROFILE`
: Pre-built `Profile` instance (`name="IngestionMetadata"`) that declares the four standard provenance attributes on all `Element` subclasses.

`unreviewed_elements(model)`
: Returns `list[Element]`. Provenance-tracked elements where `_provenance_reviewed` is `False` or absent.

`elements_by_source(model, source)`
: Returns `list[Element]`. Provenance-tracked elements whose `_provenance_source` equals `source` exactly.

`low_confidence_elements(model, threshold=0.5)`
: Returns `list[Element]`. Provenance-tracked elements whose `_provenance_confidence` is strictly below `threshold`.

See also: [Profiles](profiles.md) — [API Reference: Provenance](../api/index.md)
