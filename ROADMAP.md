# TDR Processor - Remediation Roadmap

> Last verified: 2026-06-18  
> Purpose: source of truth for implementation agents.  
> Current quality gate: not production-ready. Treat this roadmap as the execution order.

## Agent Brief

This repository is a Python desktop/API/dashboard app for processing Terminal Departure Report (TDR) Excel files and serving analytics through Flask dashboard and FastAPI endpoints.

The immediate goal is not feature expansion. The goal is to make the application internally consistent, secure enough for controlled deployment, and verifiable by CI.

Implementation agents should follow this order:

1. Fix data source consistency.
2. Fix API security defaults.
3. Fix test/CI tooling.
4. Fix Docker runtime healthchecks.
5. Clean frontend delivery risk.
6. Normalize versioning and docs.
7. Only then address lower-priority UX/refactor work.

Do not start broad refactors before P0/P1 items are complete.

## Verified Findings

These findings were checked against the working tree on 2026-06-18.

| Finding | Evidence | Risk |
|---|---|---|
| Dashboard and FastAPI use different SQLite databases | `report_processor.py` writes `outputs/tdr_master.db`; `utils/database.py` defaults to `outputs/tdr_data.db`; `api.py` calls `TDRDatabase()` with no path | API/dashboard can show different or empty data |
| Flask dashboard token has insecure default | `dashboard_api.py` defaults `TDR_API_TOKEN` to `tdr_secret_token_12345` | Anyone knowing source can access protected data |
| FastAPI has no authentication and broad CORS | `api.py` uses `allow_origins=["*"]`; process/export endpoints are unauthenticated | Data export and processing can be triggered remotely if exposed |
| Default pytest run is broken in current environment | `pytest tests/ -q` fails during collection; `pytest tests/ -q -p no:asyncio` passes 226 tests | CI/release confidence is unreliable |
| Ruff quality gate fails | `python -m ruff check .` reports 124 lint errors | Pre-commit/CI promises do not match actual code quality |
| Docker healthchecks use missing binary | Dockerfile healthcheck calls `curl`; image installs only `gcc` | Containers can become unhealthy even when app runs |
| Roadmap/docs had merge conflict and version drift | old `ROADMAP.md` contained unresolved merge-conflict text; README says v3.1.0, roadmap v3.2.0, config v1.0, FastAPI v3.0.0 | Agents and users cannot trust docs as execution source |
| Dashboard frontend is monolithic dev-mode HTML | `dashboard.html` uses CDN React development build and browser Babel | Slow, fragile, no production build contract |

## Verification Baseline

Run these commands before starting and after each milestone:

```powershell
python -m compileall -q .
pytest tests/ -q
pytest tests/ -q -p no:asyncio
python -m ruff check .
python -m bandit -r . --exclude .\.git,.\node_modules,.\tests -ll
```

Expected current baseline:

| Command | Current Result | Target |
|---|---:|---:|
| `python -m compileall -q .` | pass | pass |
| `pytest tests/ -q` | pass (246 passed) | pass |
| `pytest tests/ -q -p no:asyncio` | pass (246 passed) | pass without workaround |
| `python -m ruff check .` | 0 errors | 0 errors |
| `bandit ... -ll` | 0 medium/high issues | no untriaged medium/high issues |

## P0 - Correctness And Security

### P0-1 - Unify SQLite Data Source [DONE]

**Resolution:** Unified SQLite data source to use `outputs/tdr_master.db` consistently. Added tests checking fallback behavior and vessel consistency.

Problem:
The app has two SQLite paths and two schema styles:

- `report_processor.py` writes `outputs/tdr_master.db` with original column names such as `Vessel Name`.
- `utils/database.py` defaults to `outputs/tdr_data.db` with normalized snake_case schema.
- `dashboard_api.py` reads `outputs/tdr_master.db`.
- `api.py` initializes `TDRDatabase()` without specifying the dashboard database path.

Required decision:
Use one canonical storage contract.

Recommended implementation:

1. Make `outputs/tdr_master.db` the canonical runtime database for the current release because it is already produced by `report_processor.py` and consumed by `dashboard_api.py`.
2. Update FastAPI to read the same canonical DB or explicitly fall back to CSV without creating an empty alternate DB.
3. Remove or quarantine the unused `outputs/tdr_data.db` path unless a full migration to normalized schema is completed.
4. Add tests proving Flask dashboard and FastAPI see the same vessel count for the same fixture/output data.

Files:

- `api.py`
- `dashboard_api.py`
- `report_processor.py`
- `utils/database.py`
- `tests/`

Acceptance criteria:

- No runtime code silently creates `outputs/tdr_data.db` when `outputs/tdr_master.db` exists.
- `/health`, `/api/vessels`, dashboard `/api/meta`, and dashboard `/api/data` report consistent record counts.
- Tests cover DB present, DB missing, CSV fallback present, and CSV fallback missing.

### P0-2 - Secure API Authentication Defaults [DONE]

