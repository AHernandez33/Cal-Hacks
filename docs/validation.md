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

## Launch-experience branch: email/startup repair

The missing-SMTP 503 was reproduced in `/reports/verify/start`. This remains a real external configuration requirement; no credentials were fabricated and no email was sent during validation.

- Added public email-capability status (setting names only, never credential values).
- A real browser upload now reaches an SMTP-independent text report download. Missing email configuration hides the send form and explains availability instead of leading users into a 503 submission. Browser download content was checked against the numerical observations; no account or address was required.
- Fixed incorrect-code attempt counting: rejection previously rolled back the increment, allowing repeated guesses. The attempts now persist and are capped. Failed provider acceptance also leaves a valid code retryable instead of reporting success or silently consuming the report.
- Six isolated verification tests passed with mocked SMTP (no actual delivery). Existing API (17), workspace (12), federated (5), and integration (5) suites passed: 45 terminating tests in total.
- TypeScript, lint and production build passed. Fixed two pre-existing JSX lint errors and the introduction-animation effect error on this branch.
- Fetch entrypoint now checks an occupied receiver port before loading/starting the SDK. Local stack pins its API URL, includes local CORS origins, and generates a private report secret in the ignored .env file only when missing (without displaying it). Optional receiver termination no longer intentionally terminates the API/website; native Windows process behavior still needs verification on the user's machine.

Real SMTP delivery, a live CREAO run, real reviewed scientific passages, and the user's Windows processes are not validated by these tests.
