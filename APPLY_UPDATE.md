# Apply the update from GitHub

1. Open the fresh checkout containing `backend/`, `frontend/`, and `requirements.txt` in VS Code. Your old `Cal Hacks/SCD/1` folder is a separate copy.
2. Preserve any local edits, then run `git pull --ff-only origin main`. Stop on an error; do not reset or force-pull over your work.
3. In PowerShell at that checkout's root run:

   ```powershell
   powershell -ExecutionPolicy RemoteSigned -File .\scripts\start_windows.ps1 -Install
   ```

4. The script creates/uses a Python 3.12 `.venv`, preserves existing configuration files, installs dependencies, prepares retrieval data, and starts all three services.
5. Keep the terminal open. Stop old servers first if ports 3000, 8000, or 8001 are already occupied. Ctrl+C stops this stack.
6. Open the dashboard at port 3000. Use `/login`, `/federated`, `/research`, `/field`, and `/plans` for the new pages.

For later starts omit `-Install` unless dependencies changed. Do not replace `.env` values with `.env.example`. Read `README.md` and `docs/integrations_setup.md` for Tiger Data, Fetch.ai, CREAO, scientific sources, and deployment requirements.

If applying an archive instead, back up the project and extract into the same project root. Archives omit dependencies, virtual environments, credentials, and databases. Do not mix the old and new checkouts when starting services.
