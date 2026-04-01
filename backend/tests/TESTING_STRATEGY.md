# Testing Strategy

## Current first-pass split

### Demo backend tests
These validate the simplified backend in `app.main_simple`.

Current examples:
- `test_main_simple.py`
- most of `test_api_endpoints.py`
- much of `test_security.py`
- any test using the shared `client` / `async_client` fixtures from `conftest.py`

### Real backend tests
These should validate the canonical backend in `app.main`.

Current starter file:
- `test_real_backend_contract.py`

## Key rule

Passing demo-backend tests does **not** prove the full backend contract is healthy.

## Near-term plan

1. Keep existing demo tests, but label them honestly.
2. Grow `test_real_backend_contract.py` into a real smoke/integration suite for `app.main`.
3. Add infrastructure-gated tests separately for services that require Postgres, Neo4j, Kafka, or Temporal.
