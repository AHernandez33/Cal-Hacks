"""Cross-platform, privacy-checked adapter for the local Fetch.ai client."""

import asyncio
import json
import os
import sys
from pathlib import Path
from backend.RAG.pipeline import build_context
from backend.integrations import fetch_status
from backend.privacy import authorize_external_payload

project_root = Path(__file__).resolve().parent.parent


async def request_fetch_evidence(
    features=None,
    anomaly_score=None,
    crop_category=None,
    *,
    explicit_authorization=False,
):
    context = build_context(
        features=features, anomaly_score=anomaly_score, crop_category=crop_category
    )
    payload = authorize_external_payload(
        provider="fetch",
        payload=context["agent_payload"],
        explicit_authorization=explicit_authorization,
    )
    readiness = await fetch_status()
    if not readiness["ready"]:
        raise RuntimeError(readiness["message"])
    # Recheck after the asynchronous readiness probe, immediately before sending.
    payload = authorize_external_payload(
        provider="fetch",
        payload=context["agent_payload"],
        explicit_authorization=explicit_authorization,
    )
    executable = os.getenv("FETCH_PYTHON") or sys.executable
    process = await asyncio.create_subprocess_exec(
        executable,
        "-m",
        "backend.fetch_client",
        cwd=str(project_root),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, _ = await asyncio.wait_for(
            process.communicate(json.dumps(payload).encode()), timeout=20
        )
    except (asyncio.TimeoutError, asyncio.CancelledError):
        if process.returncode is None:
            process.kill()
        await process.communicate()
        raise
    if process.returncode:
        raise RuntimeError(
            "Fetch messaging failed. Confirm the receiver has finished startup, both processes load the same .env, and fetch_agent_address matches the receiver. See /integrations/status."
        )
    try:
        result = json.loads(stdout)
    except (ValueError, UnicodeError) as exc:
        raise RuntimeError("Fetch client returned invalid JSON") from exc
    if not isinstance(result, dict):
        raise RuntimeError("Fetch client returned an unexpected response")
    return result
