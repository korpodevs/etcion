# ADR-042: Pattern Gap Analysis Design

**Status:** PROPOSED
**Date:** 2026-03-27
**Scope:** How `Pattern.gaps()` identifies elements that partially match a pattern but are missing required connections.

## Context

PM-7 requires finding elements that *should* match a pattern but don't due to missing connections. Example: "Find all BusinessServices that have no serving ApplicationService." This is the inverse of `match()` — instead of finding complete matches, find incomplete ones.

The design question: how to define what "should match" means when the pattern isn't fully satisfied.

GitHub Issue #7 in `korpodevs/etcion` tracks the implementation.

## Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Gap analysis is anchored on a single "root" node alias | A gap query asks "for each element matching node X, what connections from the pattern are missing?" Without an anchor, the combinatorics of partial matches explode. The anchor reduces the problem to: find all elements of the root type, then check whether each one participates in a full pattern match. |
| 2 | `Pattern.gaps(model, anchor="alias") -> list[GapResult]` | The `anchor` parameter names the pattern alias to scan. For each model element matching the anchor's type, if no complete match includes that element, it appears in the results with a list of missing connections. |
| 3 | `GapResult` is a frozen dataclass: `element: Concept`, `missing: list[str]` | `element` is the model concept at the anchor position. `missing` is a human-readable list of descriptions like `"No Serving edge to any ApplicationService"`. Detailed enough for reporting, not machine-parseable (machine consumers should use `match()` directly). |
| 4 | Implementation: set subtraction, not partial isomorphism | Find all elements of the anchor type (`elements_of_type`). Find all elements that appear as the anchor in a successful `match()`. The gap set is the difference. For each gap element, inspect `connected_to()` to generate the `missing` descriptions. This avoids the complexity of partial subgraph isomorphism. |

## Alternatives Considered

| Alternative | Rejected Because |
|-------------|-----------------|
| Full partial isomorphism (find all maximal partial matches) | NP-hard, no practical benefit over the anchor-based approach for the target use cases |
| Return `MatchResult` with `None` placeholders for missing nodes | Ambiguous semantics — a `None` could mean "no element of this type exists" or "exists but not connected correctly" |
| No anchor parameter (scan all aliases) | Combinatorial explosion — a 5-node pattern would scan every element of every type against every position |

## Consequences

- Gap analysis is efficient: O(E + M) where E = elements of the anchor type and M = number of full matches
- Users must choose which alias to anchor on, which is natural ("find BusinessServices missing their ApplicationService backing")
- The `missing` descriptions are for human consumption; programmatic consumers compose `match()` + `elements_of_type()` directly
