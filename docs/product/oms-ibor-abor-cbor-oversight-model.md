# OMS → IBOR → ABOR/CBOR Oversight Model

## Purpose
This document defines the industry-native operating model Vellum should align to in the MVP.

Rather than speaking only in generic front-office, middle-office, and back-office terms, Vellum should frame the comparison problem as:
- OMS
- IBOR
- ABOR / CBOR

This is the cleaner and more credible language for sophisticated buyers.

## Core model

### OMS
The Order Management System represents front-office intent and trade activity.

It typically captures:
- orders
- allocations
- executions
- portfolio manager and trader intent
- pre-trade and near-trade decision context

### IBOR
The Investment Book of Record represents the investment-centric operational view.

It typically captures:
- timely positions
- exposures
- cash state
- transaction-driven position changes
- a more current and investment-usable view than end-of-day accounting alone

IBOR should help the firm understand what it believes it owns, has traded, and is exposed to on an operationally useful basis.

### ABOR / CBOR
The Accounting Book of Record and Custody Book of Record represent downstream official or service-provider views.

These typically capture:
- accounting positions
- custody positions
- settled cash
- official books and records
- financial reporting and auditable state

ABOR and CBOR are not always the same thing, but for Vellum they often sit in the same comparison layer: the downstream book-of-record layer.

## Vellum's role
Vellum should compare:
- OMS → IBOR
- IBOR → ABOR/CBOR
- sometimes OMS → ABOR/CBOR directly for critical controls

The product should identify where divergence occurs and whether the issue is:
- timing mismatch
- lifecycle mismatch
- reference / enrichment mismatch
- quantity mismatch
- cash mismatch
- valuation mismatch
- corporate-action mismatch
- missing-record mismatch
- signoff / governance state mismatch

## Why IBOR matters in this model
IBOR is valuable because it provides a timely and investment-centric view of positions, exposures, and cash.

Useful practical signals:
- front office needs a more current view than accounting alone often provides
- IBOR can serve as the basis for reconciliation against custodians or accounting systems
- a well-designed IBOR supports front-office decisions, middle-office oversight, and downstream control activity
- firms often use IBOR to reduce dependence on delayed start-of-day or end-of-day back-office views

## Why ABOR/CBOR still matters
The downstream book still matters because it is often:
- the official accounting basis
- the auditable record
- the source for client reporting or financial statements
- the place where operational consequences become real

Vellum should not assume the most real-time view is automatically the authoritative one for every purpose.
Instead, authority depends on the task:
- investment decision support may lean on OMS/IBOR
- accounting sign-off may lean on ABOR
- custody verification may lean on CBOR
- control decisions should preserve the lineage across all three

## Example comparison patterns

### OMS → IBOR
- intended trade exists in OMS but is missing from IBOR
- allocation differs between OMS and IBOR
- expected position impact is not reflected in IBOR
- cash expectation from trade activity is absent in IBOR

### IBOR → ABOR/CBOR
- IBOR position differs from accounting or custodian position
- IBOR cash state differs from downstream cash record
- transaction lifecycle looks complete in IBOR but unresolved in ABOR/CBOR
- valuation, tax lot, or reference details diverge downstream

### OMS → ABOR/CBOR
- original intent does not match downstream settled outcome
- allocation or quantity mismatch survives through the stack
- an issue is invisible in the middle until it appears in the back

## Product implication
Vellum is not just a custodian checker.
It is a deterministic oversight layer across the operating stack.

A strong product statement is:

**Vellum compares OMS intent, IBOR operational state, and ABOR/CBOR outcomes to identify breaks, route exceptions, and reduce operational and reimbursement risk.**

## Control design implication
This framing should directly influence:
- contract design
- reconciliation-break modeling
- rule definitions
- workflow case structure
- evidence and lineage capture
- RAG retrieval structure

The system should preserve not just the final mismatch, but where the mismatch first appears in the chain.
