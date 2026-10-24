# VigiloForge — Secured Crop Detector

**Smarter Farming. Private by Design.** Cal Hacks 13.0 research prototype.

Next.js dashboard + FastAPI/OpenCV + SQLite FTS5 + local Fetch.ai messaging + synthetic PyTorch federated averaging. Local investigation stages are rules and retrieval, not four independently hosted AI agents. CREAO is an optional hosted-agent integration.

## Requirements

- Python 3.12, Node.js 22+ (validated here on Python 3.12.14 / Node 24.19.0).
- CPU is sufficient. Camera access needs a browser on localhost or HTTPS.
- Use the existing checkout. Cloud tasks are already isolated; do not create a worktree unless requested.

## Installation on Linux / Codex cloud

From the repository root:

```bash
bash scripts/setup.sh
cp .env.example .env
cp frontend/.env.example frontend/.env.local
```

The script installs Python packages in `.venv`, runs frozen npm installation, and initializes a separate SQLite database at `.local/vigiloforge.db`. It preserves the uploaded `data/vigiloforge.db`. The current knowledge file contains an illustrative reference; it is indexed for setup but deliberately excluded from scientific search results. Add reviewed public references using the existing JSON schema and rerun ingestion before claiming evidence-backed results.

## Installation on Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
Copy-Item frontend/.env.example frontend/.env.local
$env:SQLITE_DB_PATH = ".local/vigiloforge.db"
.\.venv\Scripts\python.exe -m backend.RAG.ingest
cd frontend
npm ci
cd ..
```

Do not overwrite an existing `.env` or `.env.local`; merge the documented variable names instead. Keep their values out of Git. On Windows, replace `.venv/bin/python` below with `.\.venv\Scripts\python.exe`.

## Run (three terminals)

Backend, from repository root:

```bash
.venv/bin/python -m uvicorn backend.main:app --env-file .env --host 127.0.0.1 --port 8000
```

Optional local Fetch agent, from repository root (loads the same seed and database settings):

```bash
.venv/bin/python scripts/run_fetch.py
```

Frontend:

```bash
cd frontend
npm run dev -- --hostname 127.0.0.1
```

The agent client defaults to the backend's Python interpreter. Set `FETCH_PYTHON` only if a separate compatible environment is needed. Its address is derived from the same `FETCH_AGENT_SEED` as the receiver; `fetch_agent_address` is an optional override for a different locally reachable receiver. Local messaging uses port 8001 and does not need public registration. The SDK may still probe its ledger during initialization; a ledger warning does not establish local messaging failure.

Check backend `/health`, then open the dashboard in your local browser. Use Privacy → Connect / refresh before changing preferences. If the backend has `VIGILO_API_TOKEN`, enter it there. The token is stored only in that browser tab's session storage and is not compiled into public JavaScript.

## Workflow and privacy

1. Upload or capture one leaf. The backend returns five numerical features and a private heatmap. No disease diagnosis is produced.
2. Request a **local** investigation for an explicitly labeled rules/retrieval report.
3. For Fetch or CREAO, first enable external services, then authorize the specific request. The backend checks both permissions and restricts payload fields. Raw photos are not sent to agents.
4. The synthetic federated demo requires separate per-client opt-in for each run. Its metrics are simulation results; the demo is not connected to real customer training and provides neither differential privacy nor secure aggregation.
5. Field Mode can retain photos in IndexedDB, queue them, and synchronize with explicit permission after reconnecting. Sync processes photos without storing them on the server or invoking agents. Revoking sync blocks subsequent requests; it cannot recall an upload already in progress.
6. Retention permission controls new browser saves. Delete previously saved photos in Field Mode. The last loaded retention choice is kept on the device for offline use; this is a browser-storage setting, not a server retention guarantee.

This is a **single-grower installation**, not a multi-tenant service. Preferences and CREAO run ownership apply to the deployment. All non-health API routes require the configured bearer token; when absent they are restricted to loopback clients. Do not publish the token as a `NEXT_PUBLIC_*` variable. Do not expose a tokenless API behind a reverse proxy: the proxy may appear as a loopback client. Before supporting multiple growers, implement user accounts, per-user preferences, run ownership, quotas, and request limits at the ingress/application layer.

## Original logo

Supply your existing artwork at `frontend/public/vigiloforge-logo.png`. It is displayed with `next/image`; a visible pending-artwork message appears when absent. No replacement logo was invented. PWA PNG icons are rasterizations of the existing leaf icon, not the VigiloForge banner.

The black/green/cyan dashboard uses self-hosted Orbitron and Inter font packages, animated borders, button shine, and reduced-motion support. Existing duplicate starter files are preserved and excluded from the active frontend's TypeScript and lint scopes.

## CREAO

Configure `creao_api_key` and `creao_app_id` securely on the backend. The hosted app must have a text input called `prompt`. The adapter currently targets `https://agent.creao.ai/api/v1`; verify its request/response contract against your hosted app. This integration has not been validated with real credentials.

