---
project: pyarchi
phase: 2
last_updated: 2026-03-24
total_epics: 14
total_features: 52
total_stories: 199
---

# pyarchi Backlog

---

## Phase 1 — Completed

Phase 1 covered Requirements 1 through 5: project scaffold, scope and conformance, root type hierarchy, language structure and classification framework, abstract element hierarchy, all eleven relationships, Junction, and the derivation engine.

All 6 epics (EPIC-000 through EPIC-005), 24 features, and 96 stories are complete.
Detailed history is preserved in git (branch `develop`, up to commit `e0e2e69`).

| Epic | Title | Status |
|------|-------|--------|
| EPIC-000 | Project Scaffold and Build System | Complete |
| EPIC-001 | Scope and Conformance (Requirement 1) | Complete |
| EPIC-002 | Definitions and Root Type Hierarchy (Requirement 2) | Complete |
| EPIC-003 | Language Structure and Classification Framework (Requirement 3) | Complete |
| EPIC-004 | Generic Metamodel -- Abstract Element Hierarchy (Requirement 4) | Complete |
| EPIC-005 | Relationships and Relationship Connectors (Requirement 5) | Complete |

---

## Phase 2 — Layer-Specific Element Types

Phase 2 covers Requirements 6 through 13: concrete element classes for all ArchiMate layers, cross-layer relationship rules, and the Implementation & Migration layer.

---

## [EPIC-006] Strategy Layer Elements (Requirement 12)
**Status:** To-Do
**Priority:** High

### [FEAT-06.1] Strategy Abstract Bases
- [ ] [STORY-06.1.1] Define `StrategyStructureElement(StructureElement)` as an ABC with `layer = Layer.STRATEGY`, `aspect = Aspect.ACTIVE_STRUCTURE`
- [ ] [STORY-06.1.2] Define `StrategyBehaviorElement(BehaviorElement)` as an ABC with `layer = Layer.STRATEGY`, `aspect = Aspect.BEHAVIOR`
- [ ] [STORY-06.1.3] Write tests asserting direct instantiation of each ABC raises `TypeError`

### [FEAT-06.2] Strategy Structure Elements
- [ ] [STORY-06.2.1] Define `Resource(StrategyStructureElement)` as a concrete class with `_type_name = "Resource"`
- [ ] [STORY-06.2.2] Wire `layer` and `aspect` ClassVars on `Resource`
- [ ] [STORY-06.2.3] Attach `NotationMetadata` to `Resource` (corner_shape, layer_color, badge_letter="S")
- [ ] [STORY-06.2.4] Write test: `Resource` can be instantiated; `isinstance(Resource(...), StrategyStructureElement)` is `True`
- [ ] [STORY-06.2.5] Write test: `isinstance(Resource(...), ActiveStructureElement)` is `False`

### [FEAT-06.3] Strategy Behavior Elements
- [ ] [STORY-06.3.1] Define `Capability(StrategyBehaviorElement)` as a concrete class with `_type_name = "Capability"`
- [ ] [STORY-06.3.2] Define `ValueStream(StrategyBehaviorElement)` as a concrete class with `_type_name = "ValueStream"`
- [ ] [STORY-06.3.3] Define `CourseOfAction(BehaviorElement)` as a concrete class with `layer = Layer.STRATEGY`, `aspect = Aspect.BEHAVIOR`, `_type_name = "CourseOfAction"` -- note: NOT a subclass of `StrategyBehaviorElement`
- [ ] [STORY-06.3.4] Wire `layer` and `aspect` ClassVars on `Capability`, `ValueStream`, `CourseOfAction`
- [ ] [STORY-06.3.5] Attach `NotationMetadata` to `Capability`, `ValueStream`, `CourseOfAction`
- [ ] [STORY-06.3.6] Write test: all three classes can be instantiated without error
- [ ] [STORY-06.3.7] Write test: `isinstance(CourseOfAction(...), StrategyBehaviorElement)` is `False`
- [ ] [STORY-06.3.8] Write test: `Serving(source=Capability(...), target=Capability(...))` is valid (same-type serving)

---

## [EPIC-007] Business Layer Elements (Requirement 6)
**Status:** To-Do
**Priority:** High

