# VigiloForge — Secured Crop Detector

**Smarter Farming. Private by Design.** A Cal Hacks 13.0 research prototype for investigating visible leaf changes—not a validated disease diagnosis.

## What the app includes

- **Camera and photo upload:** capture, preview, download, and analyze leaf photos with OpenCV observations and a discoloration overlay.
- **Nine CREAO specialists:** run all nine or select one; view separate answers, errors, and automatic status updates. Reports display readable text rather than JSON or echoed prompts.
- **Fetch.ai messaging:** genuine local uAgents request/response, supervised alongside the API. No Fetch API key is needed for the bundled direct-message demo.
- **Six greenhouse scenarios:** interactive, clearly labeled synthetic examples and a browser-only comparison calculator.
- **Research and learning:** SQLite FTS5 reference search and a PyTorch federated-learning demonstration with three simulated clients.
- **Private workspaces and Field Mode:** workspace keys, separate sharing preferences, browser photo storage, and explicit synchronization.
- **Launch experience:** original logo, entrance animation, responsive pages, and reduced-motion support.

Free, Gold, and Platinum cards describe subscription proposals. No paid checkout, active paid entitlements, or email scan gate is enabled. The dashboard telemetry panel has been removed.

## Deploy the entire app on Render

The repository includes a **Dockerfile** and **Render Blueprint** for one web service:

| Capability | Configuration |
| --- | --- |
| Public website | Next.js on Render's generated HTTPS URL |
| API | FastAPI reached through the website's `/api` routes |
| Agent messaging | Local Fetch receiver supervised with the API and frontend |
| Persistent state | SQLite on a 1 GB disk mounted at `/var/data` |
| Startup and shutdown | One supervisor starts and stops all three processes |
| Health check | `/api/health` |
| Private setup | Generated administrator token and Fetch identity seed |

1. In [Render Dashboard](https://dashboard.render.com), choose **New → Blueprint**.
2. Connect **AHernandez33/Cal-Hacks** and select **`feature/nine-agent-delivery`**.
3. Use the root **`render.yaml`**, review the resources, and deploy.
4. Open the generated HTTPS URL after the service becomes live.

The Blueprint selects a **paid Standard service and 1 GB persistent disk**. Review Render's displayed pricing. The initial image build includes PyTorch and may take more than ten minutes. Do not enter a pip command as the Start Command; Docker supplies startup for the entire app.

### Credentials and first sign-in

Add your authorized `CREAO_<ROLE>_APP_ID` and `CREAO_<ROLE>_API_KEY` pairs in Render's **Environment** settings, then redeploy. Your local `.env` is not transferred through GitHub. Never put backend secrets in `NEXT_PUBLIC_*` variables.

On the website, expand **Deployment administrator access**, enter the generated `VIGILO_API_TOKEN` privately, and connect. Open **Workspace / sign in → Create private workspace**, save its key privately, and use that key for future sign-ins. The administrator provisions separate keys for pilot users.

For agent answers: analyze a photo, select CREAO, enable **Allow external agent services for this workspace**, authorize the request, and run all nine. Hosted camera access requires HTTPS and browser permission.

See the [complete Render guide](docs/deploy_render.md) for all credential names, manual service setup, and deployment checks. The container was tested locally; a live Render deployment must be verified in your own account.

## Run locally on Windows

Requires **Python 3.12, Node.js 22+, and npm**. In VS Code PowerShell:

```powershell
cd "C:\Users\herna\Cal Hacks\SCD\VigiloForge-CLEAN"
# First setup, or when dependencies need updating:
powershell -ExecutionPolicy Bypass -File .\scripts\start_windows.ps1 -Install
```

For subsequent starts:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_windows.ps1
```

The launcher preserves existing `.env` files and opens the browser after readiness. **Keep its terminal running**; Ctrl+C stops the app. Frontend: port **3000**. API: **8000**. Fetch receiver: **8001**. Stop old app servers before starting another stack.

For a Windows `EPERM` lock on Next.js, close the project's old Node processes or restart Windows, then use `start_windows.ps1 -RepairFrontend`. This repairs frontend dependencies without reinstalling Python packages. Native Windows execution still needs validation on your computer.

## Run locally on Linux / cloud

Use the existing checkout; cloud tasks are already isolated. Do not create a Git worktree unless explicitly requested.

```bash
bash scripts/setup.sh
cp -n .env.example .env
cp -n frontend/.env.example frontend/.env.local
.venv/bin/python scripts/prepare_data.py
.venv/bin/python scripts/run_stack.py
```

## Important limits

- Image measurements and scores are heuristics, not disease probabilities. Agent answers must preserve uncertainty.
- External agents receive approved numerical observations, broad crop category, and public reference passages—not raw photos or GPS. Saved workspace permission and request consent are both required.
- The reviewed research corpus is not sufficiently populated for scientific evidence claims. Placeholder sources are excluded.
- Six greenhouse scenarios and three federated clients are synthetic examples, not connected farms. The federated demo provides neither secure aggregation nor differential privacy.
- Browser photo storage is not encrypted or a durable backup. Backend analysis and agents need a network connection; offline Field Mode can retain permitted local photos and queues.
- Subscription billing, live Tiger Data, physical camera/phone behavior, and live CREAO completion require separate verification. Cloud CREAO tests used mocked provider responses.

## Validation and details

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

Avoid unrestricted test discovery: `test_fetch_message.py` is a continuous demonstration. See [validation results](docs/validation.md), [agent setup](docs/final_agents.md), and [integration details](docs/integrations_setup.md).
