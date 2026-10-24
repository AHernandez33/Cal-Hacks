#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export UV_CACHE_DIR="${UV_CACHE_DIR:-/workspace/.cache/uv}"
export npm_config_cache="${npm_config_cache:-/workspace/.cache/npm}"
if command -v uv >/dev/null 2>&1; then
  if [ ! -x .venv/bin/python ]; then uv venv .venv --python python3.12; fi
  uv pip install --python .venv/bin/python --torch-backend cpu -r requirements.txt
else
  if [ ! -x .venv/bin/python ]; then python3.12 -m venv .venv; fi
  .venv/bin/python -m pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu
  .venv/bin/python -m pip install -r requirements.txt
fi
export SQLITE_DB_PATH="${SQLITE_DB_PATH:-.local/vigiloforge.db}"
.venv/bin/python -m backend.RAG.ingest
(cd frontend && npm ci --no-audit --no-fund)
