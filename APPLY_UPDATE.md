# Apply this update

This archive contains only updated and new files, with paths relative to the project root. It does not include dependency folders, virtual environments, credentials, original logo artwork, or your database.

1. Make a backup or Git checkpoint of your current project.
2. Extract the ZIP into the folder containing `backend/` and `frontend/` (for your fresh upload, normally `C:\Users\herna\VigiloForge-clean`). Allow replacement of the listed updated files; keep your other files.
3. Read `docs/updated_files.md` for the complete file list and `docs/validation.md` for verified and outstanding work.
4. Install the updated dependencies and configure local settings using `README.md`. Keep existing `.env` values; do not overwrite them with `.env.example`.
5. Start the backend, optional Fetch receiver, and frontend using the documented commands.
6. Add your real banner at `frontend/public/vigiloforge-logo.png`.

Windows dependency refresh, from the project root, assuming a Python 3.12 `.venv` already exists:

```powershell
.\.venv\Scripts\python.exe -m pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:SQLITE_DB_PATH = ".local/vigiloforge.db"
.\.venv\Scripts\python.exe -m backend.RAG.ingest
cd frontend
npm ci
cd ..
```

If no environment exists, follow the full installation section of `README.md` first. When receiving this update through GitHub, use `git pull --ff-only` in your existing checkout instead of extracting the archive. Review local changes before pulling; do not discard them to resolve a conflict.
