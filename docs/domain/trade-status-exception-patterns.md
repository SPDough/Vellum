# Trade Status Exception Patterns

## Purpose
This note captures how Vellum should think about trade-status exceptions in the MVP.

## Why trade-status exceptions matter
Trade-status exceptions are often the earliest visible signals that the OMS → IBOR → ABOR/CBOR chain is drifting off course.
They are especially useful because they can be checked deterministically and turned into workflows quickly.

## Common exception patterns

### 1. Stalled lifecycle
The trade has not progressed from one expected state to the next within the expected time window.

Examples:
- allocated but not affirmed
- affirmed but not matched
- matched but not settled
- instructed but no downstream confirmation

### 2. Unexpected regression
A trade appears to move backward in status or returns to a prior unresolved state.

### 3. Contradictory system state
Two systems claim materially different lifecycle states for the same trade.

### 4. Missing trade in one system
Expected trade exists internally but not at the downstream provider, or vice versa.

### 5. Repeated fail pattern
A trade or strategy repeatedly encounters the same lifecycle exception pattern.

## MVP rule examples
- status not advanced within SLA window
- downstream trade record missing after expected publish time
- final status inconsistent across internal and provider record
- settlement date passed while status is still pre-settlement

## Workflow implications
When a trade-status exception is detected, Vellum should be able to:
- open an exception case
- attach the underlying trade-status evidence
- assign an owner
- route by product, desk, or provider
- capture follow-up actions and timestamps
- preserve a full audit trail

## Why this is useful early
Trade-status exceptions are a strong MVP area because they are:
- operationally important
- deterministic enough to model cleanly
- connected to real downstream pain
- good candidates for rule-plus-workflow automation

## Role of AI
AI can help summarize what happened and suggest next checks.
AI should not be the source of truth for whether a lifecycle breach exists.
