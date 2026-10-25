# SQLite presistence for privacy preference and audit records
# no customer images, coordinates, crop observations, or model parameters
# database is created locally on first access

# run this on backend

from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
from backend.identity import workspace_id
from typing import Generator

project_root = Path(__file__).resolve().parent.parent


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def database_path() -> Path:
    """Use SQLite_db_path, otherwise data/vigiloforge.db"""
    configured = Path(os.getenv("SQLITE_DB_PATH", "data/vigiloforge.db")).expanduser()
    return configured if configured.is_absolute() else project_root / configured


@contextmanager
def connection() -> Generator[sqlite3.Connection, None, None]:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    database = sqlite3.connect(str(path), timeout=10)
    database.row_factory = sqlite3.Row
    database.execute("PRAGMA busy_timeout = 5000")
    try:
        yield database
        database.commit()
    except Exception:
        database.rollback()
        raise
    finally:
        database.close()


def init_db() -> None:
    """Create the local preference and audit tables on first access."""
    with connection() as database:
        database.execute("CREATE TABLE IF NOT EXISTS creao_run_roles (owner_id TEXT, run_id TEXT, role TEXT NOT NULL, PRIMARY KEY(owner_id, run_id))")
        database.execute(
            "CREATE TABLE IF NOT EXISTS workspace_preferences (owner_id TEXT PRIMARY KEY, settings TEXT NOT NULL, updated_at TEXT NOT NULL)"
        )
        database.execute(
            "CREATE TABLE IF NOT EXISTS workspace_creao_runs (owner_id TEXT NOT NULL, run_id TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY(owner_id, run_id))"
        )
        database.execute(
            "CREATE TABLE IF NOT EXISTS workspace_events (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id TEXT NOT NULL, created_at TEXT NOT NULL, event_type TEXT NOT NULL, decision TEXT NOT NULL, destination TEXT NOT NULL, reason TEXT NOT NULL, field_names_json TEXT NOT NULL)"
        )
        database.execute(
            """
            CREATE TABLE IF NOT EXISTS privacy_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                collaborative_training_enabled INTEGER NOT NULL
                    CHECK (collaborative_training_enabled IN (0, 1)),
                updated_at TEXT NOT NULL
            )
            """
        )
        database.execute(
            """
            CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                event_type TEXT NOT NULL,
                decision TEXT NOT NULL,
                destination TEXT NOT NULL,
                reason TEXT NOT NULL,
                field_names_json TEXT NOT NULL
            )
            """
        )
        database.execute(
            """
            INSERT OR IGNORE INTO privacy_settings
                (id, collaborative_training_enabled, updated_at)
            VALUES (1, 0, ?)
            """,
            (utc_now(),),
        )


def settings_as_dict(row: sqlite3.Row) -> dict:
    return {
        "collaborative_training_enabled": bool(row["collaborative_training_enabled"]),
        "updated_at": row["updated_at"],
    }


def get_privacy_settings() -> dict:
    if workspace_id.get() != "local":
        settings = get_workspace_preferences()
        return {
            "collaborative_training_enabled": settings[
                "collaborative_training_enabled"
            ],
            "updated_at": settings["updated_at"],
        }
    init_db()
    with connection() as database:
        row = database.execute(
            "SELECT collaborative_training_enabled, updated_at "
            "FROM privacy_settings WHERE id = 1"
        ).fetchone()
    if row is None:
        raise RuntimeError("Privacy settings row is missing.")
    return settings_as_dict(row)


