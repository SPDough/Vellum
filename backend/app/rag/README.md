# NAV RAG (backend/app/rag)

Findings-oriented RAG: ingest reference documents, retrieve by finding type, and build prompts for explanation, rule justification, and client communication.

## Tables (migration 003)

- **nav_rag_documents** – Source docs (doc_id, title, doc_type, source_file, author, domain, total_chunks, …).
- **nav_rag_chunks** – Chunks with embeddings (chunk_id, doc_id, content, chunk_type, chapter, section, mart_name, topics, relevance_tags, embedding).
- **rag_retrieval_log** – Retrieval logging.

## Ingest

From repo root:

```bash
PYTHONPATH=backend python -m app.rag.ingest --doc weiss_book
PYTHONPATH=backend python -m app.rag.ingest --all
```

From `backend/`:

```bash
python -m app.rag.ingest --doc weiss_book
```

Place source files under paths listed in `DOCUMENTS` in `ingest.py` (e.g. `data/raw/`). Set `DATABASE_URL` or `OTOMESHON_DB_DSN` and `OPENAI_API_KEY` (or use app config).

**State Street Custody Accounting:** Ingest key `custody_api` uses `v10_State_Street_Core_Data_Consumption_Model__Custody_Accounting_2026_02_14.xlsx`. The same document is referenced by the app’s State Street API spec (`app.services.custodian_apis.state_street`).

## Retrieve and prompts

- **retrieve.py** – `RagRetriever.retrieve()` and `retrieve_for_finding()` (purpose: `explain` | `rule` | `report`).
- **rag_service.py** – `get_rag_retriever()`, `build_explanation_prompt()`, `build_rule_prompt()`, `build_report_prompt()`.

## API

Under `/api/v1/rag`:

- `POST /rag/findings/explanation` – Body: finding JSON. Returns prompt + citations; `?generate=true` calls Claude.
- `POST /rag/findings/rule-basis` – Same pattern for rule justification.
- `POST /rag/findings/client-communication` – Same for client letter.

## Root-level files

Repo root `ingest.py`, `retrieve.py`, and `rag_service.py` are thin redirects to this package. Use this package as the single source of truth.