### [FEAT-07.1] Business Abstract Bases
- [ ] [STORY-07.1.1] Define `BusinessInternalActiveStructureElement(InternalActiveStructureElement)` as an ABC with `layer = Layer.BUSINESS`, `aspect = Aspect.ACTIVE_STRUCTURE`
- [ ] [STORY-07.1.2] Define `BusinessInternalBehaviorElement(InternalBehaviorElement)` as an ABC with `layer = Layer.BUSINESS`, `aspect = Aspect.BEHAVIOR`
- [ ] [STORY-07.1.3] Define `BusinessPassiveStructureElement(PassiveStructureElement)` as an ABC with `layer = Layer.BUSINESS`, `aspect = Aspect.PASSIVE_STRUCTURE`
- [ ] [STORY-07.1.4] Write tests asserting direct instantiation of each ABC raises `TypeError`

### [FEAT-07.2] Business Active Structure Elements
- [ ] [STORY-07.2.1] Define `BusinessActor(BusinessInternalActiveStructureElement)` as a concrete class with `_type_name = "BusinessActor"`
- [ ] [STORY-07.2.2] Define `BusinessRole(BusinessInternalActiveStructureElement)` as a concrete class with `_type_name = "BusinessRole"`
- [ ] [STORY-07.2.3] Define `BusinessCollaboration(BusinessInternalActiveStructureElement)` as a concrete class with `_type_name = "BusinessCollaboration"`
- [ ] [STORY-07.2.4] Define `BusinessInterface(ExternalActiveStructureElement)` as a concrete class with `layer = Layer.BUSINESS`, `aspect = Aspect.ACTIVE_STRUCTURE`, `_type_name = "BusinessInterface"`
- [ ] [STORY-07.2.5] Wire `layer` and `aspect` ClassVars on all four classes
- [ ] [STORY-07.2.6] Attach `NotationMetadata` to all four classes (badge_letter="B")
- [ ] [STORY-07.2.7] Write test: all four classes can be instantiated without error
- [ ] [STORY-07.2.8] Write test: `isinstance(BusinessActor(...), InternalActiveStructureElement)` is `True`

### [FEAT-07.3] Business Behavior Elements
- [ ] [STORY-07.3.1] Define `BusinessProcess(BusinessInternalBehaviorElement, Process)` as a concrete class with `_type_name = "BusinessProcess"`
- [ ] [STORY-07.3.2] Define `BusinessFunction(BusinessInternalBehaviorElement, Function)` as a concrete class with `_type_name = "BusinessFunction"`
- [ ] [STORY-07.3.3] Define `BusinessInteraction(BusinessInternalBehaviorElement, Interaction)` as a concrete class with `_type_name = "BusinessInteraction"`
- [ ] [STORY-07.3.4] Define `BusinessEvent(Event)` as a concrete class with `layer = Layer.BUSINESS`, `aspect = Aspect.BEHAVIOR`, `_type_name = "BusinessEvent"`, `time: datetime | str | None = None`
- [ ] [STORY-07.3.5] Define `BusinessService(ExternalBehaviorElement)` as a concrete class with `layer = Layer.BUSINESS`, `aspect = Aspect.BEHAVIOR`, `_type_name = "BusinessService"`
- [ ] [STORY-07.3.6] Wire `layer` and `aspect` ClassVars on all five classes
- [ ] [STORY-07.3.7] Attach `NotationMetadata` to all five classes
- [ ] [STORY-07.3.8] Write test: all five classes can be instantiated without error
- [ ] [STORY-07.3.9] Write test: `BusinessInteraction` with fewer than 2 assigned elements raises `ValidationError`
- [ ] [STORY-07.3.10] Write test: `BusinessEvent` has `time` attribute defaulting to `None`

### [FEAT-07.4] Business Passive Structure Elements
- [ ] [STORY-07.4.1] Define `BusinessObject(BusinessPassiveStructureElement)` as a concrete class with `_type_name = "BusinessObject"`
- [ ] [STORY-07.4.2] Define `Contract(BusinessObject)` as a concrete class with `_type_name = "Contract"`
- [ ] [STORY-07.4.3] Define `Representation(BusinessPassiveStructureElement)` as a concrete class with `_type_name = "Representation"`
- [ ] [STORY-07.4.4] Wire `layer` and `aspect` ClassVars on all three classes
- [ ] [STORY-07.4.5] Attach `NotationMetadata` to all three classes
- [ ] [STORY-07.4.6] Write test: all three classes can be instantiated without error
- [ ] [STORY-07.4.7] Write test: `isinstance(Contract(...), BusinessObject)` is `True`