def _record_event(
    connection: sqlite3.Connection,
    *,
    event_type: str,
    decision: str,
    destination: str,
    reason: str,
    field_names: list[str] | None = None,
) -> int:
    """Persist fixed event metadata and field NAMES only, never field values."""
    fields = sorted(set(field_names or []))
    # Field names are sanitized to avoid accidentally logging a payload value.
    safe_fields = [
        name[:64] if name.isidentifier() else "<unrecognized-field>"
        for name in fields[:30]
    ]
    if workspace_id.get() != "local":
        cursor = connection.execute(
            "INSERT INTO workspace_events (owner_id, created_at, event_type, decision, destination, reason, field_names_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                workspace_id.get(),
                utc_now(),
                event_type,
                decision,
                destination,
                reason,
                json.dumps(safe_fields),
            ),
        )
        return int(cursor.lastrowid)
    cursor = connection.execute(
        """
        INSERT INTO security_events
            (created_at, event_type, decision, destination, reason, field_names_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            utc_now(),
            event_type,
            decision,
            destination,
            reason,
            json.dumps(safe_fields),
        ),
    )
    return int(cursor.lastrowid)


def set_collaborative_training(enabled: bool) -> dict:
    """Persist one switch, independently of any external-service permission."""
    if not isinstance(enabled, bool):
        raise TypeError("enabled must be a boolean.")

    if workspace_id.get() != "local":
        result = save_workspace_preferences({"collaborative_training_enabled": enabled})
        return {
            "collaborative_training_enabled": enabled,
            "updated_at": result["updated_at"],
        }
    init_db()
    timestamp = utc_now()
    with connection() as database:
        database.execute(
            "UPDATE privacy_settings "
            "SET collaborative_training_enabled = ?, updated_at = ? "
            "WHERE id = 1",
            (int(enabled), timestamp),
        )
        _record_event(
            database,
            event_type="training_preference_changed",
            decision="allowed",
            destination="local",
            reason="training_enabled" if enabled else "training_disabled",
        )
    return {"collaborative_training_enabled": enabled, "updated_at": timestamp}


def record_security_event(
    *,
    event_type: str,
    decision: str,
    destination: str,
    reason: str,
    field_names: list[str] | None = None,
) -> int:
    """Write an audit record; callers must supply controlled, non-sensitive labels."""
    init_db()
    with connection() as database:
        return _record_event(
            database,
            event_type=event_type,
            decision=decision,
            destination=destination,
            reason=reason,
            field_names=field_names,
        )


def list_security_events(limit: int = 25) -> list[dict]:
    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValueError("limit must be an integer.")
    limit = max(1, min(limit, 100))

    if workspace_id.get() != "local":
        init_db()
        with connection() as db:
            rows = db.execute(
                "SELECT * FROM workspace_events WHERE owner_id=? ORDER BY id DESC LIMIT ?",
                (workspace_id.get(), limit),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "created_at": row["created_at"],
                "event_type": row["event_type"],
                "decision": row["decision"],
                "destination": row["destination"],
                "reason": row["reason"],
                "field_names": json.loads(row["field_names_json"]),
            }
            for row in rows
        ]
    init_db()
    with connection() as database:
        rows = database.execute(
            """
            SELECT id, created_at, event_type, decision,
                   destination, reason, field_names_json
            FROM security_events
            ORDER BY id DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [
        {
            "id": row["id"],
            "created_at": row["created_at"],
            "event_type": row["event_type"],
            "decision": row["decision"],
            "destination": row["destination"],
            "reason": row["reason"],
            "field_names": json.loads(row["field_names_json"]),
        }
        for row in rows
    ]


DEFAULT_PREFERENCES = {
    "external_services_enabled": False,
    "observation_sync_enabled": False,
    "local_retention_enabled": True,
}


def get_preferences() -> dict:
    if workspace_id.get() != "local":
        values = get_workspace_preferences()
        return {key: values[key] for key in DEFAULT_PREFERENCES}
    init_db()
    with connection() as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS app_preferences (id INTEGER PRIMARY KEY CHECK (id=1), settings TEXT NOT NULL)"
        )
        row = db.execute("SELECT settings FROM app_preferences WHERE id=1").fetchone()
    return {**DEFAULT_PREFERENCES, **(json.loads(row["settings"]) if row else {})}


