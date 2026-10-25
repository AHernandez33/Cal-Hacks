# VigiloForge — Secured Crop Detector

**Smarter Farming. Private by Design.** A Cal Hacks 13.0 research prototype.

FastAPI/OpenCV, Next.js, SQLite FTS5 public-reference retrieval, genuine local Fetch.ai messaging, and a synthetic PyTorch federated learning demonstration. Local investigation stages use rules/retrieval. Nine optional CREAO specialists run independently through their hosted apps.

## Start on Windows (VS Code / PowerShell)

Use the updated checkout containing `backend/`, `frontend/`, `requirements.txt`, and `scripts/`. The older `Cal Hacks/SCD/1` copy is a separate folder and does not update when another checkout is pulled.

```powershell
cd "C:\Users\herna\VigiloForge-neon"
git pull --ff-only origin main
powershell -ExecutionPolicy RemoteSigned -File .\scripts\start_windows.ps1 -Install
```

If you used a different fresh checkout, change only the first path. Stop and read the error if `cd` or `git pull` fails; do not keep running commands in the old folder. Open the same folder in VS Code (`code .`). Preserve local edits before pulling.

The launcher uses Python 3.12, installs CPU dependencies and frozen npm dependencies, initializes the RAG index, then starts FastAPI, the Fetch receiver, and Next.js **from the same root**. Existing `.env` and `.env.local` files are preserved. Keep the terminal open; Ctrl+C stops the stack. Stop old servers first if ports 8000, 8001, or 3000 are occupied. The launcher never stops an unrelated application.

Subsequent starts when dependencies have not changed:

```powershell
powershell -ExecutionPolicy RemoteSigned -File .\scripts\start_windows.ps1
```

Open the local application at port 3000. It does not require a deployment administrator token for loopback development. Use `/login` for a separate workspace or the dashboard's local demo. Fetch may take time to finish SDK initialization; verify a real consented message after startup.

The PowerShell wrapper was reviewed on Linux but could not be executed on Windows here. The underlying Python launcher and application flows were exercised in this environment. Python 3.12, Node 22+, and npm are required.

## Linux / cloud

Use the existing checkout; cloud tasks are already isolated. Do not create a Git worktree unless explicitly requested.

```bash
bash scripts/setup.sh
# Only if these do not already exist:
cp -n .env.example .env
cp -n frontend/.env.example frontend/.env.local
.venv/bin/python scripts/prepare_data.py
.venv/bin/python scripts/run_stack.py
```

`run_stack.py` starts a development frontend; use a production build for PWA testing. For manual service startup:

```bash
.venv/bin/python -m uvicorn backend.main:app --env-file .env --host 127.0.0.1 --port 8000
.venv/bin/python scripts/run_fetch.py
# In another terminal:
cd frontend
npm run dev -- --hostname 127.0.0.1
```

On Windows, replace `.venv/bin/python` with `.\.venv\Scripts\python.exe`.

## Pages and workflow

| Page | Purpose |
| --- | --- |
| `/` | Image upload/camera, numerical observations, explained heatmap, consented investigation, privacy controls, telemetry, integration diagnostics |
| `/federated` | Three explicitly simulated clients, real ten-round training charts, model architecture, metric definitions, local-only comparison |
| `/research` | Search the actual SQLite FTS5 index, inspect passage counts and source links; no LLM answer |
| `/field` | Mobile photo storage, queue, explicit synchronization, installation guidance |
| `/login` | Create/sign in to a pseudonymous workspace with a private key; no name or email |
| `/plans` | Free prototype plan and a clearly unavailable future pilot; no live billing |

Image features and the anomaly index are heuristics, not disease diagnoses or probabilities. The overlay marks yellow/brown classification regions; it is not a temperature map. Camera direction/device controls support rear phone cameras and selectable webcams, subject to real browser/device permissions.

The federated model is LeafRiskMLP (5 → 64 → 32 → 16 → 1) trained on fabricated numerical observations and labels. Simulated greenhouses are datasets on one machine, not connected physical farms. FedAvg averages parameter updates; it provides neither secure aggregation nor differential privacy. Client opt-ins apply only to that run. The compute-heavy demo remains loopback-only.

## Private workspaces

A workspace key is generated once and stored only as a hash on the backend. It is the recovery/sign-in credential; no email recovery exists. Login issues a 24-hour bearer session held in browser session storage. Signing out revokes that session. Workspace deletion removes active server records; browser photos, backups, and provider-held data require separate handling.

Preferences, CREAO run ownership, audit visibility, and in-app browser-photo storage are scoped to each workspace. Browser stores are not encrypted and remain accessible to someone controlling that browser profile. Keep the workspace key in a password manager; never include it in screenshots or Git.