### [FEAT-07.5] Business Composite Element
- [ ] [STORY-07.5.1] Define `Product(CompositeElement)` as a concrete class with `layer = Layer.BUSINESS`, `aspect = Aspect.COMPOSITE`, `_type_name = "Product"`
- [ ] [STORY-07.5.2] Wire `layer` and `aspect` ClassVars on `Product`
- [ ] [STORY-07.5.3] Attach `NotationMetadata` to `Product`
- [ ] [STORY-07.5.4] Write test: `Product` can be instantiated without error
- [ ] [STORY-07.5.5] Write test: `Product` accepts cross-layer members (e.g., `ApplicationService`) via aggregation/composition

---

## [EPIC-008] Application Layer Elements (Requirement 7)
**Status:** To-Do
**Priority:** High

### [FEAT-08.1] Application Abstract Bases
- [ ] [STORY-08.1.1] Define `ApplicationInternalActiveStructureElement(InternalActiveStructureElement)` as an ABC with `layer = Layer.APPLICATION`, `aspect = Aspect.ACTIVE_STRUCTURE`
- [ ] [STORY-08.1.2] Define `ApplicationInternalBehaviorElement(InternalBehaviorElement)` as an ABC with `layer = Layer.APPLICATION`, `aspect = Aspect.BEHAVIOR`
- [ ] [STORY-08.1.3] Write tests asserting direct instantiation of each ABC raises `TypeError`

### [FEAT-08.2] Application Active Structure Elements
- [ ] [STORY-08.2.1] Define `ApplicationComponent(ApplicationInternalActiveStructureElement)` as a concrete class with `_type_name = "ApplicationComponent"`
- [ ] [STORY-08.2.2] Define `ApplicationCollaboration(ApplicationInternalActiveStructureElement)` as a concrete class with `_type_name = "ApplicationCollaboration"`
- [ ] [STORY-08.2.3] Define `ApplicationInterface(ExternalActiveStructureElement)` as a concrete class with `layer = Layer.APPLICATION`, `aspect = Aspect.ACTIVE_STRUCTURE`, `_type_name = "ApplicationInterface"`
- [ ] [STORY-08.2.4] Wire `layer` and `aspect` ClassVars on all three classes
- [ ] [STORY-08.2.5] Attach `NotationMetadata` to all three classes (badge_letter="A")
- [ ] [STORY-08.2.6] Write test: all three classes can be instantiated without error
- [ ] [STORY-08.2.7] Write test: `ApplicationCollaboration` with fewer than 2 assigned elements raises `ValidationError`

### [FEAT-08.3] Application Behavior Elements
- [ ] [STORY-08.3.1] Define `ApplicationFunction(ApplicationInternalBehaviorElement, Function)` as a concrete class with `_type_name = "ApplicationFunction"`
- [ ] [STORY-08.3.2] Define `ApplicationInteraction(ApplicationInternalBehaviorElement, Interaction)` as a concrete class with `_type_name = "ApplicationInteraction"`
- [ ] [STORY-08.3.3] Define `ApplicationProcess(ApplicationInternalBehaviorElement, Process)` as a concrete class with `_type_name = "ApplicationProcess"`
- [ ] [STORY-08.3.4] Define `ApplicationEvent(Event)` as a concrete class with `layer = Layer.APPLICATION`, `aspect = Aspect.BEHAVIOR`, `_type_name = "ApplicationEvent"`, `time: datetime | str | None = None`
- [ ] [STORY-08.3.5] Define `ApplicationService(ExternalBehaviorElement)` as a concrete class with `layer = Layer.APPLICATION`, `aspect = Aspect.BEHAVIOR`, `_type_name = "ApplicationService"`
- [ ] [STORY-08.3.6] Wire `layer` and `aspect` ClassVars on all five classes
- [ ] [STORY-08.3.7] Attach `NotationMetadata` to all five classes
- [ ] [STORY-08.3.8] Write test: all five classes can be instantiated without error
- [ ] [STORY-08.3.9] Write test: `ApplicationInteraction` with fewer than 2 assigned elements raises `ValidationError`
- [ ] [STORY-08.3.10] Write test: `ApplicationEvent` has `time` attribute defaulting to `None`

