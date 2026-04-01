# LangGraph Workflows

This directory contains LangGraph-oriented orchestration scaffolds.

## Current sample
`rules_orchestration.py` models a simple rule-processing flow:
- load advisory rule/RAG context
- evaluate a deterministic rule
- determine next operational actions
- assemble a workflow response

## Why this shape
This keeps LangGraph in the orchestration layer while preserving the authority of:
- canonical data contracts
- deterministic rules
- deterministic workflow/control outcomes

## Future evolution
When LangGraph is installed in the runtime, this scaffold can be converted into a real `StateGraph` with minimal conceptual change.
