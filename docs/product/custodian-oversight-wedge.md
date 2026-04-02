# Custodian Oversight Wedge

## Core wedge
Vellum helps asset managers and asset owners compare OMS intent, IBOR operational state, and ABOR/CBOR outcomes to find errors, manage exceptions, and reduce reimbursement exposure.

This is the starting wedge because it is concrete, painful, explainable, and close to measurable economic value.

## Problem statement
Custodians are critical operating partners, but they are not infallible.
A manager or owner that misses a custodian error may end up with:
- financial loss
- operational disruption
- delayed settlement or accounting resolution
- client dissatisfaction
- reimbursement or make-whole exposure

In many firms, these checks are still handled through:
- spreadsheets
- email chains
- manual reconciliations
- tribal knowledge
- fragmented operating procedures

## What Vellum is trying to do first
Vellum is not trying to replace the custodian.
Vellum is trying to act as the independent control layer across the operating stack.

In the first version, Vellum should help teams:
- normalize OMS, IBOR, and ABOR/CBOR data into canonical contracts
- compare intent, operational state, and downstream outcome
- detect mismatches and breaks at the point they first appear
- route exceptions into clear workflows
- preserve evidence and rationale across all compared layers
- support faster and more consistent investigation

## Ideal initial buyer
The best early buyer is likely:
- a smaller or mid-sized asset manager
- a sophisticated asset owner
- an operations, middle-office, fund-accounting, or oversight leader

The product should stay implementable and low-friction for these buyers.
It should not assume a huge IT program or a multi-year enterprise transformation.

## Why this wedge is strong
This wedge is attractive because it has:
- real operational pain
- real cost of failure
- repeatable workflows
- explainable rules
- obvious audit and evidence needs
- a clean path from detection to workflow to operator assistance

It also creates a credible story for expansion into:
- broader middle-office controls
- fund accounting oversight
- settlement oversight
- operating model analytics
- anomaly detection
- AI-assisted investigation

## Day 1 product shape
The product hierarchy remains:
1. data contracts / dictionary across OMS, IBOR, and ABOR/CBOR
2. deterministic cross-stack comparison rules
3. workflow orchestration
4. AI assistance

That means the wedge is not "AI for ops" in the vague sense.
It is an operational control system with AI assist.

## Example first-use cases
- quantity mismatch between OMS/IBOR expectation and ABOR/CBOR outcome
- unexpected cash movement or missing cash activity
- trade lifecycle stall or unexpected status
- valuation mismatch with aligned quantity but inconsistent economic value
- corporate-action mismatch across layers
- missing-record mismatch where one layer has no corresponding event
- signoff or governance-state mismatch despite apparent operational resolution
- recurring reconciliation breaks that need triage and pattern visibility

## What success looks like
A strong first implementation should let an operations team say:
- we know what broke
- we know why it broke
- we know who owns the next step
- we know what evidence supports the case
- we can prove what happened later

That is much more valuable than a system that merely says something "looks anomalous."