### [FEAT-08.4] Application Passive Structure Element
- [ ] [STORY-08.4.1] Define `DataObject(PassiveStructureElement)` as a concrete class with `layer = Layer.APPLICATION`, `aspect = Aspect.PASSIVE_STRUCTURE`, `_type_name = "DataObject"`
- [ ] [STORY-08.4.2] Wire `layer` and `aspect` ClassVars on `DataObject`
- [ ] [STORY-08.4.3] Attach `NotationMetadata` to `DataObject`
- [ ] [STORY-08.4.4] Write test: `DataObject` can be instantiated without error
- [ ] [STORY-08.4.5] Write test: `Realization(source=DataObject(...), target=BusinessObject(...))` is valid (upward cross-layer)

---

## [EPIC-009] Technology Layer Elements (Requirement 8)
**Status:** To-Do
**Priority:** High

### [FEAT-09.1] Technology Abstract Bases
- [ ] [STORY-09.1.1] Define `TechnologyInternalActiveStructureElement(InternalActiveStructureElement)` as an ABC with `layer = Layer.TECHNOLOGY`, `aspect = Aspect.ACTIVE_STRUCTURE`
- [ ] [STORY-09.1.2] Define `TechnologyInternalBehaviorElement(InternalBehaviorElement)` as an ABC with `layer = Layer.TECHNOLOGY`, `aspect = Aspect.BEHAVIOR`
- [ ] [STORY-09.1.3] Write tests asserting direct instantiation of each ABC raises `TypeError`

### [FEAT-09.2] Technology Active Structure Elements
- [ ] [STORY-09.2.1] Define `Node(TechnologyInternalActiveStructureElement)` as a concrete class with `_type_name = "Node"`
- [ ] [STORY-09.2.2] Define `Device(Node)` as a concrete class with `_type_name = "Device"` (specialization of Node)
- [ ] [STORY-09.2.3] Define `SystemSoftware(Node)` as a concrete class with `_type_name = "SystemSoftware"` (specialization of Node)
- [ ] [STORY-09.2.4] Define `TechnologyCollaboration(TechnologyInternalActiveStructureElement)` as a concrete class with `_type_name = "TechnologyCollaboration"`
- [ ] [STORY-09.2.5] Define `TechnologyInterface(ExternalActiveStructureElement)` as a concrete class with `layer = Layer.TECHNOLOGY`, `aspect = Aspect.ACTIVE_STRUCTURE`, `_type_name = "TechnologyInterface"`
- [ ] [STORY-09.2.6] Define `Path(TechnologyInternalActiveStructureElement)` as a concrete class with `_type_name = "Path"`
- [ ] [STORY-09.2.7] Define `CommunicationNetwork(TechnologyInternalActiveStructureElement)` as a concrete class with `_type_name = "CommunicationNetwork"`
- [ ] [STORY-09.2.8] Wire `layer` and `aspect` ClassVars on all seven classes
- [ ] [STORY-09.2.9] Attach `NotationMetadata` to all seven classes (badge_letter="T")
- [ ] [STORY-09.2.10] Write test: all seven classes can be instantiated without error
- [ ] [STORY-09.2.11] Write test: `isinstance(Device(...), Node)` is `True`
- [ ] [STORY-09.2.12] Write test: `TechnologyCollaboration` with fewer than 2 assigned elements raises `ValidationError`

### [FEAT-09.3] Technology Behavior Elements
- [ ] [STORY-09.3.1] Define `TechnologyFunction(TechnologyInternalBehaviorElement, Function)` as a concrete class with `_type_name = "TechnologyFunction"`
- [ ] [STORY-09.3.2] Define `TechnologyProcess(TechnologyInternalBehaviorElement, Process)` as a concrete class with `_type_name = "TechnologyProcess"`
- [ ] [STORY-09.3.3] Define `TechnologyInteraction(TechnologyInternalBehaviorElement, Interaction)` as a concrete class with `_type_name = "TechnologyInteraction"`
- [ ] [STORY-09.3.4] Define `TechnologyEvent(Event)` as a concrete class with `layer = Layer.TECHNOLOGY`, `aspect = Aspect.BEHAVIOR`, `_type_name = "TechnologyEvent"`, `time: datetime | str | None = None`
- [ ] [STORY-09.3.5] Define `TechnologyService(ExternalBehaviorElement)` as a concrete class with `layer = Layer.TECHNOLOGY`, `aspect = Aspect.BEHAVIOR`, `_type_name = "TechnologyService"`
- [ ] [STORY-09.3.6] Wire `layer` and `aspect` ClassVars on all five classes
- [ ] [STORY-09.3.7] Attach `NotationMetadata` to all five classes
- [ ] [STORY-09.3.8] Write test: all five classes can be instantiated without error
- [ ] [STORY-09.3.9] Write test: `TechnologyInteraction` with fewer than 2 assigned elements raises `ValidationError`
- [ ] [STORY-09.3.10] Write test: `TechnologyEvent` has `time` attribute defaulting to `None`

