---
name: PRD and requirements document status
description: Current state of the REQUIREMENTS.md product requirements document for the pyarchi library
type: project
---

REQUIREMENTS.md was written to `/home/kiera/dev/pyarchi/docs/REQUIREMENTS.md` on 2026-03-23, based on the ArchiMate 3.2 Specification summary at `assets/archimate-spec-3.2.md` and detailed HTML files in `assets/archimate-spec-3.2/`.

The document covers all 14 requirement areas with source references, Pythonic translations, validation rules, and acceptance criteria.

**Why:** This is the foundational PRD for the pyarchi library; it must be kept in sync with the spec and updated as implementation progresses.

**How to apply:** When a developer asks about a specific element type or relationship rule, link them back to the relevant numbered requirement in REQUIREMENTS.md. When implementation decisions arise (e.g., class hierarchy choices), refer to the "Pythonic Translation" sections. When writing tests, use the "Acceptance Criteria" bullet points.

Implementation phases are defined in Appendix C of the document:
- Phase 1: Core metamodel and relationships (Requirements 1-5) — must be complete before anything else
- Phase 2: Business, Application, Technology, Physical layers + cross-layer rules (Requirements 6-10)
- Phase 3: Motivation, Strategy, Implementation & Migration layers (Requirements 11-13)
- Phase 4: Viewpoint mechanism (Requirement 14, mandatory per spec Section 1.3)
