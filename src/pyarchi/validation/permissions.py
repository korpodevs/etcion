"""ArchiMate 3.2 Appendix B relationship permission table.

Encodes the normative relationship permission matrix and exposes a lookup
function: given a relationship type, source element type, and target element
type, returns whether the relationship is permitted by the specification.

TODO: EPIC-005, FEAT-05.11 -- encode Appendix B permission table and
      implement is_permitted(rel_type, source_type, target_type) -> bool.
"""
