
"""Fast api adapter for python 3.12 fetch ai client"""

import asyncio
import json
import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
fetch_python = project_root / ".venv-fetch" / "Scripts" / "python.exe"

async def request_fetch_evidence(
        features=None,
        anomaly_score=None, 
        crop_category=None,
):
    if not fetch_python.is_file():
        raise RuntimeError("Fetch.ai python 3.12 environment not found")

    payload = {
        "features": features,
        "anomaly_score": anomaly_score,
        "crop_category": crop_category,
    }

    env = os.environ.copy()

    process = await asyncio.create_subprocess_exec(
        str(fetch_python),
        "-m",
        "backend.fetch_client",
        cwd=str(project_root),
        env=env,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(json.dumps(payload).encode()),
            timeout=20,
        )

    except asyncio.TimeoutError:
        process.kill()
        await process.communicate()
        raise RuntimeError("fetch.ai request timed out")

    print(f"[FETCH EXIT CODE] {process.returncode}", flush=True)
    print(f"[FETCH STDOUT] {stdout.decode(errors='replace')[:1000]}", flush=True)
    print(f"[FETCH STDERR] {stderr.decode(errors='replace')[:1000]}", flush=True)

    if stderr:
        print(
        "[Fetch client stderr]",
        stderr.decode(errors="replace"),
        flush=True,
    )

    if process.returncode != 0:
        error = stderr.decode(errors="replace")
        print(f"[FETCH ERROR] {error}", flush=True)
        print(f"[FETCH EXIT CODE] {process.returncode}", flush=True)
        raise RuntimeError("Fetch.ai client failed; check backend logs")

    return json.loads(stdout.decode())

