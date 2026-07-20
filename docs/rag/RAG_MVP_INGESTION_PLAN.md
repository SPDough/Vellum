# Vellum MVP RAG Ingestion Plan

## Objective
Prepare a clean, repeatable ingestion process for industry and internal documents before bulk loading them into the MVP RAG datastore.

## Canonical storage and ingestion path
Use:
- `backend/app/models/rag.py`
- `backend/app/services/rag_pipeline_service.py`
- `backend/app/api/endpoints/rag.py`

## Embedding standard
For MVP, use OpenAI `text-embedding-3-small` only.
Reason:
- matches current pgvector schema dimension (1536)
- avoids dimension mismatch across providers

## Folder structure
Recommended staging structure under the repo root:

- `data/rag/custodians/state_street/`
- `data/rag/custodians/bny/`
- `data/rag/internal/sops/`
- `data/rag/internal/playbooks/`
- `data/rag/industry/settlement/`
- `data/rag/industry/accounting/`
- `data/rag/industry/controls/`
- `data/rag/clients/`
- `data/rag/manifests/`

## Ingestion unit
Each file should be paired with structured metadata, preferably through a manifest entry.

## Manifest format
Create JSON manifests under `data/rag/manifests/`.
Each entry should include:
- `filepath`
- `title`
- `source_type`
- `domain`
- `provider`
- `document_type`
- `effective_date`
- `trust_level`
- `tags`
- optional metadata fields

## Example manifest entry
```json
{
  "filepath": "data/rag/custodians/state_street/state_street_custody_api_listing_2026-02-14.xlsx",
  "title": "State Street Custody Accounting API Listing",
  "source_type": "custodian_api_spec",
  "domain": "custody",
  "provider": "state_street",
  "document_type": "spreadsheet_extract",
  "effective_date": "2026-02-14",
  "trust_level": "authoritative",
  "tags": ["api", "custody", "positions", "cash", "trade-status"],
  "version_label": "v10",
  "business_process": "custody_oversight"
}
```

## First ingestion waves

### Wave 1
Highest-value documents for MVP:
- State Street API specs / file specs / field dictionaries
- internal SOPs and exception playbooks
- market convention / settlement reference docs

### Wave 2
- additional custodian/provider material
- implementation notes
- reimbursement/claims guidance
- client-specific operating context

## Retrieval expectations
The first ingestion wave should support:
- rule explanation
- workflow guidance
- operator investigation assist
- provider-specific field and process lookup

## Implementation notes
- keep filenames stable and descriptive
- avoid duplicate uploads of the same document version
- mark drafts clearly in metadata
- prefer authoritative documents for provider mappings and rule support
- use tags that reflect real product retrieval needs, not generic document-management labels

## Next execution step
1. create the folder structure
2. create the first manifest
3. move the first-wave documents into the staging folders
4. ingest documents through the canonical RAG path
5. validate retrieval quality on a few real questions
