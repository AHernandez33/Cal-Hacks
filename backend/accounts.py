"""Pseudonymous workspace keys and revocable 24-hour bearer sessions.

No names or email addresses. Identifiers and credential hashes are still stored;
this is data minimization, not a claim of zero personal-data processing.
"""

import hashlib
import secrets
import time
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from backend import databases
from backend.identity import workspace_id

router = APIRouter(prefix="/auth", tags=["private workspaces"])


def init_accounts():
    with databases.connection() as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS workspaces (id TEXT PRIMARY KEY, key_hash TEXT UNIQUE NOT NULL, created_at TEXT NOT NULL)"
        )
        db.execute(
            "CREATE TABLE IF NOT EXISTS workspace_sessions (token_hash TEXT PRIMARY KEY, workspace_id TEXT NOT NULL, expires_at INTEGER NOT NULL)"
        )


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def issue_session(owner):
    token = "vfs_" + secrets.token_urlsafe(32)
    with databases.connection() as db:
        db.execute(
            "DELETE FROM workspace_sessions WHERE expires_at < ?", (int(time.time()),)
        )
        db.execute(
            "INSERT INTO workspace_sessions VALUES (?, ?, ?)",
            (digest(token), owner, int(time.time()) + 86400),
        )
    return {"token": token, "workspace_id": owner, "expires_in": 86400}


def resolve_session(token):
    init_accounts()
    with databases.connection() as db:
        row = db.execute(
            "SELECT s.workspace_id FROM workspace_sessions s JOIN workspaces w ON w.id=s.workspace_id WHERE s.token_hash=? AND s.expires_at>?",
            (digest(token), int(time.time())),
        ).fetchone()
    return row["workspace_id"] if row else None


@router.post("/workspaces", status_code=201)
def create_workspace():
    # Access dependency permits only local users or the deployment administrator.
    init_accounts()
    owner = secrets.token_hex(16)
    key = "vfw_" + secrets.token_urlsafe(32)
    with databases.connection() as db:
        db.execute(
            "INSERT INTO workspaces VALUES (?, ?, ?)",
            (owner, digest(key), databases.utc_now()),
        )
    return {
        **issue_session(owner),
        "workspace_key": key,
        "notice": "Save this key privately. No email recovery is available. It is shown only once.",
    }


class Login(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workspace_key: str = Field(min_length=20, max_length=150)


@router.post("/login")
def login(request: Login):
    init_accounts()
    with databases.connection() as db:
        row = db.execute(
            "SELECT id FROM workspaces WHERE key_hash=?",
            (digest(request.workspace_key),),
        ).fetchone()
    if not row:
        raise HTTPException(401, "Workspace key not recognized.")
    return issue_session(row["id"])


@router.get("/me")
def me():
    return {
        "workspace_id": workspace_id.get(),
        "mode": "workspace" if workspace_id.get() != "local" else "local demo",
        "plan": "free",
        "billing_enabled": False,
    }


@router.post("/logout")
def logout(request: Request):
    init_accounts()
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    with databases.connection() as db:
        db.execute(
            "DELETE FROM workspace_sessions WHERE token_hash=?", (digest(token),)
        )
    return {"signed_out": True}


@router.delete("/workspace")
def delete_workspace():
    owner = workspace_id.get()
    if owner == "local":
        raise HTTPException(400, "Sign in to a private workspace first.")
    init_accounts()
    databases.init_db()
    with databases.connection() as db:
        db.execute("DELETE FROM workspace_sessions WHERE workspace_id=?", (owner,))
        db.execute("DELETE FROM workspaces WHERE id=?", (owner,))
        for table in (
            "workspace_preferences",
            "workspace_creao_runs",
            "workspace_events",
        ):
            db.execute(f"DELETE FROM {table} WHERE owner_id=?", (owner,))
    return {
        "deleted": True,
        "notice": "Active workspace records removed. Browser photos and provider-held data require separate deletion.",
    }
