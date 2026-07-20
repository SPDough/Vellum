# Vellum / Otomeshon — Code Review Blueprint

> **Audience:** Cursor or Claude Code, acting as the executing agent.
> **Repo:** `https://github.com/SPDough/Vellum` (branch `main`)
> **Goal:** Bring the repo to a state where it is (a) presentable to investors and SMEs, (b) reliable as the demo backend for the custodian portal, and (c) ready for production hardening in a separate later sprint.
> **Date of review:** April 2026, against live `main`.

---

## Executive summary

The repo is in a workable but visibly cluttered state. A previous review (December 2024, captured in `CODE_REVIEW_SUMMARY.md`) already addressed the most serious security findings — hardcoded credentials, missing input validation, dependency conflicts, weak error handling. Those fixes are in place and should not be redone.

What remains breaks into four buckets:

1. **Repo hygiene** — the root directory has accumulated artifacts that make the project look unfinished. Easy to fix, large signal-to-effort ratio.
2. **Frontend strategy** — the in-repo React frontend still has the documented mounting issue. The custodian portal repo (`otomeshon-custodian-portal-38a8ec58`) is the active demo UI. A decision is needed: kill the in-repo frontend or fix it. **Recommend: deprecate, don't fix.**
3. **Backend demo contract** — `main_simple.py` is the demo backend. The portal wiring sprint depends on this contract being stable. A few small fixes lock it down.
4. **Production hardening** — JWT, HTTPS, real auth. Defer until after first prospect demo.

The five phases below are sequenced by leverage, not by line count. Phase 1 is half a day of work and changes the repo's first impression dramatically. Phase 5 is multiple weeks and should not start until the first paying pilot is signed.

---

## Prerequisites for the executing agent

Before starting, the agent should:

1. Pull `main` and create a new branch: `git checkout -b cleanup/repo-hygiene-and-demo-readiness`.
2. Confirm the working tree is clean: `git status` should show no uncommitted changes.
3. Read `README.md`, `README-DEVELOPMENT.md`, and `ARCHITECTURE.md` once before making changes.
4. Do **not** run any deletion command without first listing what will be deleted.
5. Commit at the end of each phase with a clear message. One phase = one PR-ready commit, not many small commits.

---

## Phase 1 — Repo hygiene

**Goal:** A repo root that looks professional when an investor, SME, or future hire opens it on GitHub.
**Estimated effort:** 4–6 hours.
**Risk:** Very low. Pure file moves and config tweaks.

### 1.1 Move root-level test files into the backend test tree

These files currently sit at the repo root and make the project feel unfinished:

```
test_custodian_langgraph.py
test_custodian_simple.py
test_implementation.py
test_rules_system.py
test_utils.py
test_workflow_system.py
```

**Action:**

1. Create `backend/tests/` if it does not already exist. (The December 2024 review references `backend/tests/test_security.py` so the directory likely exists.)
2. For each file above, run `git mv <file> backend/tests/<file>`.
3. Open each moved file and update relative imports — they will currently import as if they live at the repo root.
4. Run the full test suite from `backend/`: `cd backend && pytest tests/ -v`.
5. Fix any import failures. Do not skip failing tests; if a test was already broken before the move, mark it explicitly with `@pytest.mark.skip(reason="pre-existing failure, see issue #XX")` and open a GitHub issue for it.

**Acceptance criteria:**
- `git ls-files | grep -E "^test_.*\.py$"` returns nothing.
- `cd backend && pytest tests/ -v` exits 0 (or with only pre-existing, marked skips).

### 1.2 Move root-level RAG scripts into a proper module

These four files at root are clearly part of the RAG MVP work referenced in `RAG_MVP_*.md`:

```
ProductDoc.py
ingest.py
rag_service.py
retrieve.py
```

**Action:**

1. Read each file's top-of-file imports and main entry point to confirm role.
2. Create `backend/app/rag/` (a new package).
3. `git mv` each file into `backend/app/rag/`. Rename `ProductDoc.py` to `product_doc.py` to match Python style (snake_case).
4. Add a `backend/app/rag/__init__.py` that exposes the public callables.
5. Update any imports across the repo. A search for `from ingest import`, `from rag_service import`, `from retrieve import`, and `from ProductDoc import` will surface them.
6. If any of these scripts have a `if __name__ == "__main__":` block, also add a thin wrapper in `scripts/` that imports and calls the module function — this preserves CLI invocation without keeping the scripts at root.

**Acceptance criteria:**
- `ls /` shows no loose `.py` files except possibly `setup.py` if present.
- The RAG module is importable as `from app.rag import ingest`.

