# Vellum Contract Registry

This directory contains Vellum's pragmatic JSON contract registry.

## Design goals
- keep contracts simple and implementable
- support deterministic rules and workflows first
- provide enough semantic metadata to stay consistent
- avoid heavyweight ontology/process overhead early
- allow optional FIBO alignment where useful

## Structure
Each contract lives under:

```text
contracts/<contract-name>/<version>/
```

Each version directory may include:
- `schema.json` — canonical JSON schema
- `dictionary.json` — short business glossary and field definitions
- `fibo-alignment.json` — optional semantic reference hints

## First-wave contracts
- position
- cash-activity
- cash-balance
- trade-status
- exception
- account
- entity
- security
- reconciliation-break
- workflow-case
- approval-request
- rule-definition
- rule-result

## Rules direction
Vellum's native deterministic rules are JSON-first.
Rule definitions should be versioned artifacts that evaluate canonical contract objects.
LLMs and RAG may assist with explanation and enrichment, but do not override deterministic rule outcomes.

## Rule of thumb
The contract registry is a practical product/engineering asset, not a heavyweight ontology program.