**Resolution:** Standardized security token validation in `dashboard_api.py` and `api.py`. Eliminated fallback default credentials and enforced constant-time string comparison (`hmac.compare_digest`).

Problem:
`dashboard_api.py` uses a public fallback token, and `api.py` has no auth.

Required implementation:

1. Require `TDR_API_TOKEN` for protected deployments.
2. Remove the hardcoded fallback token.
3. Use constant-time token comparison.
4. Apply token auth to FastAPI endpoints that expose data or trigger processing.
5. Keep `/health` public only if it does not expose sensitive data.
6. Add a clear local-dev mode, for example `TDR_AUTH_DISABLED=true`, but never enable it by default.

Files:

- `dashboard_api.py`
- `api.py`
- `.env.example`
- `docker-compose.yml`
- `Readme.md`
- `tests/test_security.py` or new API auth tests

Acceptance criteria:

- Missing token returns 401 for protected Flask and FastAPI endpoints.
- Wrong token returns 401.
- Correct token returns success.
- No source file contains a real or default shared secret.

### P0-3 - Restrict CORS And Network Binding [DONE]

**Resolution:** Added `TDR_ALLOWED_ORIGINS` to restrict CORS endpoints. Network interfaces default to loopback `127.0.0.1` unless running inside container environment.

Problem:
FastAPI allows all origins and both servers bind to `0.0.0.0` by default.

Required implementation:

1. Add `TDR_ALLOWED_ORIGINS`, defaulting to localhost dashboard origins.
2. Parse origins from env as a comma-separated list.
3. Add `TDR_API_HOST` and `TDR_DASH_HOST`, defaulting to `127.0.0.1` for local execution.
4. In Docker compose, explicitly set host/binding behavior needed for containers.

Files:

- `api.py`
- `dashboard_api.py`
- `docker-compose.yml`
- `.env.example`

Acceptance criteria:

- Local run binds to localhost by default.
- Docker still works when ports are published.
- Bandit binding warnings are either fixed or documented with targeted `# nosec` and rationale.

## P1 - CI, Tooling, And Deployment Reliability

### P1-1 - Fix Pytest Default Run [DONE]

**Resolution:** Upgraded `pytest-asyncio` dependency to `0.24.0` in `requirements.txt` to align compatibility with Python 3.12. Fixed a date-parsing order bug in `excel_utils.py` where `dd/mm` was misparsed as `mm/dd` for ambiguous cases, ensuring all tests pass without bypass parameters.

Problem:
`pytest tests/ -q` fails during collection in the current environment, while `pytest tests/ -q -p no:asyncio` passes.

Recommended implementation:

1. Upgrade `pytest-asyncio` to a compatible version or remove it if no async tests require it.
2. Add `pytest.ini` or `pyproject.toml` with explicit pytest config.
3. Ensure CI and local command use the same test behavior.

Files:

- `requirements.txt`
- `tests/`
- `.github/workflows/ci.yml`
- optional `pytest.ini`

Acceptance criteria:

- `pytest tests/ -q` passes without disabling plugins.
- CI test matrix passes on Python 3.11 and 3.12.

### P1-2 - Make Ruff Quality Gate Realistic [DONE]

**Resolution:** Configured auto-formatter to fix E701/E702/E402 style rules. Unused/duplicate imports are fixed. `ruff check .` passes with 0 errors.

Problem:
Ruff is configured in pre-commit/CI, but current code fails with 124 errors.

Required implementation:

1. Fix straightforward unused imports, duplicate imports, invalid f-strings, and module import order.
2. For large legacy files, either fix rule violations or configure scoped ignores with comments.
3. Do not hide broad categories globally unless unavoidable.

Files:

- Python source files reported by `python -m ruff check .`
- `.pre-commit-config.yaml`
- optional `pyproject.toml`

Acceptance criteria:

- `python -m ruff check .` returns 0.
- `ruff format --check .` passes or formatting policy is explicitly configured.

### P1-3 - Fix Docker Healthchecks [DONE]

**Resolution:** Standardized Docker healthchecks to use native Python `urllib` script checks in order to bypass the lack of `curl` on default Alpine/Debian base containers.

Problem:
Dockerfile healthchecks call `curl`, but `curl` is not installed.

Recommended implementation:

Option A:
Install `curl` in the base image.

Option B:
Replace healthchecks with Python standard-library checks.

Recommended choice:
Use Python healthchecks to avoid extra OS dependency.

Files:

- `Dockerfile`
- `docker-compose.yml`

Acceptance criteria:

- `docker compose build` succeeds.
- `docker compose up` marks both services healthy when apps are running.

### P1-4 - Make Security Scan Actionable [DONE]

**Resolution:** Relocated local developer cleaning scripts to `scripts/dev/` to isolate them. Added `# nosec B608` bypass annotations to safe parameterized DB execution statements. Bandit outputs 0 Medium/High errors.

Problem:
Bandit reports medium issues, some real and some false positives.

Required implementation:

