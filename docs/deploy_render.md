# Deploy the entire VigiloForge app to Render

The root `render.yaml` now deploys one Docker web service: the public Next.js app proxies `/api` to FastAPI on loopback, and the supervisor also runs the genuine local Fetch receiver. Render supplies the HTTPS URL required for phone/webcam permissions. No separate Vercel project or API hostname is needed.

## Create the service

1. Push/select branch `feature/nine-agent-delivery` in `AHernandez33/Cal-Hacks` (the Blueprint explicitly selects it until this work is merged).
2. Sign in at https://dashboard.render.com and select **New → Blueprint**. Connect your GitHub account if needed and select **AHernandez33/Cal-Hacks**. In the Blueprint setup, select branch **feature/nine-agent-delivery** before reviewing the services. Use the root `render.yaml`; do not select `frontend/frontend-setup`.
3. Review the proposed service and disk, then deploy. The Blueprint uses a **paid Standard service and 1 GB persistent disk** because Python/PyTorch, Next.js, and Fetch run together. Review Render's displayed pricing before confirming. Free instances do not provide this persistent-disk workflow.
4. Wait for the Docker build and startup. A successful health check is `/api/health`. Open the service's generated **HTTPS URL**, such as `https://<your-service>.onrender.com`. The actual URL is assigned by Render; do not assume the example name is available.

If using **New → Web Service** instead of Blueprint: select the same repository/branch, Docker runtime, repository root, and `./Dockerfile`. Use the image's default command, a Standard-size service, health path `/api/health`, and a persistent disk mounted at `/var/data`. Add the environment values below yourself; automatic token/seed generation happens through the Blueprint.

## Secure environment settings

The Blueprint generates private `VIGILO_API_TOKEN` and `FETCH_AGENT_SEED` values and sets `SQLITE_DB_PATH=/var/data/vigiloforge.db`, `FETCH_MAILBOX=false`, `CREAO_API_VERSION=v1`, and `NEXT_PUBLIC_API_URL=/api`. Render supplies `PORT`. Leave the API and receiver private: only Next.js listens publicly on that port. The production supervisor refuses to start without an administrator token.

To connect all nine CREAO agents, add these pairs in the Render service's **Environment** settings using the authorized values already stored in your Windows `.env`:

| Role | App ID variable | API key variable |
| --- | --- | --- |
| Coordinator | `CREAO_COORDINATOR_APP_ID` | `CREAO_COORDINATOR_API_KEY` |
| Crop investigator | `CREAO_CROP_INVESTIGATOR_APP_ID` | `CREAO_CROP_INVESTIGATOR_API_KEY` |
| Leaf analyst | `CREAO_LEAF_ANALYST_APP_ID` | `CREAO_LEAF_ANALYST_API_KEY` |
| Reference retriever | `CREAO_REFERENCE_RETRIEVER_APP_ID` | `CREAO_REFERENCE_RETRIEVER_API_KEY` |
| Response advisor | `CREAO_RESPONSE_ADVISOR_APP_ID` | `CREAO_RESPONSE_ADVISOR_API_KEY` |
| Trend analyst | `CREAO_TREND_ANALYST_APP_ID` | `CREAO_TREND_ANALYST_API_KEY` |
| Privacy reviewer | `CREAO_PRIVACY_REVIEWER_APP_ID` | `CREAO_PRIVACY_REVIEWER_API_KEY` |
| Telemetry analyst | `CREAO_TELEMETRY_ANALYST_APP_ID` | `CREAO_TELEMETRY_ANALYST_API_KEY` |
| Visitor guide | `CREAO_VISITOR_GUIDE_APP_ID` | `CREAO_VISITOR_GUIDE_API_KEY` |

Save/redeploy after changing runtime credentials. Supply keys without the `Bearer` word. Backend keys must never use `NEXT_PUBLIC_` names or be committed to GitHub. The build context excludes `.env` files and local database files. Existing Windows `.env` files are not uploaded by a Git push; set hosted values separately.

Optional Tiger Data requires `TIGER_DATABASE_URL` and a verified read-only database connection. This is independent of the core app. No live sensor data, vetted scientific corpus, or hosted CREAO completion is implied by a successful deployment.

## First sign-in and camera use

1. Open your Render HTTPS app URL. Expand **Deployment administrator access (optional)** in Privacy controls. Privately enter the generated `VIGILO_API_TOKEN` from Render and press **Connect / refresh**. It is the setup password, not a customer login.
2. Open **Workspace / sign in** and **Create private workspace**. Save the new workspace key privately; the server retains a hash, not a recoverable copy. The app switches to the workspace session.
3. Sign in later with that workspace key. Pilot users must receive their own key privately from the administrator. No email verification is required. Public hosted scans retain the existing workspace access controls.
4. On the dashboard, allow camera permission, press **Start camera**, wait for **Camera ready**, then **Capture & analyze**. A captured photo appears with a download action before the API result. On Windows, also allow desktop-browser camera access in Windows privacy settings. Close Teams/Zoom if they hold the webcam. Phones must use the HTTPS Render URL; a laptop's localhost URL is not reachable from a phone.
5. Enable external agent services in Privacy controls and explicitly authorize a Fetch or CREAO investigation. Verify a genuine Fetch result and completed CREAO output. A configured indicator or HTTP 202 is not completion.

## Update the deployed app

Push tested changes to the Blueprint's selected branch. Render's normal Git autodeploy can rebuild them; otherwise select **Manual Deploy → Deploy latest commit**. After merging this delivery branch into main, change the service's deployment branch to main. Keep the disk and token/seed values stable across redeploys so workspace state and agent identity remain available.

## Local Docker check

If Docker Desktop is installed, from the repository root:

```powershell
docker build -t vigiloforge .
docker volume create vigiloforge-data
# Replace this placeholder privately; do not commit the real password.
docker run --rm --name vigiloforge -p 10000:10000 -v vigiloforge-data:/var/data -e VIGILO_API_TOKEN="YOUR_PRIVATE_ADMIN_PASSWORD" -e FETCH_AGENT_SEED="YOUR_PRIVATE_AGENT_SEED" vigiloforge
```

Open `http://localhost:10000` on that computer. These Docker commands run locally; they do not publish a Render deployment.
