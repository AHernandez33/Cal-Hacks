# External setup checklist

Never send credentials in chat or commit them to Git. Supply them through the local root `.env` or hosting provider's secure environment settings. Restart the backend/receiver after changes. Configuration presence is not proof of successful integration.

## Tiger Data

1. Create a PostgreSQL/Timescale service in your Tiger Data account. Choose a region and plan appropriate for your demo; review its price before provisioning.
2. In its SQL editor, run `docs/telemetry_schema.sql` to create `greenhouse_telemetry`. Its columns are `timestamp`, `soil_moisture` (0–1), `temperature_c`, and `humidity_pct` (0–100).
3. Import actual historical sensor records into that table. An empty table can connect successfully but cannot display a history. Keep synthetic samples in the separately labeled demo; do not pass them off as actual measurements.
4. Create an application database role with only CONNECT, schema USAGE, and SELECT on the telemetry table. Use a separate owner role for imports and schema changes. Example grants (replace your database/role names):

   ```sql
   GRANT CONNECT ON DATABASE your_database TO your_app_role;
   GRANT USAGE ON SCHEMA public TO your_app_role;
   GRANT SELECT ON greenhouse_telemetry TO your_app_role;
   ```

5. Put the role's PostgreSQL connection string in `TIGER_DATABASE_URL`. Use the provider's hostname, port, database, and read-only credentials. The adapter enforces `sslmode=verify-full`; install/configure the provider's CA certificate using PostgreSQL's supported trust configuration when needed. Do not disable certificate verification.
6. Ensure the machine hosting FastAPI can reach that PostgreSQL host/port. An HTTPS-only proxy does not carry PostgreSQL sessions. Restrict network access using your provider's available controls.
7. From the project root run `.venv/bin/python scripts/check_tiger.py` (Windows: `.\.venv\Scripts\python.exe scripts/check_tiger.py`). It prints only a successful record count or a sanitized error.
8. In the dashboard choose **Load database history**. A successful query with rows is the real validation. **View synthetic demo** does not validate the connection.

The current telemetry feed belongs to the installation and is shared with authorized workspaces. There is no per-farm telemetry authorization or tenant partitioning. Use a non-private demonstration dataset and trusted pilot accounts; a multi-farm product needs per-owner rows and query authorization.

## Fetch.ai (local demo)

1. Use Python 3.12 and install `requirements.txt` into the same `.venv` used by the API.
2. Start the entire stack with `scripts/start_windows.ps1` or `.venv/bin/python scripts/run_stack.py`. This starts the genuine uAgent receiver on port 8001 as well as FastAPI and Next.js.
3. Both processes load the SAME project root `.env`. Leave `FETCH_PYTHON` blank unless you intentionally use a second compatible environment. Do not point it to an old Windows project or deleted virtual environment.
4. Leave `fetch_agent_address` blank for the bundled receiver: the client derives the matching address automatically. Keep `FETCH_MAILBOX=false` for direct local messaging. `FETCH_AGENT_ENDPOINT` defaults to `http://127.0.0.1:8001/submit`.
5. For a deployed identity, set a private `FETCH_AGENT_SEED` consistently for the receiver and API. The default seed is public and suitable only for a local synthetic demonstration, not a funded wallet or private agent identity.
6. Wait for **Fetch agent started**. The SDK can delay startup while probing ledger/registry services; a local listening port alone does not prove messaging works.
7. Choose **Check integration status** on the dashboard. Its result distinguishes an interpreter problem, missing SDK, and unavailable receiver. A responding endpoint still needs a real message test.
8. Enable external agent services in the current workspace's Privacy settings. Analyze a leaf, select Fetch.ai, authorize that request, and submit it. A genuine completed response is the end-to-end check.

No Fetch API key is required for this bundled direct local demo. It uses the actual uAgents messaging SDK and local scientific retrieval, not an LLM. Public Agentverse/mailbox registration, discovery, billing, and hosted agents are separate capabilities and are not validated here.

