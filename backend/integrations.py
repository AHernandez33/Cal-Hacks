"""Bounded, local connection diagnostics. No credentials are returned."""

import asyncio
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit
import httpx


def fetch_endpoint():
    endpoint = os.getenv("FETCH_AGENT_ENDPOINT", "http://127.0.0.1:8001/submit").strip()
    parsed = urlsplit(endpoint)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise ValueError(
            "FETCH_AGENT_ENDPOINT must be an HTTP(S) URL without credentials."
        )
    if parsed.scheme == "http" and parsed.hostname not in {
        "127.0.0.1",
        "localhost",
        "::1",
    }:
        raise ValueError("Remote Fetch endpoints must use HTTPS.")
    return endpoint


async def fetch_status():
    executable = os.getenv("FETCH_PYTHON") or sys.executable
    if not Path(executable).is_file():
        return {
            "ready": False,
            "code": "interpreter_missing",
            "message": "FETCH_PYTHON does not point to a Python executable. Leave it blank to use the backend environment.",
        }
    # Check the selected interpreter, not just the API's interpreter.
    try:
        process = await asyncio.create_subprocess_exec(
            executable,
            "-c",
            "import importlib.util,json; print(json.dumps({'installed':importlib.util.find_spec('uagents') is not None}))",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except OSError:
        return {
            "ready": False,
            "code": "interpreter_unusable",
            "message": "The selected Fetch Python executable could not start. Clear FETCH_PYTHON to use the backend environment.",
        }
    try:
        stdout, _ = await asyncio.wait_for(process.communicate(), 5)
        installed = process.returncode == 0 and json.loads(stdout).get("installed")
    except (ValueError, asyncio.TimeoutError):
        if process.returncode is None:
            process.kill()
        await process.communicate()
        installed = False
    if not installed:
        return {
            "ready": False,
            "code": "sdk_missing",
            "message": "Install requirements.txt in the Python environment used by the backend and Fetch receiver.",
        }
    try:
        endpoint = fetch_endpoint()
        async with httpx.AsyncClient(
            timeout=2,
            trust_env=urlsplit(endpoint).hostname
            not in {"127.0.0.1", "localhost", "::1"},
        ) as client:
            # HEAD reaches the configured receiver, without sending observations.
            result = await client.head(endpoint)
        reachable = result.status_code in {200, 204, 400, 405}
    except (httpx.RequestError, ValueError):
        reachable = False
    return {
        "ready": reachable,
        "code": "receiver_reachable" if reachable else "receiver_unavailable",
        "message": "Receiver endpoint responds. Send a consented investigation to verify agent address and messaging."
        if reachable
        else "Start scripts/run_fetch.py from the SAME project as the backend. Wait for 'Fetch agent started'. Check port 8001 and matching FETCH_AGENT_SEED settings.",
        "messaging_verified": False,
    }


async def integration_status():
    return {
        "fetch": await fetch_status(),
        "creao": {
            "configured": bool(
                os.getenv("creao_api_key") and os.getenv("creao_app_id")
            ),
            "verified": False,
            "message": "Hosted LLM integration is outside this update; configured does not mean tested.",
        },
        "tiger_data": {
            "configured": bool(os.getenv("TIGER_DATABASE_URL")),
            "verified": False,
            "message": "Use Load database history to verify a real read-only database query.",
        },
    }
