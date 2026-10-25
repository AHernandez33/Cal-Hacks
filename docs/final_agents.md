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

The root Render Blueprint now deploys the entire app in one Docker service, including Next.js, FastAPI, and the supervised Fetch receiver. Use [the complete Render deployment guide](deploy_render.md) for the Blueprint steps, paid service/disk requirements, secure agent credentials, administrator setup, workspace sign-in, and HTTPS camera permissions. No Vercel deployment is required for this path. No public Render service has been deployed by the cloud checks.

## Delivery validation

Rebuilt from main because handoff commit bf0da1f and its artifacts were unavailable. The terminating backend suites now contain 47 tests. TypeScript, ESLint, production build, real browser flows, and launcher lifecycle checks are recorded in `docs/validation.md`. Hosted CREAO responses use mocks because real keys are only on the user's computer; genuine local Fetch is exercised separately. Native Windows execution and public deployment remain unverified.


## Browser connection refused after Ctrl+C

A `GET / 200` line means Next.js served the page. Pressing Ctrl+C stops that foreground server; a later browser request then receives connection refused. The Windows startup script opens the browser after service readiness automatically. Keep that terminal open while using the app. From the root run `powershell -ExecutionPolicy Bypass -File .\scripts\start_windows.ps1`; no dependency reinstall is needed for this change. Direct Python startup can also open the browser with `scripts/run_stack.py --open-browser`.

The `scroll-behavior: smooth` development warning is resolved by the matching data attribute on the HTML element; it was unrelated to the refused connection.


## Combined launch interface

The delivery branch also includes the recovered original logo and entrance animation, Six greenhouse scenarios navigation/page, and Free/Gold/Platinum subscription proposal cards. Use `feature/nine-agent-delivery` to receive both this interface and the camera/agent fixes. The six scenarios are fabricated educational examples, separate from the three-client federated simulation. Regular scans have no email gate, and subscriptions are not active paid products.
