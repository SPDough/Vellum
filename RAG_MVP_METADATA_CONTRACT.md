# Vellum MVP RAG Metadata Contract

This file defines the minimum metadata standard for documents ingested into Vellum's MVP RAG store.

## Goals
- keep ingestion disciplined and repeatable
- support filtering by provider/domain/source type
- distinguish authoritative sources from working notes
- make retrieved evidence more useful for rules and workflows

## Canonical document fields
Each ingested document should have the following metadata fields.

### Required
- `title`
- `source_type`
- `domain`
- `provider`
- `document_type`
- `effective_date`
- `trust_level`
- `tags`

### Optional
- `source_url`
- `author`
- `version_label`
- `jurisdiction`
- `audience`
- `confidentiality`
- `business_process`
- `asset_class`
- `client_scope`
- `notes`

## Allowed values

### source_type
- `custodian_api_spec`
- `custodian_file_spec`
- `custodian_operating_guide`
- `internal_sop`
- `internal_playbook`
- `market_convention`
- `regulation`
- `client_document`
- `implementation_note`
- `training_material`

### domain
- `custody`
- `reconciliation`
- `settlements`
- `fund_accounting`
- `cash`
- `corporate_actions`
- `tax`
- `workflow`
- `controls`
- `client_reporting`
- `reference_data`

### provider
- `state_street`
- `bny`
- `northern_trust`
- `bbh`
- `simcorp`
- `aladdin`
- `internal`
- `sec`
- `industry`
- `other`

### document_type
- `pdf`
- `markdown`
- `text`
- `spreadsheet_extract`
- `playbook`
- `guide`
- `specification`
- `regulatory_text`

### trust_level
- `authoritative`
- `internal_guidance`
- `working_note`
- `draft`

## Metadata interpretation guidance
- `authoritative`: source should be preferred in retrieval and explanation when conflict exists
- `internal_guidance`: useful for workflow/investigation help but not external source-of-truth
- `working_note`: analyst/design note; useful for internal context only
- `draft`: provisional content; do not over-weight

## Example metadata object
```json
{
  "title": "State Street Custody Accounting API Listing",
  "source_type": "custodian_api_spec",
  "domain": "custody",
  "provider": "state_street",
  "document_type": "spreadsheet_extract",
  "effective_date": "2026-02-14",
  "trust_level": "authoritative",
  "tags": ["api", "custody", "positions", "cash", "trade-status"],
  "version_label": "v10",
  "business_process": "custody_oversight",
  "notes": "Primary source for State Street first-wave provider mappings"
}
```