1. Fix real issues: auth defaults, broad binding defaults, unchecked SQL table names where user-controlled.
2. For safe dynamic SQL over fixed allowlists, add narrow `# nosec B608` with rationale.
3. Exclude one-off local demo cleanup scripts from production scan or move them under `scripts/dev/`.

Files:

- `api.py`
- `dashboard_api.py`
- `utils/database.py`
- `check_db.py`
- `final_data_clean.py`
- `.github/workflows/ci.yml`

Acceptance criteria:

- No untriaged medium/high Bandit findings.
- CI security job fails on new high findings instead of always swallowing results.

## P2 - Frontend And Maintainability

### P2-1 - Stabilize Dashboard Frontend Delivery [DONE]

**Resolution:** Transpiled `dashboard.html` JSX code block to static `/assets/dashboard.js` bundle using local Babel transpiler. Replaced CDN imports with production builds of React/ReactDOM and eliminated `@babel/standalone` runtime dependency.

Problem:
`dashboard.html` is a large monolithic React app using CDN development builds and browser Babel.

Required implementation:

1. Short-term: switch to production UMD builds and remove browser Babel if feasible.
2. Medium-term: migrate to Vite + React + TypeScript or plain bundled React with a build artifact.
3. Keep `dashboard.html` serving behavior compatible with `dashboard_api.py` until migration is complete.

Files:

- `dashboard.html`
- `package.json`
- new frontend source directory if migrating
- `dashboard_api.py`

Acceptance criteria:

- No React development build in production dashboard.
- No runtime JSX transpilation in browser for production path.
- Dashboard still supports token entry, auto-refresh, filters, KPI target persistence, and CSV export.

### P2-2 - Normalize Versioning [DONE]

**Resolution:** Standardized release version `3.1.0` in `config.py` (`APP_VERSION`), `api.py`, `dashboard_api.py`, and test assertions (`test_config_security.py`).

Problem:
Versions differ across docs and code:

- README badge: v3.1.0
- Old roadmap: v3.2.0
- `config.py`: v1.0
- `api.py`: v3.0.0
- `dashboard_api.py`: v1.0

Required implementation:

1. Define one canonical version source.
2. Import/use it in FastAPI and Flask dashboard metadata.
3. Update README and release notes.

Recommended implementation:
Use `config.APP_VERSION` as the canonical source after updating it to the intended release version.

Files:

- `config.py`
- `api.py`
- `dashboard_api.py`
- `Readme.md`
- release notes

Acceptance criteria:

- `/health`, `/api/meta`, README, and package/build metadata agree.

### P2-3 - Clean Local Utility Scripts [DONE]

**Resolution:** Created the `scripts/dev/` directory, relocated all developer script files inside it, and documented them in `scripts/dev/README.md`.

Problem:
Ad hoc files such as `check_demo_db.py`, `check_excel_demo.py`, `clean_demo_labels.py`, and `final_data_clean.py` are in the repo root and show lint/security issues.

Required implementation:

1. Move dev-only scripts to `scripts/dev/` or remove if obsolete.
2. Add explicit documentation for any script that remains.
3. Exclude dev-only scripts from production packaging if needed.

Acceptance criteria:

- Repo root contains only primary app entrypoints and docs.
- Ruff/Bandit behavior for dev scripts is intentional.

## P3 - Product Polish

These are lower priority. Do not start until P0 and P1 are complete.

| ID | Task | Notes |
|---|---|---|
| P3-1 | Improve dashboard error boundaries | Prevent blank screen on chart/component errors |
| P3-2 | Add API response ETag or mtime-aware cache invalidation | Current Flask cache is time-only |
| P3-3 | Add integration tests for dashboard API payload shape | Protect frontend/backend contract |
| P3-4 | Add sample fixture TDR files or synthetic dataset | Make onboarding and tests reproducible |
| P3-5 | Improve observability | Structured logs are partly present, standardize request IDs and processing job IDs |

## Suggested Claude Work Plan

Give Claude this sequence as separate commits or pull requests:

1. `fix(data): unify API and dashboard SQLite source`
2. `fix(security): require token auth across protected APIs`
3. `fix(test): make pytest pass without plugin workaround`
4. `chore(lint): make ruff gate pass`
5. `fix(docker): repair healthchecks`
6. `chore(version): normalize app version metadata`
7. `refactor(frontend): prepare dashboard for production bundle`

Each commit should include tests or verification output in the commit message/PR notes.

## Definition Of Done

The remediation is complete when:

```powershell
python -m compileall -q .
pytest tests/ -q
python -m ruff check .
python -m ruff format --check .
python -m bandit -r . --exclude .\.git,.\node_modules,.\tests -ll
```

all pass or any remaining exceptions are explicitly documented with narrow, file-local rationale.

For runtime verification:

```powershell
python dashboard_api.py
uvicorn api:app --host 127.0.0.1 --port 8000
```

Then verify:

- Dashboard loads at `http://127.0.0.1:8503`.
- Protected dashboard API rejects missing/wrong token.
- Protected FastAPI endpoints reject missing/wrong token.
- Dashboard and FastAPI report the same vessel count from the same output data.