### 1.3 Archive the AI-generated review artifacts

The repo root currently holds these markdown files, most of which are artifacts of past AI sessions:

```
CI_CD_FIXES_APPLIED.md
CODE_REVIEW_SUMMARY.md
DETAILED_CODE_REVIEW.md
NEXT_STEPS_IMPLEMENTATION.md
PERFORMANCE_ANALYSIS_REPORT.md
PERFORMANCE_IMPROVEMENTS_SUMMARY.md
WORKFLOW_FIX.md
```

**Action:**

1. Create `docs/reviews/`.
2. `git mv` each of the seven files above into `docs/reviews/`.
3. In `docs/reviews/`, create a new `README.md` with a short index — one line per file, with the date of that review and a one-sentence summary of its scope. This makes the history navigable rather than noisy.
4. Update any links to these files from `README.md` and other root-level markdown.

**Keep at root:** `README.md`, `README-DEVELOPMENT.md`, `ARCHITECTURE.md`, `AUTH_STRATEGY.md`, `RUN_MODES.md`, `WORKFLOW_CONFIGURATION_README.md`, `DEVELOPMENT.md`. These describe how the system works, not what was reviewed.

**Consider moving to `docs/`:** the four `RAG_MVP_*.md` files. They are design docs for a specific subsystem and belong with code, not at root.

**Acceptance criteria:**
- Repo root has at most 8 markdown files.
- `docs/reviews/README.md` indexes the moved files.

### 1.4 Resolve the `.env.dev` ambiguity

The repo currently has three env templates: `.env.example`, `.env.template`, and `.env.dev`. I checked `.env.dev` — it contains only placeholders (`SECRET_KEY=dev-secret-key-not-for-production`, `OPENAI_API_KEY=sk-your-openai-dev-key`, etc.), so this is **not a security issue**. It is, however, confusing and redundant.

**Action:**

1. Pick **one** canonical template. Recommend keeping `.env.example` since the December review already standardised on it.
2. Diff the three files. If `.env.dev` or `.env.template` contains keys not in `.env.example`, merge them into `.env.example` first.
3. Add `.env.dev` and `.env.template` to `.gitignore` if any developer is locally using those filenames. Otherwise, `git rm` them.
4. Update `README.md` and `README-DEVELOPMENT.md` to reference only `.env.example`.

**Acceptance criteria:**
- One env template at root: `.env.example`.
- `.gitignore` covers `.env`, `.env.local`, `.env.production`, `.env.staging`, `.env.dev`.

### 1.5 Consolidate Docker Compose files

There are currently four: `docker-compose.yml`, `docker-compose.dev.yml`, `docker-compose.minimal.yml`, `docker-compose.prod.yml`. This is one too many.

**Action:**

1. Read all four files and identify which one `docker-compose.yml` (no suffix) actually targets. If it is identical to one of the other three, delete it. If it is a default that nobody runs, delete it.
2. Document the remaining three clearly in `README-DEVELOPMENT.md`: minimal for daily dev, dev for full-stack integration testing, prod for production deployment. The README already does this — verify it stays accurate.

**Acceptance criteria:**
- Three Compose files at root, each with a clear, documented purpose.

### 1.6 Decide the repo name vs product name

The repo is `Vellum`, the product is `Otomeshon`. This will continue to confuse anyone you point at the GitHub URL — investors, SMEs, prospective hires.

**Action:** This is a decision, not an automatic fix. Do **not** rename without the human's confirmation.

Recommend the human decide between:
- **(a)** Rename the repo to `otomeshon-platform` (or similar). GitHub auto-redirects from the old URL, so existing links keep working.
- **(b)** Keep `Vellum` as a deliberate internal name — but then update `README.md` to open with one line explaining the relationship: "Vellum is the internal codename for the Otomeshon banking operations platform."

If the human picks (a), the agent should perform the rename via the GitHub UI (cannot be done from a clone) and update any hardcoded references in the codebase: `grep -r "Vellum" --include="*.md" --include="*.py" --include="*.ts" --include="*.tsx"`.

**Acceptance criteria:**
- A human-confirmed decision is recorded in `docs/reviews/README.md` under "Decisions log".

### Phase 1 commit

```
chore: repo hygiene cleanup

- Move root-level test files into backend/tests/
- Move RAG scripts into backend/app/rag/ package
- Archive review artifacts into docs/reviews/
- Consolidate env templates to .env.example only
- Document Docker Compose file purposes
```

---

## Phase 2 — Frontend strategy decision

