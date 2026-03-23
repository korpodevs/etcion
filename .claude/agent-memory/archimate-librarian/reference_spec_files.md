---
name: ArchiMate 3.2 specification file locations
description: Where the ArchiMate 3.2 spec files live in the repo and how they are organized
type: reference
---

- Spec summary (Markdown, all chapters): `/home/kiera/dev/pyarchi/assets/archimate-spec-3.2.md`
- Detailed HTML chapter files: `/home/kiera/dev/pyarchi/assets/archimate-spec-3.2/`
  - `ch-introduction.html` — Chapter 1: Introduction, conformance clause
  - `ch-definitions.html` — Chapter 2: Formal definitions, root type union
  - `ch-language-structure.html` — Chapter 3: Layer/aspect framework, nesting, notation
  - `ch-generic-metamodel.html` — Chapter 4: Abstract element hierarchy, Grouping, Location
  - `ch-relationships-and-relationship-connectors.html` — Chapter 5: All 11 relationships + Junction + derivation
  - `ch-motivation-elements.html` — Chapter 6: Motivation layer elements
  - `ch-strategy-layer.html` — Chapter 7: Strategy layer elements
  - `ch-business-layer.html` — Chapter 8: Business layer elements
  - `ch-application-layer.html` — Chapter 9: Application layer elements
  - `ch-technology-layer.html` — Chapter 10: Technology + Physical elements
  - `ch-relationships-between-core-layers.html` — Chapter 11: Cross-layer relationship rules
  - `ch-implementation-and-migration-layer.html` — Chapter 12: I&M layer elements
  - `ch-stakeholders-architecture-views-and-viewpoints.html` — Chapter 13: Viewpoint mechanism

Anchor IDs in the HTML files follow the pattern `#sec-Section-Name` and `#ch-Chapter-Name`.
The normative relationship permission table (Appendix B) is referenced throughout but not present as a local HTML file.
