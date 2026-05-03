# Prefect Cloud Work Pools (Free Tier)

This runbook covers how to move Vellum deterministic orchestration from local Prefect server to Prefect Cloud work pools, while keeping `docker-compose.dev.yml` usable for local development.

## 1) Local profile vs Cloud

- **Local profile** (`docker compose --profile prefect up`) uses:
  - `prefect-server`
  - `prefect-worker`
  - `PREFECT_API_URL=http://prefect-server:4200/api`
- **Cloud profile** uses:
  - no local server container required
  - `PREFECT_API_URL` set to Prefect Cloud workspace API URL
  - `PREFECT_API_KEY` for authentication

## 2) Create a Cloud work pool

In Prefect Cloud UI (free tier):

1. Create / select a workspace
2. Create a **Work Pool** of type `process` (or another type you manage)
3. Note the pool name (for example `default-agent-pool`)

Set in `.env`:

```env
PREFECT_API_URL=https://api.prefect.cloud/api/accounts/<account-id>/workspaces/<workspace-id>
PREFECT_API_KEY=<your-prefect-cloud-api-key>
PREFECT_WORK_POOL=default-agent-pool
```

## 3) Start a worker

With current Compose wiring:

```bash
docker compose --profile prefect up -d prefect-worker
```

The worker command uses:

```bash
prefect worker start --pool ${PREFECT_WORK_POOL} --type process
```

If `PREFECT_API_URL` points at Cloud and `PREFECT_API_KEY` is set, this worker will register against Cloud.

## 4) Deploy and run canonical probe flow

From `backend/`:

```bash
python -m flows.canonical_probe
```

This verifies Prefect client/runtime wiring and is also used in CI as a smoke check.

## 5) CI smoke behavior

CI currently runs `python -m flows.canonical_probe` with:

- local `PREFECT_HOME` under `backend/.prefect`
- sqlite database file in workspace

That keeps CI deterministic and avoids requiring external Cloud credentials.

## 6) Troubleshooting

- **`unable to open database file`**:
  - ensure `PREFECT_HOME` directory exists and is writable
- **Cloud auth errors**:
  - verify `PREFECT_API_KEY`
  - verify workspace-scoped `PREFECT_API_URL`
- **Worker not picking jobs**:
  - confirm deployment targets the same `PREFECT_WORK_POOL`
  - ensure worker type matches pool type

