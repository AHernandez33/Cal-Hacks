"""Exercise real session issuance, revocation, ownership and privacy isolation."""

import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
from backend import databases
from backend.accounts import digest
from backend.identity import workspace_id


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.environment = patch.dict(
            os.environ,
            {
                "SQLITE_DB_PATH": str(Path(self.directory.name) / "db.sqlite"),
                "VIGILO_API_TOKEN": "",
            },
        )
        self.environment.start()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.environment.stop()
        self.directory.cleanup()

    def create(self):
        result = self.client.post("/auth/workspaces")
        self.assertEqual(result.status_code, 201, result.text)
        return result.json()

    def headers(self, session):
        return {"Authorization": f"Bearer {session['token']}"}

    def test_create_requires_no_personal_profile_and_stores_only_hashes(self):
        session = self.create()
        self.assertTrue(session["workspace_key"].startswith("vfw_"))
        with databases.connection() as db:
            account = db.execute("SELECT * FROM workspaces").fetchone()
            saved = db.execute("SELECT * FROM workspace_sessions").fetchone()
        self.assertEqual(account["key_hash"], digest(session["workspace_key"]))
        self.assertNotIn(session["workspace_key"], str(dict(account)))
        self.assertEqual(saved["token_hash"], digest(session["token"]))
        self.assertEqual(set(account.keys()), {"id", "key_hash", "created_at"})

    def test_sign_in_and_logout_revokes_only_that_session(self):
        account = self.create()
        result = self.client.post(
            "/auth/login", json={"workspace_key": account["workspace_key"]}
        )
        self.assertEqual(result.status_code, 200, result.text)
        session = result.json()
        self.assertNotEqual(session["token"], account["token"])
        self.assertEqual(
            self.client.get("/auth/me", headers=self.headers(session)).json()[
                "workspace_id"
            ],
            account["workspace_id"],
        )
        self.client.post(
            "/auth/logout", headers=self.headers(session)
        ).raise_for_status()
        self.assertEqual(
            self.client.get(
                "/privacy/settings", headers=self.headers(session)
            ).status_code,
            401,
        )
        self.assertEqual(
            self.client.get(
                "/privacy/settings", headers=self.headers(account)
            ).status_code,
            200,
        )

    def test_unknown_key_rejected(self):
        self.assertEqual(
            self.client.post(
                "/auth/login", json={"workspace_key": "vfw_" + "x" * 43}
            ).status_code,
            401,
        )

    def test_preferences_separated_between_accounts_and_local_demo(self):
        first, second = self.create(), self.create()
        self.client.put(
            "/privacy/settings",
            headers=self.headers(first),
            json={
                "external_services_enabled": True,
                "collaborative_training_enabled": True,
            },
        ).raise_for_status()
        own = self.client.get("/privacy/settings", headers=self.headers(first)).json()
        other = self.client.get(
            "/privacy/settings", headers=self.headers(second)
        ).json()
        local = self.client.get("/privacy/settings").json()
        self.assertTrue(own["external_services_enabled"])
        self.assertTrue(own["collaborative_training_enabled"])
        self.assertFalse(other["external_services_enabled"])
        self.assertFalse(other["collaborative_training_enabled"])
        self.assertFalse(local["external_services_enabled"])

    def test_settings_cannot_leak_from_local_context(self):
        first = self.create()
        self.client.put(
            "/privacy/settings", json={"external_services_enabled": True}
        ).raise_for_status()
        self.assertFalse(
            self.client.get("/privacy/settings", headers=self.headers(first)).json()[
                "external_services_enabled"
            ]
        )
        self.assertEqual(workspace_id.get(), "local")

    def test_run_and_audit_ownership(self):
        first, second = self.create(), self.create()
        marker = workspace_id.set(first["workspace_id"])
        try:
            databases.remember_creao_run("run-private-001")
            databases.record_security_event(
                event_type="external_data_request",
                decision="blocked",
                destination="fetch",
                reason="test_only",
            )
        finally:
            workspace_id.reset(marker)
        self.assertEqual(
            self.client.get(
                "/agents/creao/run-private-001", headers=self.headers(first)
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(
                "/agents/creao/run-private-001", headers=self.headers(second)
            ).status_code,
            404,
        )
        self.assertEqual(
            len(
                self.client.get("/security/events", headers=self.headers(first)).json()[
                    "events"
                ]
            ),
            1,
        )
        self.assertEqual(
            self.client.get("/security/events", headers=self.headers(second)).json()[
                "events"
            ],
            [],
        )
        self.assertEqual(self.client.get("/security/events").json()["events"], [])

    def test_expiration(self):
        account = self.create()
        with databases.connection() as db:
            db.execute(
                "UPDATE workspace_sessions SET expires_at=?", (int(time.time()) - 1,)
            )
        self.assertEqual(
            self.client.get("/auth/me", headers=self.headers(account)).status_code, 401
        )

    def test_workspace_deletion_revokes_key_and_cleans_owned_records(self):
        account = self.create()
        self.client.put(
            "/privacy/settings",
            headers=self.headers(account),
            json={"external_services_enabled": True},
        ).raise_for_status()
        self.assertEqual(
            self.client.delete(
                "/auth/workspace", headers=self.headers(account)
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get("/auth/me", headers=self.headers(account)).status_code, 401
        )
        self.assertEqual(
            self.client.post(
                "/auth/login", json={"workspace_key": account["workspace_key"]}
            ).status_code,
            401,
        )
        with databases.connection() as db:
            self.assertEqual(
                db.execute("SELECT count(*) FROM workspace_preferences").fetchone()[0],
                0,
            )

    def test_remote_signup_is_admin_only_but_existing_key_can_log_in(self):
        account = self.create()
        with TestClient(app, client=("203.0.113.2", 1000)) as remote:
            self.assertEqual(remote.post("/auth/workspaces").status_code, 403)
            result = remote.post(
                "/auth/login", json={"workspace_key": account["workspace_key"]}
            )
            self.assertEqual(result.status_code, 200)
            self.assertEqual(
                remote.get(
                    "/privacy/settings", headers=self.headers(result.json())
                ).status_code,
                200,
            )
        with patch.dict(os.environ, {"VIGILO_API_TOKEN": "admin-test-only"}):
            with TestClient(app, client=("203.0.113.2", 1000)) as remote:
                self.assertEqual(
                    remote.post(
                        "/auth/workspaces",
                        headers={"Authorization": "Bearer admin-test-only"},
                    ).status_code,
                    201,
                )

    def test_current_users_cannot_create_another_workspace(self):
        account = self.create()
        self.assertEqual(
            self.client.post(
                "/auth/workspaces", headers=self.headers(account)
            ).status_code,
            403,
        )

    def test_plan_is_honest_free_status(self):
        result = self.client.get("/billing/status").json()
        self.assertEqual(result["plan"], "free")
        self.assertFalse(result["billing_enabled"])
        self.assertFalse(result["payment_collected"])

    def test_auth_responses_not_cached(self):
        self.assertEqual(
            self.client.get("/auth/me").headers["cache-control"], "no-store"
        )


if __name__ == "__main__":
    unittest.main()
