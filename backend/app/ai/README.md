# AI / LLM Orchestration

This folder is the home for Vellum's AI orchestration layer.

## Architecture stance
- deterministic contracts, rules, and workflows remain authoritative
- RAG and LLM orchestration provide explanation, enrichment, and operator acceleration
- LangGraph-style orchestration can wrap deterministic rule execution without replacing it

## Current scaffold
- `langgraph_workflows/rules_orchestration.py` provides a LangGraph-shaped sample workflow
- the workflow runs a sample rule through the native deterministic rule engine
- it returns suggested next actions and advisory RAG collection context

## Important principle
Generative AI should not override deterministic rules where deterministic logic is available.
