# Reference: Rule Definition & Rule Result contracts

**Status:** Reference (reflects `contracts/rule-definition/1.0.0` and `contracts/rule-result/1.0.0`)
**Audience:** engineers and domain authors building out Vellum's rules and ontology
**Related:** [Vellum Authority Order](../product/vellum-authority-order.md), [RAG_MVP_ARCHITECTURE](../rag/RAG_MVP_ARCHITECTURE.md)

## What this is (and what it is not)

Vellum rules are **deterministic, versioned JSON data artifacts** evaluated against canonical
contract objects. They are **not** Drools and **not** hidden code paths.

- **Canonical engine:** `backend/app/rules/` — `engine.py` (`RuleEngine`), `jsonlogic.py`
  (`JsonLogicEvaluator`), `loader.py`, `registry.py`, `models.py`. This is the go-forward path,
  wired into `rules_orchestration`.
- **Definitions live as data:** `contracts/rule-definition/1.0.0/*.json`, governed by
  `schema.json` (JSON Schema draft 2020-12), with a `dictionary.json` (business definitions) and
  a `fibo-alignment.json` (optional ontology intersection).
- **Legacy:** `backend/app/services/drools_service.py` + `drools/*.drl` still back the older
  `/rules` REST endpoint (`app/api/endpoints/rules.py`). Drools is legacy and slated for phased
  deprecation; new rules are JSON-native.

### Design principles (from `dictionary.json`)

1. Rules are **deterministic and replayable**.
2. Rules are **versioned data artifacts, not hidden code paths**.
3. Rules **evaluate canonical contracts**, not provider-specific payloads.
4. LLMs may **assist with explanation and enrichment but do not override** deterministic outcomes.

## Contract envelope

Every contract instance shares an envelope: `contract_type`, `contract_version`, optional
provenance (`source_system`, `source_type`, `source_record_id`, `ingested_at`, `effective_at`,
`lineage`), and a `payload`. `additionalProperties: false` everywhere — unknown fields are
rejected, which is itself a control (no silent, unmodeled data).

## RuleDefinition payload

Required: `rule_id`, `rule_name`, `rule_family`, `version`, `status`, `determinism_class`,
`target_contract_types`, `expression_language`, `predicate`, `outcome`.

| Field | Purpose |
|---|---|
| `rule_id` / `rule_name` | Stable identifier / human-readable name |
| `rule_family` | Logical grouping: `custody`, `reconciliation`, `workflow`, `approvals`, … |
| `version` / `status` | Rule version; lifecycle `draft` \| `active` \| `retired` |
| `determinism_class` | `deterministic` only (today). The field exists so non-deterministic modes stay an explicit, separately-governed decision — never an accident. |
| `target_contract_types` | Canonical contract types the rule evaluates (e.g. `TradeStatus`, `Position`, `CashActivity`) — rules bind to the ontology, not to raw feeds |
| `input_scope` | Pre-evaluation shaping: `join_keys`, `lookback_window`, `group_by`, `filters` |
| `expression_language` | `jsonlogic` or `vellum-json` |
| `predicate` | The JSON expression evaluating to true/false over the facts |
| `severity` / `materiality` | Default severity; static or expression-based materiality |
| `outcome` | Result + control actions (see below) |
| `evidence` | `fields` to snapshot; `rag_enabled` + `rag_collections` to attach knowledge-repository context for operator explanation |
| `workflow_binding` | Routing into `workflow_name` / `case_type` / `approval_type` |
| `test_cases` | Built-in expectation metadata (name → expected result) — every rule carries its own tests |
| `tags` | Discovery/governance |

### Outcome (the control surface)

`result_code` + `result_type` (`pass` \| `flag` \| `break` \| `exception`), plus deterministic
side-effect flags the workflow layer honors: `create_exception`, `create_reconciliation_break`,
`open_workflow_case`, `require_approval`, and an `explanation_template` (mustache-style, filled
from evidence). The rule decides *whether something is wrong*; these flags declare *what
control action follows* — deterministically.

## RuleResult payload

The immutable record of an evaluation: `rule_result_id`, `rule_id`, `rule_version`,
`evaluation_status` (`success` \| `error` \| `skipped`), `triggered`, `severity`, `materiality`,
`result_code`, `result_type`, `target_contract_ids`, `evaluated_at`, an `evidence_snapshot`
(the facts as seen), `explanation`, and the ids of any created control objects
(`created_exception_id`, `created_reconciliation_break_id`, `created_workflow_case_id`,
`created_approval_request_id`). This is the audit spine: every fired rule leaves a replayable,
evidence-bearing record.

## Expression languages

- **`jsonlogic`** — standard [JsonLogic](https://jsonlogic.com) over the fact object
  (`{"var": "derived.days_past_settlement"}`), evaluated by `JsonLogicEvaluator`.
- **`vellum-json`** — Vellum's extension namespace for domain operators JsonLogic doesn't cover.
  Both are declared per-rule and validated by the engine; anything else is rejected.

Facts are the canonical contract object plus a `derived.*` namespace computed during
`input_scope` shaping (e.g. `derived.days_past_settlement`).

## FIBO alignment (selective, per contract)

Each contract type carries a `fibo-alignment.json`. Alignment is **opt-in per contract**, not a
blanket mapping. For `rule-definition` it is currently **disabled** by deliberate design:

> "RuleDefinition is a Vellum-native control artifact and should not be forced into a heavy
> external ontology model."

The intent: **domain data contracts** (positions, cash, trades, securities) are the natural
place to intersect Vellum's proprietary ontology with FIBO; **control artifacts** (rules,
results) stay Vellum-native. This keeps the ontology intersection precise and useful rather than
ceremonial.

## Worked example

`contracts/rule-definition/1.0.0/example.json` — *"Unsettled trade aging exceeds threshold"*:
targets `TradeStatus`, filters out `SETTLED`/`CANCELLED`, predicate
`derived.days_past_settlement > 2`, outcome `result_type: break` that creates an exception, a
reconciliation break, and a workflow case, with RAG evidence from `custody-ops-playbooks` and
`market-settlement-conventions`. One JSON file expresses detection, materiality, control
actions, evidence, workflow routing, and tests — inspectable and versioned.

## How this fits the authority order

Rules are **layer 2** of the [authority order](../product/vellum-authority-order.md): they
decide *"is something wrong?"* over **layer 1** canonical contracts, and hand off to **layer 3**
workflows/control objects. Retrieval (4) and LLM reasoning (5) attach evidence and explanation
via the `evidence` block but never change a `RuleResult`. This contract is where that boundary
is enforced in data.