Unsigned local development uses a separate shared demo workspace. Do not treat it as a private account. `VIGILO_API_TOKEN` is an optional **administrator setup password**, not a customer login. Remote registration requires administrator authorization; pilot users sign in using privately supplied workspace keys. All current features are on the free prototype plan; paid billing is not configured.

Before public deployment use HTTPS, persistent storage, ingress request limits, and trusted pilot users. The telemetry feed is shared at installation level, so per-farm authorization must be added before hosting private multi-farm records.

## Privacy / offline behavior

Saved external-service permission and per-request consent are both checked by the backend. Only permitted numerical observations, broad crop category, anomaly score, and curated public passages can reach agents; images are excluded. Queued photo sync separately requires its saved preference and explicit permission. Synced images are processed and returned, not retained on the server.

Photos are stored in IndexedDB under the current workspace. Retention choice controls new saves; delete existing photos explicitly. Its last loaded choice is retained locally for offline use. Sign in online before relying on account-specific offline storage in a new tab/session. Signing out does not erase saved photos.

Production PWA shell/static assets are cached; API responses, credentials, and photos are not stored in the service-worker cache. Visit dashboard/Field Mode online before using them offline. OpenCV and agents require the server. For production testing:

```bash
cd frontend
npm run build
npm run start -- --hostname 127.0.0.1
```

A physical phone needs a deployed HTTPS origin; a laptop's loopback URL is not reachable from the phone. iOS/Android installation and physical devices still require testing. Browser storage can be evicted, so local history is not a durable backup.

## Integrations and scientific evidence

Read [the complete setup checklist](docs/integrations_setup.md) for Tiger Data, Fetch.ai, CREAO, and the scientific corpus.

SQLite retrieval is in `backend/RAG/retrieve.py`; ingestion is in `backend/RAG/ingest.py`. API routes are `/knowledge/status` and `/knowledge/search?query=leaf+yellowing`. The bundled example.org placeholder is excluded from evidence. Add reviewed agricultural passages and run `scripts/prepare_data.py` before expecting scientific citations. Suggested organization links are not presented as retrieved evidence.

Tiger Data uses `TIGER_DATABASE_URL` with full TLS verification and a read-only database role. Apply `docs/telemetry_schema.sql`, import actual readings, and run `scripts/check_tiger.py`. Demo telemetry is separate and explicitly synthetic. Credentials and a real cloud database were not available for validation.

Fetch uses the API's interpreter by default; both receiver and client load the same `.env`. The client auto-derives the local receiver address unless overridden. `FETCH_AGENT_ENDPOINT` can specify a remote HTTPS receiver. Configuration/port reachability does not prove a successful agent-message response. Public Agentverse/mailbox integration is not verified.

CREAO supports nine independent specialists with role-specific app IDs/keys, individual results/errors, and automatic polling. See [the agent delivery guide](docs/final_agents.md). Hosted calls were tested with mocks; verify live completion using your own keys. Four local report stages do not establish hosted agent execution.

## Original artwork

The animated banner uses `frontend/public/vigiloforge-logo.png` at the supplied 3:1 aspect ratio, with a light sweep, glow and reduced-motion support. Original typography is preserved by using the image. The chat preview was not available as a downloadable asset; the PNG still needs to be supplied. No replacement logo was invented. UI fonts are self-hosted Inter and Orbitron.

## Validation

```bash
.venv/bin/python -m unittest discover -s tests -p test_api.py
.venv/bin/python -m unittest discover -s tests -p test_federated.py
.venv/bin/python -m unittest discover -s tests -p test_workspaces.py
.venv/bin/python -m unittest discover -s tests -p test_integrations.py
.venv/bin/python -m unittest discover -s tests -p test_creao_agents.py
cd frontend
npx tsc --noEmit
npm run lint
npm run build
```

Do not use unrestricted test discovery: `test_fetch_message.py` is a continuous interactive agent demonstration, not a terminating suite. See `docs/validation.md` for actual outcomes and remaining limitations.

## Deployment

Deploy the complete app with the root Render Blueprint: Docker runs Next.js, FastAPI, and the supervised local Fetch receiver behind one HTTPS URL. See [the full Render walkthrough](docs/deploy_render.md). The Standard service and persistent disk are paid; review Render's displayed price before creating them. Backend credentials belong in Render's environment settings, never in frontend `NEXT_PUBLIC_*` variables.

Public users sign in with private workspace keys provisioned by the administrator. The production launcher requires a private administrator token to protect loopback API requests behind the frontend proxy. Local development still supports the shared demo without an email gate.

Camera capture now waits for decoded video, displays a captured-photo preview/download, and reports blocked permissions or disconnected devices. Physical webcams and phones still need device testing. On Windows, stop existing app terminals before startup. For a Next.js native-module EPERM failure, use `scripts/start_windows.ps1 -RepairFrontend` after releasing the lock. See [the delivery guide](docs/final_agents.md).