Request CREAO from the investigation panel and use **Check hosted run status** to poll. Only run IDs created through this installation are available through that route. The local four-stage checklist is not evidence that four CREAO agents ran. Configure and verify your hosted multi-agent workflow separately.

## Tiger Data

Create the table in `docs/telemetry_schema.sql` and populate it with actual telemetry. Set `TIGER_DATABASE_URL` securely for a read-only PostgreSQL role. The connection uses `sslmode=verify-full`; configure the provider's CA using supported PostgreSQL trust settings if necessary. Do not disable TLS verification.

`GET /telemetry/history` reads actual records and returns 503 when unconfigured/unreachable. `GET /telemetry/history?source=demo` is an explicitly labeled synthetic alternative. This service requires direct PostgreSQL connectivity; an HTTPS-only secret proxy cannot provide PostgreSQL authentication. No live cloud database was available for validation.

## PWA / mobile validation

Use a production build on HTTPS (or localhost). The service worker registers only in production. Visit the dashboard and Field Mode online before testing offline. Public shell assets and Next.js static chunks are cached; API responses, photos, and access tokens are not placed in the service-worker cache. Photos remain in IndexedDB until deleted. Browser data eviction/clearing can delete them; this is not a durable backup.

Cloud agents and server OpenCV do not work offline. Install prompts vary by browser. Android/iOS installation and physical camera devices still require manual testing. Cached shell versions can remain until a new worker activates; increment its cache version with future shell changes.

## Checks

From repository root:

```bash
.venv/bin/python -m unittest discover -s tests -p test_api.py
.venv/bin/python -m unittest discover -s tests -p test_federated.py
```

The existing `tests/test_fetch_message.py` is a continuously running interactive agent demonstration, not a terminating unit test. Do not use unrestricted test discovery to run it as a CI suite. For local messaging, start `scripts/run_fetch.py`, enable external services, and request Fetch from the dashboard.

Frontend:

```bash
cd frontend
npx tsc --noEmit
npm run lint
npm run build
npm run start -- --hostname 127.0.0.1
```

See `docs/validation.md` for the outcomes verified for this update.

## Render + Vercel

`render.yaml` describes a single-instance FastAPI service with a paid persistent disk for SQLite. Review costs and settings before creating it. Set `FRONTEND_ORIGIN` to your actual HTTPS frontend origin. The generated `VIGILO_API_TOKEN` belongs only on the backend and in the owner's browser session. Keep a secure copy. Optional CREAO/Tiger variables are set separately in service settings.

On Vercel, select `frontend` as the root directory, use `npm ci` / `npm run build`, and set `NEXT_PUBLIC_API_URL` to the actual HTTPS Render URL **before building**. Changes to this variable require rebuilding the frontend. Never use a loopback API URL for mobile/public deployments.

The Render blueprint starts only FastAPI. Its Fetch subprocess requires a separately running receiver reachable through a supported endpoint; the current direct resolver assumes that receiver is on the same machine at port 8001. Until you configure a supervised same-machine receiver or adapt its transport, use local investigations or configured CREAO on Render. The compute-intensive federated endpoint remains loopback-only and must not be exposed by changing that restriction alone.

After deployment verify health, authenticated image upload, CORS, rejected unauthorized requests, privacy persistence across restarts, and the real frontend-to-backend flow. Public deployment, provider credentials, domain setup, and physical device validation are not completed by adding these files.
