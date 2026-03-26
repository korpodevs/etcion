# ADR Index

This project records significant design decisions as **Architecture Decision
Records** (ADRs) stored in `docs/adr/`.  Each ADR captures the context,
decision, and consequences so that future contributors can understand *why* the
codebase is shaped the way it is.  The table below provides a quick-reference
index of every ADR in the repository.

| ID | Title | Status |
|----|-------|--------|
| ADR-001 | Package Configuration and Toolchain | ACCEPTED |
| ADR-002 | Module Layout | ACCEPTED |
| ADR-003 | ConformanceProfile | ACCEPTED |
| ADR-004 | Conformance Test Suite | ACCEPTED |
| ADR-005 | Undefined Type Guard | ACCEPTED |
| ADR-006 | Concept Abstract Base Class | ACCEPTED |
| ADR-007 | Element and Relationship Abstract Base Classes | ACCEPTED |
| ADR-008 | AttributeMixin | ACCEPTED |
| ADR-009 | RelationshipConnector Abstract Base Class | ACCEPTED |
| ADR-010 | Model Container | ACCEPTED |
| ADR-011 | Layer Enum Ratification | ACCEPTED |
| ADR-012 | Aspect Enum Ratification | ACCEPTED |
| ADR-013 | NotationMetadata Dataclass | ACCEPTED |
| ADR-014 | Classification Metadata on Elements | ACCEPTED |
| ADR-015 | Nesting Rendering Hint | ACCEPTED |
| ADR-016 | Generic Metamodel Abstract Element Hierarchy | ACCEPTED |
| ADR-017 | Relationships and Relationship Connectors | ACCEPTED |
| ADR-018 | Strategy Layer Elements | ACCEPTED |
| ADR-019 | Business Layer Elements | ACCEPTED |
| ADR-020 | Application Layer Elements | ACCEPTED |
| ADR-021 | Technology Layer Elements | ACCEPTED |
| ADR-022 | Physical Layer Elements | ACCEPTED |
| ADR-023 | Motivation Elements | ACCEPTED |
| ADR-024 | Implementation and Migration Layer Elements | ACCEPTED |
| ADR-025 | Cross-Layer Relationship Rules | ACCEPTED |
| ADR-026 | Public API Exports for Phase 2 | ACCEPTED |
| ADR-027 | Model-Level Validation Engine | ACCEPTED |
| ADR-028 | Declarative Relationship Permission Table | PROPOSED |
| ADR-029 | Viewpoint Mechanism | PROPOSED |
| ADR-030 | Language Customization Mechanism | PROPOSED |
| ADR-031 | Open Group Exchange Format Serialization | PROPOSED |
| ADR-032 | Conformance Cleanup and Phase 3 Public API | PROPOSED |
| ADR-033 | Archi Tool Interoperability | PROPOSED |
| ADR-034 | Performance Optimization | PROPOSED |
| ADR-035 | Predefined Viewpoint Catalogue | PROPOSED |
| ADR-036 | Model Querying and Filtering API | ACCEPTED |
| ADR-037 | Model Comparison and Diff Utilities | ACCEPTED |
| ADR-038 | Plugin and Extension System | ACCEPTED |
| ADR-039 | Documentation and API Reference | ACCEPTED |

!!! note "Regenerating this table"
    Run `python scripts/generate_adr_index.py` to regenerate the table from
    the current contents of `docs/adr/`.
