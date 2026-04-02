# Vellum Authority Order

## Purpose
This document defines what is allowed to decide, what is allowed to recommend, and what is only allowed to explain inside Vellum.

The product must remain deterministic-first. That is not just a technical preference; it is a product trust decision.

## Authority order
1. Canonical data contracts and data dictionary
2. Deterministic rules
3. Deterministic workflow orchestration and control objects
4. Retrieval (RAG)
5. LLM reasoning, explanation, drafting, and summarization

## What each layer does

### 1. Canonical data contracts and dictionary
This is the substrate.

Examples:
- position
- cash-activity
- cash-balance
- trade-status
- exception
- reconciliation-break
- workflow-case
- approval-request
- rule-definition
- rule-result

This layer defines what the system believes a thing is. If the dictionary is sloppy, the rest of the system will be sloppy.

### 2. Deterministic rules
Rules decide whether a condition is met.

Examples:
- value date is later than allowed
- position quantity exceeds tolerance
- trade status has not progressed in expected time
- cash movement lacks required reference data

Rules should be explicit, inspectable, versioned, and testable.

### 3. Deterministic workflows and control objects
Workflows decide what operational action should happen next.

Examples:
- create investigation case
- assign queue owner
- request supporting evidence
- escalate after SLA breach
- request approval before client-facing communication

Rules answer: "is something wrong?"
Workflows answer: "what do we do now?"

### 4. Retrieval (RAG)
RAG provides evidence, context, and operational guidance.
It does not override rules or workflows.

Examples:
- retrieve relevant SOP snippet
- retrieve custodian operating guidance
- retrieve prior internal playbook notes
- retrieve domain explanation for an operator

### 5. LLM reasoning / drafting / summarization
LLMs explain and help humans move faster.
They do not decide the official state of the platform.

Examples:
- summarize a break
- draft an outreach email
- explain why a rule fired
- suggest likely next investigative steps

## Product implication
Vellum should never silently allow a probabilistic model to overrule deterministic control logic.

If an LLM suggests a different outcome from a deterministic rule, the system should:
- keep the deterministic outcome authoritative
- surface the LLM output as commentary or recommendation only
- preserve lineage so a human can inspect both

## Why this matters
The product thesis is operational trust.
The user is trying to double-check custodians, find errors, manage exceptions, and reduce reimbursement exposure.

That requires:
- explainable logic
- repeatable outcomes
- auditability
- low operational ambiguity

A smart but non-deterministic system without authority boundaries would be impressive in demos and dangerous in production.

## Design principle
Use AI to make humans faster and better informed.
Do not use AI to make core control decisions opaque.
