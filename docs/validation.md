# Verified scope — October 24, 2026

Validated in the cloud checkout, using Python 3.12.14, Node 24.19.0, and CPU PyTorch.

| Check | Result |
| --- | --- |
| `bash scripts/setup.sh` | Passed, including a repeated run |
| Python imports / compilation | Passed |
| `test_api.py` | 17 tests passed |
| `test_federated.py` | 5 tests passed |
| Ten-round synthetic federated API run | Passed within API tests |
| `npx tsc --noEmit` | Passed |
| `npm run lint` | Passed without errors or warnings |
| `npm run build` | Passed |
| FastAPI health and Next production startup | Passed |
| Real local Fetch.ai request through FastAPI | HTTP 200, genuine agent-message response |
| Chromium: upload → OpenCV → local report | Passed |
| Chromium: upload → Fetch report | Passed |
| Chromium: IndexedDB save → queue → consent → backend analysis | Passed |
| Chromium: offline reload of warmed Field Mode | Passed; saved photo history visible |
| Chromium: 390px viewport | No horizontal overflow |
| Browser JavaScript errors in tested flow | None |

The existing Fetch interactive demonstration was not represented as a completed unit suite. The existing 5 federated tests and 17 added API tests are terminating automated checks. Browser checks used a synthetic green ellipse image, actual running API/agent/frontend processes, and system Chromium through Playwright. They do not establish biological accuracy or physical-camera compatibility.

The Fetch SDK logged unavailable ledger/registry services during startup. Local direct messaging nevertheless completed successfully after startup. Public Agentverse registration and mailbox communication were not tested.

The current scientific corpus contains only an example.org placeholder. Search excludes that domain, so the observed reports correctly returned zero citations. Add manually reviewed source passages; no real citations or scientific claims were invented.

CREAO and Tiger Data were tested only for honest missing-configuration behavior. There were no credentials for successful live-provider checks. CREAO request/response compatibility, multi-agent execution on CREAO, and a real PostgreSQL query remain unverified.

Original logo artwork was absent. The tested UI showed a pending-artwork notice. PWA installability on physical Android/iOS devices, actual webcam capture, public Render/Vercel deployments, custom domains, reverse-proxy behavior, and multi-user authorization remain outside the validated scope.

## Remaining actions

1. Supply `frontend/public/vigiloforge-logo.png`.
2. Replace illustrative knowledge data with reviewed public agricultural material, then rerun ingestion.
3. Configure a real CREAO hosted app and securely supply its credentials; verify the API contract and run-result polling.
4. Provision Tiger Data, apply `telemetry_schema.sql`, ingest real sensor observations, and configure a read-only TLS-verified connection.
5. Review deployment costs/settings and deploy Render + Vercel; set the actual API URL and frontend CORS origin.
6. Configure Fetch process supervision / transport for hosted deployment. The supplied Render blueprint starts only FastAPI.
7. Test phone/webcam permissions, PWA installation, offline reload, and consent-controlled synchronization on physical devices.
8. Add per-user identity/permissions and ingress request limits before turning the single-grower prototype into a multi-user product.

The cloud installation/startup instructions were saved as configuration draft fields. Draft persistence does not publish an environment or prove restoration in a fresh task.
