"""Session access with a loopback demo and a separate deployment-admin token."""

import hmac
import os
from fastapi import HTTPException, Request
from backend.identity import workspace_id


async def require_access(request: Request):
    public = request.url.path in {"/health", "/auth/login", "/reports/verify/start", "/reports/verify/confirm"}
    identity = "local"
    supplied = request.headers.get("Authorization", "")
    bearer = supplied.removeprefix("Bearer ") if supplied.startswith("Bearer ") else ""
    admin = os.getenv("VIGILO_API_TOKEN", "").strip()
    is_admin = bool(admin) and hmac.compare_digest(bearer.encode(), admin.encode())
    if not public:
        if bearer.startswith("vfs_") and not is_admin:
            from backend.accounts import resolve_session

            identity = resolve_session(bearer)
            if not identity:
                raise HTTPException(
                    401, "Session expired or revoked. Sign in with your workspace key."
                )
            if request.url.path == "/auth/workspaces":
                raise HTTPException(
                    403,
                    "Only local setup or the deployment administrator can create workspaces.",
                )
        elif not is_admin:
            if admin:
                raise HTTPException(
                    401,
                    "Sign in with your private workspace key, or use the deployment administrator token for setup.",
                )
            if request.client is None or request.client.host not in {
                "127.0.0.1",
                "::1",
                "testclient",
            }:
                raise HTTPException(
                    403,
                    "Remote access requires a workspace session or deployment administrator token.",
                )
            if bearer:
                raise HTTPException(401, "Access token not recognized.")
    marker = workspace_id.set(identity)
    try:
        yield
    finally:
        workspace_id.reset(marker)
