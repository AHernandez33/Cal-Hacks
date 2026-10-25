# Nine CREAO agents

The dashboard supports one selected role or nine independent hosted runs, with separate errors/results and automatic polling for two minutes. Manual checks retrieve existing runs. Saved external permission and per-request consent are both required. Photos are never sent to these agents. Missing telemetry, trends, privacy decisions, and visitor inputs must be reported as missing.

Set `CREAO_<ROLE>_APP_ID` and `CREAO_<ROLE>_API_KEY` in the root `.env` for COORDINATOR, CROP_INVESTIGATOR, LEAF_ANALYST, REFERENCE_RETRIEVER, RESPONSE_ADVISOR, TREND_ANALYST, PRIVACY_REVIEWER, TELEMETRY_ANALYST, VISITOR_GUIDE. Store full keys without `Bearer`. Never commit `.env`. The legacy lowercase coordinator variables remain supported. The API contract is fixed to v1: POST `/apps/APP_ID/runs`, GET `/runs/RUN_ID`. Leaf analyst receives structured measurements/observations/crop/references/question; other roles receive prompt.

Configuration check: `.venv/bin/python scripts/check_creao_agents.py` (Windows: `.venv\Scripts\python.exe`). This does not send a hosted request. `--role leaf_analyst --run` explicitly sends synthetic observations when saved external permission is enabled; `--run-id ID` polls the existing run. HTTP acceptance is not proof of completion. Real keys are available only on the user's computer; cloud tests use mocks.

Start the normal stack before running `scripts/check_fetch.py`. It performs genuine local uAgents messaging without an API key. Public-ledger warnings do not establish local messaging failure.

Regular image scans have no email gate. Remote workspace/admin authorization remains required. No reviewed scientific corpus, live Tiger Data read, or actual farm federated training is claimed. Revoke the previously exposed CREAO key in provider settings; this checkout cannot verify revocation.

## Windows update

Stop the stack with Ctrl+C. Open PowerShell in `C:\Users\herna\Cal Hacks\SCD\VigiloForge-CLEAN`. Preserve local work with `git stash push --include-untracked -m "Before nine-agent update"`; ignored `.env` files stay in place. Fetch the delivery branch, then merge it (no reset or force push). If Git reports a conflict, stop and resolve it in VS Code. Restore your stash with `git stash apply`; keep it until the result is verified. Review any conflicts in your own check scripts.

Run `powershell -ExecutionPolicy Bypass -File .\scripts\start_windows.ps1 -Install` once to refresh dependencies after updating. Subsequent starts: `.\.venv\Scripts\python.exe scripts/run_stack.py`. Open port 3000 in your local browser.

## Online deployment

There is no single command that publishes both services with credentials and persistent storage. The existing Render blueprint provisions a paid API disk; review its cost before creating it. Set FRONTEND_ORIGIN to the deployed frontend HTTPS origin, keep VIGILO_API_TOKEN private, and add CREAO keys securely on Render. The current blueprint runs the API only: local Fetch needs a separately supervised receiver (or a real HTTPS receiver configured with its matching address). Do not claim online Fetch works without that receiver.

Deploy the frontend from `frontend` with `npx vercel --prod` after setting NEXT_PUBLIC_API_URL to the HTTPS Render API address in Vercel project settings. This command requires your Vercel login/project and triggers deployment; the address must be set before building. Remote users sign in with a workspace key provisioned by the deployment administrator. The admin token must never become NEXT_PUBLIC_* configuration. No public deployment has been performed by this update.

## Delivery validation

Rebuilt from main because handoff commit bf0da1f and its artifacts were unavailable. Backend: 44 tests passed (39 existing plus five new CREAO contract/privacy/ownership tests, including all nine roles). TypeScript, ESLint, and production build passed. Hosted CREAO requests were mocked; no real provider credentials were present. Genuine local Fetch messaging is checked separately using scripts/check_fetch.py. Native Windows execution and public deployment remain unverified.
