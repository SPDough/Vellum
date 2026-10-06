# Vellum Rules

Vellum's native deterministic, JSON-first rules engine — the only rules engine in this
repo (Drools/Kogito has been fully decommissioned; see
[docs/contracts/RULE_DEFINITION_CONTRACT.md](../../../../docs/contracts/RULE_DEFINITION_CONTRACT.md)).

## Purpose
- load versioned JSON rule definitions (directory-scanned from `contracts/rule-definition/`)
- evaluate deterministic predicates against canonical contract-shaped facts
- group related rules by tag and evaluate them together via `evaluate_rule_group`
- emit standardized `RuleResult` contract objects
- keep rule logic auditable, replayable, and low-friction

## Current approach
- `contracts/rule-definition/...` remains the source of truth for rule shape
- `backend/app/rules/jsonlogic.py` provides a small JsonLogic-like evaluator; date/aggregation
  math is deliberately kept out of it — callers precompute those into `derived.*` facts
  (see `derived_facts.py`) before evaluation, keeping predicates simple comparisons
- `backend/app/rules/loader.py` / `registry.py` scan `contracts/rule-definition/<version>/` and
  index rules by `rule_id` and by `tags`
- `backend/app/rules/engine.py` runs a single rule (`evaluate_rule`) or an entire tagged group
  (`evaluate_rule_group`) and emits `RuleResult`-shaped output
- `backend/app/rules/fact_builder.py` builds the fact dicts each rule group needs from the
  camelCase data shapes callers (API routes, LangGraph nodes) already send
- this can later swap to a fuller evaluator library without changing Vellum's contract model

## Important design principle
LLMs and RAG may assist with explanation and context, but deterministic predicates remain the source of truth for rule outcomes.
