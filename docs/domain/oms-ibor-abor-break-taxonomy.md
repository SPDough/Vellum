# OMS / IBOR / ABOR / CBOR Break Taxonomy

## Purpose
This document defines the first-pass mismatch taxonomy for Vellum.

These break types are the operational categories Vellum should detect, classify, and route into deterministic workflows.

They are useful both for:
- product use-case definition
- rule design
- workflow routing
- operator investigation
- downstream analytics on exception patterns

## Core principle
Vellum should not just say that two systems differ.
It should classify how they differ, where the divergence first appears, and what kind of operational response the difference should trigger.

## Comparison surfaces
The taxonomy applies across:
- OMS → IBOR
- IBOR → ABOR/CBOR
- OMS → ABOR/CBOR

In some client environments, IBOR may remain a current-state comparison surface.
In Vellum's long-term architecture, many of these control functions should be handled directly in the Vellum layer between OMS and ABOR/CBOR.

## Break categories

### 1. Timing mismatch
A record or state is directionally consistent across layers, but appears at different times than expected.

Examples:
- trade appears in OMS but has not yet propagated to the next layer
- expected cash movement is delayed downstream
- position is correct by next cycle but not at the expected cutoff
- an accounting or custody update lags the investment-operational view

Operational meaning:
- may be benign
- often needs watchlist or monitor workflow rather than immediate escalation
- should be distinguished from true economic mismatch

### 2. Lifecycle mismatch
An item exists across layers but is in inconsistent process states.

Examples:
- OMS indicates executed, while downstream remains pre-booked
- IBOR reflects activity as processed while ABOR/CBOR remains unresolved
- settlement date has passed but lifecycle status remains pre-settlement
- corporate action is reflected in one layer but not advanced in another

Operational meaning:
- often indicates process stall, incomplete propagation, or status mapping issue
- strong candidate for SLA-driven workflow escalation

### 3. Reference / enrichment mismatch
The economic event may be the same, but descriptive or mapped data differs.

Examples:
- security identifier mapping mismatch
- account mapping inconsistency
- currency mismatch caused by reference-data handling
- strategy, sleeve, entity, or custodian account enrichment differs by layer
- tax lot, reason code, or transaction attribute is missing or inconsistent

Operational meaning:
- often reflects data quality or mapping governance issues
- may create false breaks if not handled carefully
- should feed data-quality remediation as well as case resolution

### 4. Quantity mismatch
The same position or transaction is represented with different quantities across layers.

Examples:
- OMS expected quantity does not match IBOR reflected quantity
- IBOR position differs from ABOR/CBOR position beyond tolerance
- partial booking or partial settlement leads to unexpected difference

Operational meaning:
- often a core break type
- should support tolerance logic, severity classification, and materiality assessment

### 5. Cash mismatch
Cash balances or cash activities differ across layers.

Examples:
- expected cash event missing downstream
- downstream cash amount differs from operational expectation
- value date or settlement date differs materially
- duplicate or offsetting cash event appears in one layer only

Operational meaning:
- high operational importance
- often tied to settlement, accounting, treasury, and reimbursement risk

### 6. Valuation mismatch
Quantities may agree while economic value differs.

Examples:
- same position but different market value
- stale price in one layer
- different valuation methodology across systems
- derivative or illiquid asset marked differently across views

Operational meaning:
- often a pricing, methodology, or timing issue rather than a position break
- should be separated from pure quantity mismatch for cleaner routing

### 7. Corporate-action mismatch
A dividend, split, merger, maturity, option event, or similar lifecycle event is handled differently across layers.

Examples:
- entitlement reflected in one layer but not another
- mandatory event posted inconsistently
- voluntary election not propagated correctly
- backdated corporate action changes subsequent records differently by system

Operational meaning:
- often high-complexity and high-confusion
- good candidate for specialized playbooks and reason codes

### 8. Missing-record mismatch
A record expected in one layer is absent in another.

Examples:
- OMS trade missing from downstream processing view
- IBOR record missing from ABOR/CBOR
- external/custody record present with no corresponding internal record
- event appears in accounting or custody data with no upstream explanation

Operational meaning:
- one of the clearest and most actionable break types
- often strong evidence of propagation, ingestion, mapping, or operating-model failure

### 9. Signoff / governance state mismatch
The underlying data may match, but the governance or operational control state does not.

Examples:
- break resolved operationally but not formally signed off
- adjustment posted without required approval
- reconciliation completed without evidence package
- workflow step advanced without required ownership or reason code

Operational meaning:
- critical for auditability and control integrity
- especially important in regulated and outsourced operating models

## Recommended classification dimensions
For each break, Vellum should ideally classify:
- break type
- source comparison surface
- first point of divergence
- severity / materiality
- confidence of match
- likely cause category
- owner / queue
- SLA status
- signoff requirement

## Product use-case framing
These break types support a strong product message:

**Vellum automates reconciliation across OMS, IBOR, and ABOR/CBOR, classifies only the meaningful exceptions, and routes them into governed workflows with evidence, ownership, and signoff.**

Short version:

**Match everything, escalate only exceptions.**

## Design implication
This taxonomy should influence:
- canonical contract design
- rule-definition examples
- reconciliation-break schema evolution
- workflow case routing rules
- internal knowledge and playbooks
- reporting on recurring exception patterns