### [FEAT-09.4] Technology Passive Structure Element
- [ ] [STORY-09.4.1] Define `Artifact(PassiveStructureElement)` as a concrete class with `layer = Layer.TECHNOLOGY`, `aspect = Aspect.PASSIVE_STRUCTURE`, `_type_name = "Artifact"`
- [ ] [STORY-09.4.2] Wire `layer` and `aspect` ClassVars on `Artifact`
- [ ] [STORY-09.4.3] Attach `NotationMetadata` to `Artifact`
- [ ] [STORY-09.4.4] Write test: `Artifact` can be instantiated without error
- [ ] [STORY-09.4.5] Write test: `Realization(source=Artifact(...), target=DataObject(...))` is valid (downward cross-layer)
- [ ] [STORY-09.4.6] Write test: `Realization(source=Artifact(...), target=ApplicationComponent(...))` is valid

---

## [EPIC-010] Physical Elements (Requirement 9)
**Status:** To-Do
**Priority:** High

### [FEAT-10.1] Physical Abstract Bases
- [ ] [STORY-10.1.1] Define `PhysicalActiveStructureElement(ActiveStructureElement)` as an ABC with `layer = Layer.PHYSICAL`, `aspect = Aspect.ACTIVE_STRUCTURE`
- [ ] [STORY-10.1.2] Define `PhysicalPassiveStructureElement(PassiveStructureElement)` as an ABC with `layer = Layer.PHYSICAL`, `aspect = Aspect.PASSIVE_STRUCTURE`
- [ ] [STORY-10.1.3] Write tests asserting direct instantiation of each ABC raises `TypeError`

### [FEAT-10.2] Physical Active Structure Elements
- [ ] [STORY-10.2.1] Define `Equipment(PhysicalActiveStructureElement)` as a concrete class with `_type_name = "Equipment"`
- [ ] [STORY-10.2.2] Define `Facility(PhysicalActiveStructureElement)` as a concrete class with `_type_name = "Facility"`
- [ ] [STORY-10.2.3] Define `DistributionNetwork(PhysicalActiveStructureElement)` as a concrete class with `_type_name = "DistributionNetwork"`
- [ ] [STORY-10.2.4] Wire `layer` and `aspect` ClassVars on all three classes
- [ ] [STORY-10.2.5] Attach `NotationMetadata` to all three classes (badge_letter="P")
- [ ] [STORY-10.2.6] Write test: all three classes can be instantiated without error
- [ ] [STORY-10.2.7] Write test: `Realization(source=DistributionNetwork(...), target=Path(...))` is valid

### [FEAT-10.3] Physical Passive Structure Element
- [ ] [STORY-10.3.1] Define `Material(PhysicalPassiveStructureElement)` as a concrete class with `_type_name = "Material"`
- [ ] [STORY-10.3.2] Wire `layer` and `aspect` ClassVars on `Material`
- [ ] [STORY-10.3.3] Attach `NotationMetadata` to `Material`
- [ ] [STORY-10.3.4] Write test: `Material` can be instantiated without error
- [ ] [STORY-10.3.5] Write test: `Assignment(source=Equipment(...), target=Material(...))` is valid (non-standard but permitted)

---

## [EPIC-011] Motivation Elements (Requirement 11)
**Status:** To-Do
**Priority:** High

