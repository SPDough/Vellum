# ADR-002: Schema and migration authority

## Status

Proposed — 2026-07-21. Prompted by a pre-existing, un-run Alembic setup discovered
while unblocking `alembic upgrade` (see [Trigger](#trigger)).

## Context

The backend currently has **two independent systems that both create the PostgreSQL
schema**, and they disagree with each other:

1. **Runtime `create_all`** — on startup, `app/main.py` → `init_db()` →
   `DatabaseManager.init_postgres()` calls `metadata.create_all` for the Trade, SOP,
   Workflow, and RAG declarative bases (`app/core/database.py:70-73`). This is what
   actually runs in dev and in the container today.
2. **Alembic migrations** — hand-written revisions `001`–`005` under
   `backend/migrations/versions/`, driven by `backend/migrations/env.py` and
   `backend/alembic.ini`.

Nothing in the `Dockerfile`, `Makefile`, or any `docker-compose*.yml` runs
`alembic upgrade`. In normal operation, `create_all` builds the tables and the
migrations never execute. Alembic is a spare tire that isn't bolted on.

### Trigger

The migration path was import-broken on `origin/main` and nobody had hit it:

- `migrations/env.py:21` imported `TradeExecution, Position` from `app.models.trade`;
  neither exists (the real models are `Trade`, `TradeException`, `ProcessingStep`).
- The same import block referenced three more non-existent symbols —
  `WorkflowInstance`/`WorkflowStep` (workflow), `DataStream` (data_sandbox), and
  `KnowledgeNode`/`KnowledgeRelation` (knowledge_graph, which has **no** ORM models
  at all).
- `alembic.ini:37` `version_num_format` used unescaped `%(...)` tokens, crashing
  ConfigParser during `run_migrations_online` (masked behind the ImportError above).

All three are now fixed on this branch, and `alembic upgrade head` runs `001`→`004`
cleanly against a fresh `ankane/pgvector` Postgres. Two further **separate**,
pre-existing bugs remain (see [Known defects](#known-defects)). Fixing the load
errors is what surfaced the deeper question: **is Alembic actually the schema
authority, or is it decorative?**

### Evidence that Alembic provides little value as configured

| Problem | Detail |
|---------|--------|
| **Not in the loop** | No deploy/startup step runs `alembic upgrade`; `create_all` is the de-facto authority. |
| **The two paths disagree** | The `trades` table differs between migration `001` and the ORM model. Migration `001` has `trade_id`, `external_trade_id`, `symbol`, `instrument_type`, `counterparty`, `account`, `portfolio`, `trader_id`, JSON `settlement_instructions`, and `quantity` as **Integer**. The ORM `Trade` (`app/models/trade.py`) has `trade_reference`, `counterparty_id`, `instrument_id`, `trade_type`, `trade_value`, and `quantity` as **Numeric(18,8)**. Same table name, different table. Whichever path hits the DB second is a silent no-op. |
| **Autogenerate is disabled by design** | `env.py` sets `target_metadata = Base`, which resolves to `TradeBase` only. There are **five** separate `DeclarativeBase` registries — `trade`, `sop`, `workflow` (shared by `data_sandbox`), `rag`, `data_source`. Autogenerate would only ever see the trade tables and would propose dropping everything else, so it can't be used. Every migration is hand-written. |
| **No one runs it** | The env-load errors sat un-hit on `main`. A migration tool that's been import-broken with nobody tripping over it is, definitionally, one nobody runs. |

`create_all` is fine for dev and tests, but it is a poor production story: no
versioning, no rollback, no data migrations, and — critically — it **never `ALTER`s
an existing table**. Add a column to a model and a long-lived database silently stays
on the old schema. For a banking-flavored platform with an `audit` schema and
compliance framing, that is exactly the failure mode Alembic exists to prevent.

## Decision

**Keep Alembic, and make it the single schema authority — but only by fixing the
setup so it actually earns its keep.** Do not leave two competing systems in place.

Concretely:

1. **Consolidate to one shared declarative base / one `MetaData`.** Introduce a single
   `Base` (e.g. `app/core/base.py`) and have every model module import it instead of
   declaring its own `DeclarativeBase`. This makes `target_metadata` real and makes
   `--autogenerate` usable.
2. **Reconcile the model ↔ migration divergence.** Decide the true `trades` schema
   (and audit any other tables that differ), then make the ORM models and the
   migrations agree. This is the load-bearing step; everything else is mechanical.
3. **Demote `create_all` to dev/test only.** Gate it behind a setting (e.g.
   `STARTUP_CREATE_ALL`, default off outside tests) or remove it, and run
   `alembic upgrade head` in the deploy/startup path so there is exactly one source
   of truth.
4. **Regenerate the baseline once models are unified.** With a single `MetaData`,
   either squash `001`–`005` into a coherent baseline that matches the ORM, or verify
   the existing chain against `--autogenerate` and add a "no diff" test to CI.
5. **Fix the outstanding migration bugs** (below) so the chain reaches `head` and
   round-trips.

### Alternative considered — drop Alembic, keep `create_all`

Rejected. It's less work today but abandons versioned, reversible, auditable schema
changes and the ability to `ALTER` existing tables — unacceptable for the compliance
posture in [ADR-001](ADR-001-canonical-platform-stack.md). If the team genuinely does
not want migrations, that should be an explicit decision recorded here, and the broken
migration files should be deleted rather than left to rot.

## Known defects

Independent of the schema-authority question, two pre-existing bugs block a full
`001`→`005` round-trip:

- **`005` runs `CREATE INDEX CONCURRENTLY` inside a transaction.** Migration `005`
  (knowledge-agent durable memory, on `feat/knowledge-agent-durable-memory`) executes
  `PostgresSaver.MIGRATIONS`, which includes a `CONCURRENTLY` index. Alembic wraps
  migrations in a transaction, and Postgres forbids `CONCURRENTLY` there
  (`psycopg2.errors.ActiveSqlTransaction`). Fix: run those statements on an autocommit
  connection / with `op.get_context().autocommit_block()`, or drop `CONCURRENTLY`.
- **Full `downgrade base` cannot complete.** Migration `001`'s `downgrade()` runs
  `DROP SCHEMA IF EXISTS audit CASCADE` (`001_...initial_banking_schema.py:279`), which
  destroys `audit.alembic_version` — the table Alembic uses to record versions
  (`env.py` sets `version_table_schema="audit"`). The final `001 → base` step then
  errors and the whole downgrade rolls back. Fix: drop the `audit_log` table
  explicitly and leave the `audit` schema (and its version table) intact.

## Consequences

- **Positive:** one source of truth; `--autogenerate` becomes usable; schema changes to
  existing databases actually apply; reversible, auditable migrations that match the
  compliance framing.
- **Cost:** the reconciliation in step 2 is real work and needs care against any
  existing data. Until it's done, the divergence remains a latent production hazard
  regardless of this ADR.
- **Interim guidance:** until consolidation lands, treat `create_all` as the truth in
  dev, do **not** rely on Alembic for schema state, and land new tables in **both**
  the ORM models and a migration so the eventual cutover is cheap.

## References

- `backend/migrations/env.py`, `backend/alembic.ini`
- `backend/app/core/database.py:61-73` (`init_postgres` / `create_all` path)
- `backend/app/main.py:51` (`init_db()` on startup)
- `backend/app/models/trade.py`, `.../workflow.py`, `.../rag.py`, `.../data_source.py`,
  `.../sop.py`, `.../data_sandbox.py` (five separate declarative bases)
- `backend/migrations/versions/001_20241127_1400_initial_banking_schema.py`
- [ADR-001: Canonical platform stack](ADR-001-canonical-platform-stack.md)
- [Database schema documentation](DATABASE_SCHEMA.md)
