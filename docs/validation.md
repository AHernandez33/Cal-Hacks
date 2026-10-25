# Validation record — October 24, 2026 (Pacific time)

This records observed outcomes, not a claim that external services or real crops were validated.

## Current update

| Check | Outcome |
| --- | --- |
| API suite (`test_api.py`) | 17 passed |
| Existing federated suite (`test_federated.py`) | 5 passed |
| Workspace suite (`test_workspaces.py`) | 12 passed |
| Integration diagnostics suite (`test_integrations.py`) | 5 passed |
| Total terminating backend tests | **39 passed** |
| TypeScript | Passed |
| ESLint | Passed, no errors or warnings |
| Next.js production build | Passed; dashboard, field, federated, login, plans, research and offline routes generated |
| Python full-stack launcher | Started API, genuine Fetch receiver and development frontend from one checkout; stop signal cleaned up all child services |
| Windows PowerShell wrapper | Reviewed; not executable on this Linux host, so native Windows operation is unverified |
| Chromium workspace creation / sign-in / logout | Passed; revoked session rejected by API |
| Two-account preference and photo-store separation | Passed in browser and API checks |
| Camera permission / stream open-stop | Passed with browser-simulated hardware; not a physical camera test |
| Real image upload and explained heatmap | Passed with a synthetic green-leaf-shaped fixture |
| Workspace consent → genuine local Fetch message → report | Passed; actual agent response received |
| Ten-round federated model page | Passed; two charts and ten history rows reflect the actual generated training results |
| Research page and actual SQLite retrieval | Passed; correctly reported zero vetted passages instead of citing the placeholder |
| Plans page | Correctly showed free access and no configured paid billing |
| Six pages at 390px width | No horizontal overflow |
| Browser JavaScript errors in tested feature flow | None |
| Production PWA worker v4 and account-scoped offline history | Passed; queued photo survived offline reload, then synchronized with explicit consent after reconnect |
| Final production API → Fetch receiver | HTTP 200 genuine message response with workspace authorization |

Workspace tests cover credential hashing, session expiry/revocation, account deletion, cross-workspace privacy/audit/run ownership, remote signup restrictions, and uncached API responses. Integration tests distinguish a responding receiver endpoint from verified agent messaging, reject remote plain HTTP/credential-bearing URLs, and verify placeholder exclusion.

The existing `tests/test_fetch_message.py` is an interactive continuous demonstration and was not counted as a terminating unit test.

## Remaining external validation

- Tiger Data credentials and a real historical dataset were unavailable. The diagnostic returned a clear not-configured failure; no live database success is claimed.
- CREAO/LLM work was intentionally excluded. Its existing adapter is unverified against a live hosted app and may need contract changes.
- The scientific corpus still contains only an illustrative source, which is excluded from retrieval. A university source request returned HTTP 403 in this environment; no source text was invented or silently promoted to vetted evidence.
- Original logo artwork was visible in chat but unavailable as an accessible image file. Its PNG still needs to be supplied; the missing-artwork state remains honest.
- Real phone cameras, NexiGo hardware, Android/iOS PWA installation, public Render/Vercel deployments, native Windows execution and paid billing remain unverified.
- Federated results are synthetic single-machine simulations, not farm-field performance; no secure aggregation or differential privacy is claimed.
- Authorized workspaces share the installation's telemetry feed. Per-farm database isolation is not implemented.

See `integrations_setup.md` for the exact outside actions needed to complete provider and corpus setup.


## Nine-agent delivery follow-up — October 25, 2026 (Pacific time)

- 47 terminating backend tests passed: API 17, federated 5, workspaces 12, integrations 5, CREAO 8. CREAO subtests cover all nine app/key pairs, leaf structured inputs, outbound privacy rejection, output variants, immediate completion, role ownership, account deletion, and coordinator credential consistency.
- TypeScript, ESLint, and Next.js production build passed.
- Headless system Chromium exercised a real image upload/API response and input reset, one immediately completed hosted response, nine distinct CREAO starts, seven completed outputs alongside independent POST and polling failures, and manual status checking without a new start. CREAO transport was mocked; no live CREAO keys were available.
- The same browser flow then displayed a genuine local Fetch request/response, with no page JavaScript errors.
- Full-stack launcher passed readiness checks, frontend page retrieval, genuine API-to-Fetch messaging, and SIGTERM cleanup of all three service ports on Linux.
- Backend-only launcher passed custom API-port startup, genuine API-to-Fetch messaging, and required-child failure detection. Stopping the receiver failed the supervisor and cleaned up the API; no frontend was started in backend-only mode.
- The Render blueprint now uses the backend-only supervisor. Its configuration was exercised locally; no Render/Vercel service was provisioned or deployed.
- Windows script changes were reviewed on Linux. Native Windows process checks and repair execution remain unverified. The launcher refuses installation while matching project Node processes or stack listeners remain and supports frontend-only repair without reinstalling Python dependencies.
- Live CREAO completion, provider-side revocation of previously exposed keys, optional live Tiger Data, public deployment, original logo artwork, and physical-device testing remain outside these verified outcomes.