### [FEAT-11.1] Motivation Intentional Elements
- [ ] [STORY-11.1.1] Define `Stakeholder(MotivationElement)` as a concrete class with `layer = Layer.MOTIVATION`, `aspect = Aspect.MOTIVATION`, `_type_name = "Stakeholder"`
- [ ] [STORY-11.1.2] Define `Driver(MotivationElement)` as a concrete class with `_type_name = "Driver"`
- [ ] [STORY-11.1.3] Define `Assessment(MotivationElement)` as a concrete class with `_type_name = "Assessment"`
- [ ] [STORY-11.1.4] Wire `layer` and `aspect` ClassVars on all three classes
- [ ] [STORY-11.1.5] Attach `NotationMetadata` to all three classes (badge_letter="M")
- [ ] [STORY-11.1.6] Write test: all three classes can be instantiated without error

### [FEAT-11.2] Motivation Goal-Oriented Elements
- [ ] [STORY-11.2.1] Define `Goal(MotivationElement)` as a concrete class with `_type_name = "Goal"`
- [ ] [STORY-11.2.2] Define `Outcome(MotivationElement)` as a concrete class with `_type_name = "Outcome"`
- [ ] [STORY-11.2.3] Define `Principle(MotivationElement)` as a concrete class with `_type_name = "Principle"`
- [ ] [STORY-11.2.4] Define `Requirement(MotivationElement)` as a concrete class with `_type_name = "Requirement"`
- [ ] [STORY-11.2.5] Define `Constraint(MotivationElement)` as a concrete class with `_type_name = "Constraint"`
- [ ] [STORY-11.2.6] Wire `layer` and `aspect` ClassVars on all five classes
- [ ] [STORY-11.2.7] Attach `NotationMetadata` to all five classes
- [ ] [STORY-11.2.8] Write test: all five classes can be instantiated without error
- [ ] [STORY-11.2.9] Write test: `Goal` and `Outcome` are distinct types (not subclasses of each other)
- [ ] [STORY-11.2.10] Write test: `Principle`, `Requirement`, and `Constraint` are distinct types

### [FEAT-11.3] Motivation Meaning and Value
- [ ] [STORY-11.3.1] Define `Meaning(MotivationElement)` as a concrete class with `_type_name = "Meaning"`
- [ ] [STORY-11.3.2] Define `Value(MotivationElement)` as a concrete class with `_type_name = "Value"`
- [ ] [STORY-11.3.3] Wire `layer` and `aspect` ClassVars on both classes
- [ ] [STORY-11.3.4] Attach `NotationMetadata` to both classes
- [ ] [STORY-11.3.5] Write test: both classes can be instantiated without error
- [ ] [STORY-11.3.6] Write test: `Association(source=Meaning(...), target=some_relationship)` is valid (Meaning associates with any Concept)

### [FEAT-11.4] Motivation Cross-Layer Validation Rules
- [ ] [STORY-11.4.1] Add permission table entries: only `BusinessActor`, `BusinessRole`, `BusinessCollaboration` may be `Assignment` source targeting `Stakeholder`
- [ ] [STORY-11.4.2] Add permission table entries: core structure/behavior elements may realize `Requirement`
- [ ] [STORY-11.4.3] Add permission table entries: `Influence` between motivation elements and core elements is permitted
- [ ] [STORY-11.4.4] Write test: `Assignment(source=ApplicationComponent(...), target=Stakeholder(...))` raises `ValidationError`
- [ ] [STORY-11.4.5] Write test: `Assignment(source=BusinessActor(...), target=Stakeholder(...))` is valid
- [ ] [STORY-11.4.6] Write test: `Influence(source=Assessment(...), target=Goal(...), sign=InfluenceSign.NEGATIVE)` is valid

---

## [EPIC-012] Implementation and Migration Layer Elements (Requirement 13)
**Status:** To-Do
**Priority:** High