def set_preferences(values: dict) -> dict:
    if not set(values).issubset(DEFAULT_PREFERENCES) or any(
        type(v) is not bool for v in values.values()
    ):
        raise ValueError("Unknown or invalid privacy preference")
    if workspace_id.get() != "local":
        return save_workspace_preferences(values)
    get_preferences()
    with connection() as db:
        row = db.execute("SELECT settings FROM app_preferences WHERE id=1").fetchone()
        updated = {
            **DEFAULT_PREFERENCES,
            **(json.loads(row["settings"]) if row else {}),
            **values,
        }
        db.execute(
            "INSERT INTO app_preferences VALUES (1, ?) ON CONFLICT(id) DO UPDATE SET settings=excluded.settings",
            (json.dumps(updated),),
        )
    return updated


def remember_creao_run(run_id: str) -> None:
    if workspace_id.get() != "local":
        init_db()
        with connection() as db:
            db.execute(
                "INSERT OR IGNORE INTO workspace_creao_runs VALUES (?, ?, ?)",
                (workspace_id.get(), run_id, utc_now()),
            )
        return
    with connection() as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS creao_runs (run_id TEXT PRIMARY KEY, created_at TEXT NOT NULL)"
        )
        db.execute(
            "INSERT OR IGNORE INTO creao_runs VALUES (?, ?)", (run_id, utc_now())
        )


def has_creao_run(run_id: str) -> bool:
    if workspace_id.get() != "local":
        init_db()
        with connection() as db:
            return (
                db.execute(
                    "SELECT 1 FROM workspace_creao_runs WHERE owner_id=? AND run_id=?",
                    (workspace_id.get(), run_id),
                ).fetchone()
                is not None
            )
    with connection() as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS creao_runs (run_id TEXT PRIMARY KEY, created_at TEXT NOT NULL)"
        )
        return (
            db.execute("SELECT 1 FROM creao_runs WHERE run_id=?", (run_id,)).fetchone()
            is not None
        )


def get_workspace_preferences():
    init_db()
    with connection() as db:
        row = db.execute(
            "SELECT settings, updated_at FROM workspace_preferences WHERE owner_id=?",
            (workspace_id.get(),),
        ).fetchone()
    return {
        **DEFAULT_PREFERENCES,
        "collaborative_training_enabled": False,
        **(json.loads(row["settings"]) if row else {}),
        "updated_at": row["updated_at"] if row else utc_now(),
    }


def save_workspace_preferences(values):
    init_db()
    with connection() as db:
        row = db.execute(
            "SELECT settings FROM workspace_preferences WHERE owner_id=?",
            (workspace_id.get(),),
        ).fetchone()
        settings = {
            **DEFAULT_PREFERENCES,
            "collaborative_training_enabled": False,
            **(json.loads(row["settings"]) if row else {}),
            **values,
        }
        timestamp = utc_now()
        db.execute(
            "INSERT INTO workspace_preferences VALUES (?, ?, ?) ON CONFLICT(owner_id) DO UPDATE SET settings=excluded.settings, updated_at=excluded.updated_at",
            (workspace_id.get(), json.dumps(settings), timestamp),
        )
    return {**settings, "updated_at": timestamp}


def remember_creao_role(run_id: str, role: str) -> None:
    with connection() as db:
        db.execute("CREATE TABLE IF NOT EXISTS creao_run_roles (owner_id TEXT, run_id TEXT, role TEXT NOT NULL, PRIMARY KEY(owner_id, run_id))")
        db.execute("INSERT OR IGNORE INTO creao_run_roles VALUES (?, ?, ?)", (workspace_id.get(), run_id, role))


def creao_run_role(run_id: str) -> str:
    with connection() as db:
        db.execute("CREATE TABLE IF NOT EXISTS creao_run_roles (owner_id TEXT, run_id TEXT, role TEXT NOT NULL, PRIMARY KEY(owner_id, run_id))")
        row = db.execute("SELECT role FROM creao_run_roles WHERE owner_id=? AND run_id=?", (workspace_id.get(), run_id)).fetchone()
    return row["role"] if row else "coordinator"
