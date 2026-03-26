# Diffing

Compare two model versions to find additions, removals, and field-level changes.

## diff_models()

`diff_models()` compares a baseline model against a revised model:

```python
from pyarchi import diff_models

diff = diff_models(model_v1, model_v2)
print(diff.summary())
# "ModelDiff: 2 added, 1 removed, 3 modified"
```

By default, concepts are matched by `id`. Use `match_by="type_name"` to match by `(type, name)` tuple instead:

```python
diff = diff_models(model_v1, model_v2, match_by="type_name")
```

## ModelDiff

The returned `ModelDiff` is a frozen dataclass with three fields:

- `diff.added` -- tuple of concepts present only in model_b
- `diff.removed` -- tuple of concepts present only in model_a
- `diff.modified` -- tuple of `ConceptChange` for concepts with field differences

```python
for concept in diff.added:
    print(f"+ {type(concept).__name__}: {concept.name}")

for concept in diff.removed:
    print(f"- {type(concept).__name__}: {concept.name}")
```

`ModelDiff` is falsy when models are identical:

```python
if not diff:
    print("Models are identical")
```

## ConceptChange and FieldChange

Each modified concept produces a `ConceptChange` containing a dict of `FieldChange` objects:

```python
for change in diff.modified:
    print(f"~ {change.concept_type} ({change.concept_id}):")
    for field_name, fc in change.changes.items():
        print(f"    {field_name}: {fc.old!r} -> {fc.new!r}")
```

## Serializing Diffs

Convert a diff to a JSON-compatible dict:

```python
import json
print(json.dumps(diff.to_dict(), indent=2))
```

Or get a one-line summary:

```python
print(diff.summary())
```

See also: [`examples/model_diff.py`](../examples/index.md)