### [FEAT-12.1] Implementation Behavior and Structure Elements
- [ ] [STORY-12.1.1] Define `WorkPackage(InternalBehaviorElement)` as a concrete class with `layer = Layer.IMPLEMENTATION_MIGRATION`, `aspect = Aspect.BEHAVIOR`, `_type_name = "WorkPackage"`, extra fields `start: datetime | str | None = None`, `end: datetime | str | None = None`
- [ ] [STORY-12.1.2] Define `Deliverable(PassiveStructureElement)` as a concrete class with `layer = Layer.IMPLEMENTATION_MIGRATION`, `aspect = Aspect.PASSIVE_STRUCTURE`, `_type_name = "Deliverable"`
- [ ] [STORY-12.1.3] Define `ImplementationEvent(Event)` as a concrete class with `layer = Layer.IMPLEMENTATION_MIGRATION`, `aspect = Aspect.BEHAVIOR`, `_type_name = "ImplementationEvent"`, `time: datetime | str | None = None`
- [ ] [STORY-12.1.4] Wire `layer` and `aspect` ClassVars on all three classes
- [ ] [STORY-12.1.5] Attach `NotationMetadata` to all three classes (badge_letter="I")
- [ ] [STORY-12.1.6] Write test: all three classes can be instantiated without error
- [ ] [STORY-12.1.7] Write test: `WorkPackage` has `start` and `end` attributes defaulting to `None`

### [FEAT-12.2] Plateau (Composite Element)
- [ ] [STORY-12.2.1] Define `Plateau(CompositeElement)` as a concrete class with `layer = Layer.IMPLEMENTATION_MIGRATION`, `aspect = Aspect.COMPOSITE`, `_type_name = "Plateau"`
- [ ] [STORY-12.2.2] Implement `members: list[Concept]` on `Plateau` accepting any core ArchiMate concept via aggregation/composition
- [ ] [STORY-12.2.3] Wire `layer` and `aspect` ClassVars on `Plateau`
- [ ] [STORY-12.2.4] Attach `NotationMetadata` to `Plateau`
- [ ] [STORY-12.2.5] Write test: `Plateau` can be instantiated without error
- [ ] [STORY-12.2.6] Write test: `Plateau` accepts any core element (e.g., `BusinessProcess`, `Requirement`) as a member

### [FEAT-12.3] Gap (Associative Element)
- [ ] [STORY-12.3.1] Define `Gap` class with mandatory `plateau_a: Plateau` and `plateau_b: Plateau` fields, `layer = Layer.IMPLEMENTATION_MIGRATION`, `_type_name = "Gap"`
- [ ] [STORY-12.3.2] Implement validation: `Gap` requires exactly two `Plateau` references; missing either raises `ValidationError`
- [ ] [STORY-12.3.3] Wire `layer` and `aspect` ClassVars on `Gap`
- [ ] [STORY-12.3.4] Attach `NotationMetadata` to `Gap`
- [ ] [STORY-12.3.5] Write test: `Gap(plateau_a=Plateau(...), plateau_b=Plateau(...))` is valid
- [ ] [STORY-12.3.6] Write test: `Gap` without both plateau references raises `ValidationError`

### [FEAT-12.4] Implementation & Migration Cross-Layer Validation
- [ ] [STORY-12.4.1] Emit `DeprecationWarning` when `Realization(source=WorkPackage, target=Deliverable)` is detected
- [ ] [STORY-12.4.2] Add permission table entries: `BusinessInternalActiveStructureElement` may be `Assignment` source targeting `WorkPackage`
- [ ] [STORY-12.4.3] Add permission table entries: `ImplementationEvent` may trigger/be triggered by `WorkPackage` or `Plateau`
- [ ] [STORY-12.4.4] Add permission table entries: `ImplementationEvent` may access `Deliverable`
- [ ] [STORY-12.4.5] Add permission table entries: `Deliverable` may realize any core concept
- [ ] [STORY-12.4.6] Write test: `Realization(source=WorkPackage(...), target=Deliverable(...))` emits `DeprecationWarning`
- [ ] [STORY-12.4.7] Write test: `Assignment(source=BusinessRole(...), target=WorkPackage(...))` is valid
- [ ] [STORY-12.4.8] Write test: `Triggering(source=ImplementationEvent(...), target=WorkPackage(...))` is valid

---

## [EPIC-013] Cross-Layer Relationship Rules (Requirement 10)
**Status:** To-Do
**Priority:** High

### [FEAT-13.1] Business -- Application Cross-Layer Serving
- [ ] [STORY-13.1.1] Add permission table entries: `Serving` from `ApplicationService` to any `BusinessBehaviorElement`
- [ ] [STORY-13.1.2] Add permission table entries: `Serving` from `ApplicationInterface` to `BusinessRole`
- [ ] [STORY-13.1.3] Add permission table entries: `Serving` from `BusinessService` to any `ApplicationBehaviorElement`
- [ ] [STORY-13.1.4] Add permission table entries: `Serving` from `BusinessInterface` to `ApplicationComponent`
- [ ] [STORY-13.1.5] Write test: `Serving(source=ApplicationService(...), target=BusinessProcess(...))` is valid
- [ ] [STORY-13.1.6] Write test: `Serving(source=BusinessService(...), target=ApplicationFunction(...))` is valid