**Goal:** Stop investing time in two frontends. Pick one demo UI and commit to it.
**Estimated effort:** 30 minutes for the decision; 4–6 hours for the chosen path.
**Risk:** Medium — wrong call wastes work in Phase 3.

### The current state

- The Vellum repo has a `frontend/` directory with React 18 + MUI + TanStack Table + Recharts + Zustand + React Query. The `README.md` lists "React frontend debugging (mounting issues)" under "In Progress" and "React frontend has import conflicts preventing proper mounting" under "Known Issues". This has been the case since at least early April.
- The custodian portal repo (`otomeshon-custodian-portal-38a8ec58`, separate repo) is built with Vite + shadcn/ui + Tailwind, mounts cleanly, and the recent sprint wired it to Vellum's `main_simple.py` backend.

### The recommendation

**Deprecate the in-repo `frontend/` directory.** The portal repo is further along, mounts cleanly, has FormatJS already installed, and is the asset that will be in front of prospects. Spending another week debugging the in-repo frontend is sunk-cost reasoning.

### 2.1 If the human agrees to deprecate

**Action:**

1. Create a tag on the current `main` before deletion: `git tag pre-frontend-removal && git push --tags`. This preserves the code permanently in case it is ever needed.
2. `git rm -r frontend/`.
3. Update `README.md`:
   - Remove the "Frontend Stack" section.
   - Replace with a "UI" section pointing at the portal repo URL with a one-line explanation that the portal is the active UI, this repo is the backend platform.
   - Move "React frontend debugging" out of the "In Progress" list.
4. Update `docker-compose.dev.yml`, `docker-compose.minimal.yml`, `docker-compose.prod.yml` to remove the `frontend` service. The portal runs separately on port 8080.
5. Remove `package.json` and `package-lock.json` from the repo root if they exist solely to support the in-repo frontend. Verify by checking what scripts and dependencies they declare.
6. Remove `vercel.json` and `.vercelignore` if they were configured for the in-repo frontend deployment.

**Acceptance criteria:**
- `frontend/` directory does not exist on `main`.
- `docker-compose.minimal.yml up -d` succeeds and serves the backend on `:8000`.
- The portal repo can still hit the backend with no CORS issues.

### 2.2 If the human chooses to fix instead of deprecate

Do not start this without an explicit decision. The fix is roughly:

1. Audit `frontend/src/main.tsx` and `frontend/app/layout.tsx`. The mounting issue per ARCHITECTURE.md is caused by two competing entry points (Next.js App Router under `frontend/app/` and a legacy SPA under `frontend/src/`). Pick one.
2. Delete the unchosen entry point and all files that reference it.
3. Run `frontend/npm install && npm run dev` and verify it mounts.

This path is ~4–6 hours of careful work and produces the same result the portal repo already gives you.

### Phase 2 commit (deprecation path)

```
refactor: deprecate in-repo frontend in favour of custodian portal repo

- Remove frontend/ directory (preserved at tag pre-frontend-removal)
- Remove frontend service from all Docker Compose files
- Update README to point at the portal repo as the active UI
```

---

## Phase 3 — Lock the demo backend contract

**Goal:** Make `main_simple.py` reliable enough that the portal wiring sprint can depend on it without surprises.
**Estimated effort:** 3–4 hours.
**Risk:** Low if Phase 2 went well.

### 3.1 Stabilise the API surface

The portal wiring plan depends on these exact endpoints:

```
POST /api/auth/login
GET  /api/auth/me
GET  /api/v1/data-sandbox/records
GET  /api/v1/data-sandbox/stats
GET  /api/v1/data-sandbox/sources
POST /api/v1/data-sandbox/filter
POST /api/v1/data-sandbox/export
WS   /api/v1/data-sandbox/ws
```

**Action:**

1. Open `backend/app/main_simple.py` and grep for each endpoint above. Confirm they exist.
2. For each endpoint, write down the response schema by running `curl` against a local instance and capturing the JSON. Store these in `contracts/data-sandbox.openapi.json` (or similar location under `contracts/` which already exists).
3. Add a contract test under `backend/tests/test_demo_contract.py` that hits each endpoint and asserts the response shape matches the contract. This is what catches breaking changes before they break the portal.

**Acceptance criteria:**
- `pytest backend/tests/test_demo_contract.py -v` passes against a running `main_simple.py` instance.
- `contracts/data-sandbox.openapi.json` documents every endpoint above.

### 3.2 Enrich the demo seed data

Per the prior portal wiring plan, the 100 sample records need to tell a believable reconciliation story for the demo:

