#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -z "${VIGILO_API_TOKEN:-}" ]; then
  echo "Set VIGILO_API_TOKEN securely in Render before starting the public app." >&2
  exit 1
fi
python scripts/prepare_data.py
exec python scripts/run_stack.py --production
