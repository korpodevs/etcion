# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 26 Mar 2026

### Added

- ArchiMate 3.2 metamodel: all element types across Business, Application,
  Technology, Strategy, Motivation, Implementation & Migration, and Composite layers.
- Complete relationship type system with source/target validation matrix.
- Open Group Exchange Format XML serialization and deserialization.
- XSD validation against bundled ArchiMate 3.1 schemas.
- Model comparison and diff utilities (`diff_models`).
- Conformance profiles (flag, standard, full).
- Opaque XML preservation for organizations and views during round-trip.
- Archi tool interoperability (import and export verified).
- PEP 561 `py.typed` marker for downstream type checking.