- Spread across three custodians: State Street, BNY Mellon, Northern Trust.
- Mix of break types: settlement date, price, quantity, corporate action.
- Mix of statuses: Open, In Review, Resolved, Escalated.
- Age range 0–30 days, with a few aged records.
- Plausible mid-tier asset manager fund names.
- An `agent_analysis` block on each record with `root_cause`, `recommended_action`, `confidence`, and `steps`.
- Amounts in USD, $10K–$50M.

**Action:**

1. Locate the seed data generator in `backend/app/main_simple.py` (or wherever it lives).
2. Replace generic banking records with the schema above.
3. Update the `/api/v1/data-sandbox/stats` endpoint so its summary counts match the seeded records exactly. Inconsistent dashboard numbers will be the first thing a prospect notices.

**Acceptance criteria:**
- `curl /api/v1/data-sandbox/records | jq '.[].agent_analysis.root_cause'` returns 100 plausible root cause strings.
- `curl /api/v1/data-sandbox/stats` returns counts that sum to the records returned by `/records`.

### Phase 3 commit

```
feat(demo): lock backend contract and enrich seed data

- Document data-sandbox endpoints in contracts/data-sandbox.openapi.json
- Add contract tests in backend/tests/test_demo_contract.py
- Replace generic seed data with reconciliation-specific records
- Add agent_analysis block to every seed record
```

---

## Phase 4 — Demo auth (only if Phase 2 chose deprecation)

**Goal:** Replace the demo auto-login with a real login screen that hits Vellum's auth endpoint, without yet doing full JWT.
**Estimated effort:** 2–3 hours.
**Risk:** Low. Touches only `main_simple.py` and the portal's auth client.

This is mostly a portal-repo task, not a Vellum-repo task. The Vellum side is small:

1. Verify `POST /api/auth/login` accepts the demo credentials from `.env.example`.
2. Verify `GET /api/auth/me` returns user info given the token.
3. If the existing tokens are UUIDs (per the December review), leave them — full JWT lives in Phase 5.

**Acceptance criteria:**
- `curl -X POST /api/auth/login -d '{"username":"admin@otomeshon.ai","password":"<from-env>"}'` returns a token.
- That token works on `/api/auth/me`.

---

## Phase 5 — Production hardening (DEFER)

Do not start this before the first paid pilot is signed. These are the items the December 2024 review flagged as "remaining":

- Replace UUID tokens with proper JWT (signed, expiring, refresh rotation).
- Add HTTPS redirect middleware and HSTS headers.
- Encrypt database connections.
- Add per-endpoint rate limiting.
- Add comprehensive audit logging.
- Add data encryption at rest where required by client compliance teams.

Each of these is a half-day to two-day task. None of them block the demo or the first pilot conversations. Several are best done with the first pilot client's compliance team in the room rather than guessing at their requirements.

---

## Execution order summary

| Phase | What | Effort | Blocks |
|-------|------|--------|--------|
| 1 | Repo hygiene | 4–6 hrs | Nothing — start here |
| 2 | Frontend deprecation decision | 30 min decision + 4–6 hrs execution | Phase 3 |
| 3 | Lock demo backend contract | 3–4 hrs | Portal demo |
| 4 | Demo auth | 2–3 hrs | Pilot prospect demos |
| 5 | Production hardening | Multi-week | First paid pilot |

**Total demo-readiness work: ~14–20 hours**, or roughly one focused week at 4 hrs/day.

---

## What this blueprint deliberately does not do

A few things were considered and explicitly excluded:

- **No new architecture changes.** The stack (FastAPI, LangChain, Postgres, Redis, Neo4j) is appropriate. Adding Snowflake, GoRules Zen, or other components from the broader architecture vision should happen post-pilot.
- **No NAV calculation domain work.** That is real-effort domain work that requires the human's expertise, not Cursor's.
- **No corpus curation for the RAG system.** Same reason. The `RAG_MVP_*.md` files describe what needs to happen but the curation itself is human work.
- **No CI/CD overhaul.** GitHub Actions is already configured per the repo's `.github/` directory. If pipelines are passing, leave them.

These are the three places where Cursor and Claude Code have least leverage. Spending agent time on them does not move the demo forward.

---

## Notes for the executing agent

- After each phase, **show the diff** before committing. Do not auto-commit large file moves.
- If a test fails after a file move, **investigate** rather than skipping. The whole point is to make the repo trustworthy.
- For the Phase 1.6 repo rename, **stop and ask the human**. Renames are reversible but disruptive.
- For the Phase 2 deprecation, **stop and ask the human** before deleting `frontend/`. Tag first, delete second.
- When in doubt about scope, prefer doing less. A clean partial result is better than a sprawling half-finished refactor.