### [FEAT-13.2] Application -- Technology Cross-Layer Serving
- [ ] [STORY-13.2.1] Add permission table entries: `Serving` from `TechnologyService` to any `ApplicationBehaviorElement`
- [ ] [STORY-13.2.2] Add permission table entries: `Serving` from `TechnologyInterface` to `ApplicationComponent`
- [ ] [STORY-13.2.3] Write test: `Serving(source=TechnologyService(...), target=ApplicationFunction(...))` is valid

### [FEAT-13.3] Cross-Layer Realization Rules
- [ ] [STORY-13.3.1] Add permission table entries: `Realization` from `ApplicationProcess`/`ApplicationFunction` to `BusinessProcess`/`BusinessFunction`
- [ ] [STORY-13.3.2] Add permission table entries: `Realization` from `DataObject` to `BusinessObject`
- [ ] [STORY-13.3.3] Add permission table entries: `Realization` from `TechnologyProcess`/`TechnologyFunction` to `ApplicationProcess`/`ApplicationFunction`
- [ ] [STORY-13.3.4] Add permission table entries: `Realization` from `Artifact` to `DataObject` and `Artifact` to `ApplicationComponent`
- [ ] [STORY-13.3.5] Write test: `Realization(source=ApplicationProcess(...), target=BusinessProcess(...))` is valid
- [ ] [STORY-13.3.6] Write test: `Realization(source=Artifact(...), target=DataObject(...))` is valid

### [FEAT-13.4] Cross-Layer Realization Prohibitions
- [ ] [STORY-13.4.1] Add prohibition: `Realization` targeting `BusinessActor`, `BusinessRole`, or `BusinessCollaboration` is forbidden
- [ ] [STORY-13.4.2] Write test: `Realization(source=ApplicationProcess(...), target=BusinessActor(...))` raises `ValidationError`
- [ ] [STORY-13.4.3] Write test: `Realization(source=ApplicationComponent(...), target=BusinessRole(...))` raises `ValidationError`
- [ ] [STORY-13.4.4] Write test: `Realization(source=ApplicationComponent(...), target=BusinessCollaboration(...))` raises `ValidationError`

### [FEAT-13.5] Cross-Layer Derivation
- [ ] [STORY-13.5.1] Ensure derivation engine supports multi-hop realization chains across layers (e.g., `BusinessObject <- DataObject <- Artifact`)
- [ ] [STORY-13.5.2] Write test: chained `Realization(Artifact -> DataObject)` and `Realization(DataObject -> BusinessObject)` produces derived `Realization(Artifact, BusinessObject)`
- [ ] [STORY-13.5.3] Write test: `Product` aggregation of `ApplicationService` does not raise `ValidationError`

---

## [EPIC-014] Public API Exports for Phase 2
**Status:** To-Do
**Priority:** Medium

### [FEAT-14.1] Update __init__.py Exports
- [ ] [STORY-14.1.1] Export all Strategy layer concrete classes from `src/pyarchi/__init__.py`
- [ ] [STORY-14.1.2] Export all Business layer concrete classes from `src/pyarchi/__init__.py`
- [ ] [STORY-14.1.3] Export all Application layer concrete classes from `src/pyarchi/__init__.py`
- [ ] [STORY-14.1.4] Export all Technology layer concrete classes from `src/pyarchi/__init__.py`
- [ ] [STORY-14.1.5] Export all Physical element concrete classes from `src/pyarchi/__init__.py`
- [ ] [STORY-14.1.6] Export all Motivation element concrete classes from `src/pyarchi/__init__.py`
- [ ] [STORY-14.1.7] Export all Implementation & Migration element concrete classes from `src/pyarchi/__init__.py`
- [ ] [STORY-14.1.8] Export all new layer-specific abstract bases from `src/pyarchi/__init__.py`
- [ ] [STORY-14.1.9] Update `__all__` list to include all Phase 2 types
- [ ] [STORY-14.1.10] Write test: every Phase 2 concrete class is importable from `pyarchi` top-level
