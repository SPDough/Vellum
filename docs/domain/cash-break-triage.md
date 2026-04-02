# Cash Break Triage

## Purpose
This note describes how Vellum should think about cash-related breaks and why they matter operationally.

## What is a cash break?
A cash break is a mismatch between expected and observed cash state or cash movement.

Examples:
- a cash activity appears at the custodian but not internally
- an expected cash movement does not appear when expected
- value date differs from expectation
- amount differs beyond tolerance
- reference details are missing or inconsistent
- the same event is represented differently across systems

## Why cash breaks matter
Cash breaks are dangerous because they often cut across multiple functions at once:
- trade support
- settlement
- treasury or cash management
- fund accounting
- client reporting
- oversight and control

They can be small in size but high in downstream confusion.
They also create strong conditions for reimbursement exposure if not detected and resolved quickly.

## First-pass break dimensions
Vellum should classify cash breaks along a few simple dimensions:

### 1. Timing
- missing
- late
- early
- wrong value date

### 2. Amount
- exact mismatch
- tolerance breach
- sign reversal
- duplicate or offsetting pattern

### 3. Identity / reference data
- account mismatch
- currency mismatch
- security or transaction reference mismatch
- incomplete narrative / missing identifiers

### 4. Workflow state
- new
- under investigation
- awaiting counterparty response
- resolved
- escalated

## Suggested deterministic checks
Examples of rules that fit the MVP well:
- value date later than allowed threshold
- amount difference exceeds tolerance
- expected cash event missing after cutoff
- duplicate cash event detected within comparison window
- currency mismatch between expected and observed event

## Suggested operator workflow
1. identify the break and classify it
2. gather the source records and references
3. determine whether the issue is timing, amount, reference-data, or process-state related
4. assign owner and SLA
5. capture communication and evidence
6. resolve, escalate, or reimburse as needed
7. preserve reason and outcome for future pattern analysis

## Role of RAG and AI
RAG should help retrieve:
- internal triage guidance
- glossary or field definitions
- prior playbooks
- provider-specific documentation

LLMs can help:
- summarize the break
- draft outreach language
- explain likely causes

But the official break state and action path should still be driven by deterministic logic and workflow state.
