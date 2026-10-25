# Nine CREAO agents

The dashboard supports one selected role or nine independent hosted runs, with separate errors/results and automatic polling for two minutes. Manual checks retrieve existing runs. Saved external permission and per-request consent are both required. Photos are never sent to these agents. Missing telemetry, trends, privacy decisions, and visitor inputs must be reported as missing.

Set `CREAO_<ROLE>_APP_ID` and `CREAO_<ROLE>_API_KEY` in the root `.env` for COORDINATOR, CROP_INVESTIGATOR, LEAF_ANALYST, REFERENCE_RETRIEVER, RESPONSE_ADVISOR, TREND_ANALYST, PRIVACY_REVIEWER, TELEMETRY_ANALYST, VISITOR_GUIDE. Store full keys without `Bearer`. Never commit `.env`. The legacy lowercase coordinator variables remain supported. The API contract is fixed to v1: POST `/apps/APP_ID/runs`, GET `/runs/RUN_ID`. Leaf analyst receives structured measurements/observations/crop/references/question; other roles receive prompt.

Configuration check: `.venv/bin/python scripts/check_creao_agents.py` (Windows: `.venv\Scripts\python.exe`). This does not send a hosted request. `--role leaf_analyst --run` explicitly sends synthetic observations when saved external permission is enabled; `--run-id ID` polls the existing run. HTTP acceptance is not proof of completion. Real keys are available only on the user's computer; cloud tests use mocks.

Start the normal stack before running `scripts/check_fetch.py`. It performs genuine local uAgents messaging without an API key. Public-ledger warnings do not establish local messaging failure.

Regular image scans have no email gate. Remote workspace/admin authorization remains required. No reviewed scientific corpus, live Tiger Data read, or actual farm federated training is claimed. Revoke the previously exposed CREAO key in provider settings; this checkout cannot verify revocation.

## Windows update

Stop the stack with Ctrl+C. Open PowerShell in `C:\Users\herna\Cal Hacks\SCD\VigiloForge-CLEAN`. Preserve local work with `git stash push --include-untracked -m "Before nine-agent update"`; ignored `.env` files stay in place. Fetch the delivery branch, then merge it (no reset or force push). If Git reports a conflict, stop and resolve it in VS Code. Restore your stash with `git stash apply`; keep it until the result is verified. Review any conflicts in your own check scripts.

Run `powershell -ExecutionPolicy Bypass -File .\scripts\start_windows.ps1 -Install` once to refresh dependencies after updating. Subsequent starts: `.\.venv\Scripts\python.exe scripts/run_stack.py`. Open port 3000 in your local browser.

## Windows EPERM repair

Before installing, the Windows launcher checks for Node processes belonging to this checkout and occupied stack ports. It lists matching project PIDs and exits without killing unrelated applications. Stop this app with Ctrl+C first. If Next.js's native module remains locked, restart Windows, then run:

```powershell
cd "C:\Users\herna\Cal Hacks\SCD\VigiloForge-CLEAN"
powershell -ExecutionPolicy Bypass -File .\scripts\start_windows.ps1 -RepairFrontend
```

This refreshes only frontend dependencies with `npm ci`, prepares SQLite, then starts the app. It preserves `.env`, `.env.local`, the lockfile, and source. Python packages are installed only with `-Install` or when creating a missing environment. A native Windows run remains unverified in the Linux cloud.

## Online deployment

No public deployment was performed. The existing Render blueprint provisions a paid API disk. Review the service cost before creating it and select the `feature/nine-agent-delivery` branch while the update is awaiting merge. The blueprint's start command now supervises both FastAPI and the local Fetch receiver, without requiring Node on the backend:

```bash
python scripts/prepare_data.py && python scripts/run_stack.py --backend-only --host 0.0.0.0 --port "$PORT"
```

Set FRONTEND_ORIGIN to the deployed frontend HTTPS origin. Keep VIGILO_API_TOKEN and CREAO credentials in Render's secure environment settings. For a deployed Fetch identity, set the same private FETCH_AGENT_SEED for API and receiver (both inherit the service environment). Never fund the public demo seed. The receiver stays behind the backend service; the browser calls the API. The supervisor stops its children on shutdown and fails if a required child exits.

Deploy the frontend from `frontend` with `npx vercel --prod` after setting NEXT_PUBLIC_API_URL to the HTTPS Render API address in Vercel project settings. This command requires your Vercel login/project and triggers deployment; the address must be set before building. Set Render's FRONTEND_ORIGIN to the final frontend origin and redeploy if necessary. Remote users sign in with a workspace key provisioned by the deployment administrator. The admin token must never become NEXT_PUBLIC_* configuration.

Check `/health`, sign in, upload an image, enable external services, and verify a genuine Fetch response and completed CREAO outputs after deployment. Local validation does not prove a hosted service has been deployed or is working.

## Delivery validation

Rebuilt from main because handoff commit bf0da1f and its artifacts were unavailable. The terminating backend suites now contain 47 tests. TypeScript, ESLint, production build, real browser flows, and launcher lifecycle checks are recorded in `docs/validation.md`. Hosted CREAO responses use mocks because real keys are only on the user's computer; genuine local Fetch is exercised separately. Native Windows execution and public deployment remain unverified.