For a remote receiver, configure an HTTPS `FETCH_AGENT_ENDPOINT` and the receiver's actual `fetch_agent_address`, plus supported connectivity from the API. Never use a laptop's loopback address from a hosted Render service. The supplied Render Blueprint runs Next.js, FastAPI, and the supervised local receiver in one Docker service using `scripts/run_stack.py --production`. API and receiver share the server-side environment and SQLite index. See [the Render guide](deploy_render.md). Public Agentverse hosting remains separate.

## Nine CREAO specialists

See [final_agents.md](final_agents.md) for role names, secure configuration, check commands, and delivery instructions. Each role uses `CREAO_<ROLE>_APP_ID` and `CREAO_<ROLE>_API_KEY`. Supply the full key without a Bearer prefix. Legacy lowercase variables are a fallback only when both coordinator-specific variables are absent. Version v1 is supported.

The adapter starts `POST https://agent.creao.ai/api/v1/apps/APP_ID/runs` with `{"inputs": {...}}` and polls `GET /api/v1/runs/RUN_ID` using that role's matching key. Leaf analyst uses measurements/observations/crop/references/question. Other roles use prompt. Separate hosted runs are independent; they are not a chained coordinator execution.

Enable saved external-service permission, analyze an image, select a specialist or all nine, and explicitly authorize the request. The dashboard displays individual failures and polls for up to two minutes. A manual check only retrieves existing runs. Complete output is read from result, outputs, or output. An immediate completed response is also displayed. Completed-without-output is reported explicitly.

This implementation was verified with mocked CREAO responses, not live keys. Verify each app's completed run with the credentials stored on your Windows machine or hosting provider. Acceptance alone is insufficient. Do not send private farm data or invent absent sensor readings, history, or visitor intent. Revoke the previously exposed key in the CREAO console; cloud code cannot verify account-side revocation.

## Scientific SQLite retrieval (no LLM)

- Ingest: `backend/RAG/ingest.py`.
- Search: `backend/RAG/retrieve.py`.
- Observation-to-query context: `backend/RAG/pipeline.py`.
- API: `/knowledge/status` and `/knowledge/search?query=leaf+yellowing`.
- User interface: `/research`.
- Database: the `rag_passages_fts` FTS5 table in the configured `SQLITE_DB_PATH`.

The bundled knowledge file is illustrative and excluded from scientific results. The environment could not fetch the attempted university source (HTTP 403), so no unverified source text was promoted into the index. To finish the corpus:

1. Read suitable UC IPM, USDA, university-extension, or peer-reviewed material in your browser.
2. Confirm the source, date, relevance, and permission to use short passages/paraphrases.
3. Add entries to `data/knowledge.json` with the existing schema (`title`, `source_url`, `public: true`, `passages`). Only set `public` after review. Do not add private farm records.
4. Run `.venv/bin/python scripts/prepare_data.py` (Windows uses `.venv\Scripts\python.exe`). The command loads the same `.env` database path as the API.
5. Open `/research`, confirm a positive usable-passage count, search representative crop questions, and verify every displayed link and passage. A citation link alone does not prove its contents or scientific accuracy.

## Accounts, plans, and deployment

Workspace keys require no name or email, but account IDs, credential hashes, settings, sessions, and audit records are stored. Sessions expire after 24 hours and can be revoked. Keep the private workspace key: there is no email recovery. Do not place it in your hackathon video.

Local users or the deployment administrator create workspaces. Public remote registration is disabled. An administrator can provision a remote workspace using their private `VIGILO_API_TOKEN`, then hand its workspace key privately to the pilot user. Never give the administrator token to customers. Use HTTPS in deployment, request limits at the ingress, trusted pilot accounts, and persistent database storage.

The `/plans` page describes the free research prototype and a planned pilot. There is no live paid checkout, subscription charge, or paid entitlement enforcement. A real subscription requires a billing-provider account, product/pricing decisions, server-side checkout and webhook verification, and provider-managed payment data. No fake purchase success is shown.
