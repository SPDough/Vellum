# Vellum MVP RAG Architecture

## Purpose
Vellum's MVP RAG layer is the knowledge and evidence substrate for:
- rule explanation
- exception investigation
- workflow guidance
- operator assist
- draft communications
- industry and custodian reference retrieval

## Authority order
1. Canonical contracts / data dictionary
2. Deterministic rules
3. Deterministic workflows / control objects
4. RAG retrieval
5. LLM explanation / drafting / summarization

RAG is assistive, not authoritative over deterministic control logic.

## Canonical MVP path
Use the existing repo capability as follows:
- storage/search source of truth:
  - `backend/app/models/rag.py`
  - `backend/app/services/rag_pipeline_service.py`
  - `backend/app/api/endpoints/rag.py`
- domain-specific retrieval/prompt helper layer:
  - `backend/app/rag/*`

## Vector store decision
For MVP, use PostgreSQL + pgvector.
Do not introduce Pinecone yet.

## Embedding decision
For MVP, standardize on OpenAI `text-embedding-3-small` (1536 dimensions).
Do not mix providers with different dimensions in the canonical chunk table.

## Logical corpora
Use metadata to represent logical collections:
- custodian/provider reference
- internal SOP / playbook
- market / industry reference
- client / implementation knowledge

## Retrieval patterns
- general semantic search
- rule-support retrieval
- workflow-assist retrieval
- explanation retrieval

## Product interaction model
1. data is normalized into canonical contracts
2. deterministic rules evaluate
3. rule results create or inform control objects
4. RAG retrieves supporting evidence and guidance
5. LLMs explain, summarize, and draft based on deterministic outputs + retrieved evidence
