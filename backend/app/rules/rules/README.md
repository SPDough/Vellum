# Vellum Rules

Lightweight scaffold for Vellum's native deterministic, JSON-first rules framework.

## Purpose
- load versioned JSON rule definitions
- evaluate deterministic predicates against canonical contract-shaped facts
- emit standardized `RuleResult` contract objects
- keep rule logic auditable, replayable, and low-friction

## Current approach
- `contracts/rule-definition/...` remains the source of truth for rule shape
- `backend/app/rules/jsonlogic.py` provides a small evaluator scaffold for early prototyping
- `backend/app/rules/engine.py` runs a rule and emits a `RuleResult`
- this can later swap to a fuller evaluator library without changing Vellum's contract model

## Important design principle
LLMs and RAG may assist with explanation and context, but deterministic predicates remain the source of truth for rule outcomes.
