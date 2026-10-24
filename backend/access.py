"""Single-grower prototype access. Not a multi-tenant identity system."""

import hmac
import os
from fastapi import HTTPException, Request


def require_access(request: Request):
    if request.url.path == "/health":
        return
    token = os.getenv("VIGILO_API_TOKEN", "").strip()
    if token:
        supplied = request.headers.get("Authorization", "")
        if not hmac.compare_digest(supplied.encode(), f"Bearer {token}".encode()):
            raise HTTPException(
                401, "Enter the deployment access token in Privacy settings."
            )
    elif request.client is None or request.client.host not in {
        "127.0.0.1",
        "::1",
        "testclient",
    }:
        raise HTTPException(
            403, "Remote access requires VIGILO_API_TOKEN on the backend."
        )
