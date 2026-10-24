"""Isolated API checks; no external credentials or farm data required."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import cv2
import numpy as np
from fastapi.testclient import TestClient
from backend.main import app
from backend.RAG.ingest import ingest_documents
from backend import databases

FEATURES = {
    "yellow_fraction": 0.2,
    "brown_fraction": 0.1,
    "mean_hue": 40,
    "texture_variance": 0.01,
    "edge_density": 0.1,
}


class APITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.environment = patch.dict(
            os.environ,
            {
                "SQLITE_DB_PATH": str(Path(self.temp.name) / "test.db"),
                "VIGILO_API_TOKEN": "",
            },
        )
        self.environment.start()
        ingest_documents()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.environment.stop()
        self.temp.cleanup()

    def image(self):
        image = np.zeros((160, 160, 3), dtype=np.uint8)
        cv2.ellipse(image, (80, 80), (45, 60), 0, 0, 360, (40, 170, 40), -1)
        return cv2.imencode(".png", image)[1].tobytes()

    def test_health(self):
        self.assertEqual(self.client.get("/health").json()["status"], "ok")

    def test_vision_to_local_report(self):
        response = self.client.post(
            "/vision/analyze", files={"file": ("leaf.png", self.image(), "image/png")}
        )
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(set(result["features"]), set(FEATURES))
        report = self.client.post(
            "/agents/analyze",
            json={
                "features": result["features"],
                "anomaly_score": result["anomaly_score"],
            },
        )
        self.assertEqual(report.status_code, 200, report.text)
        self.assertEqual(len(report.json()["stages"]), 4)
        self.assertFalse(report.json()["external_request_sent"])

    def test_placeholder_is_not_citation(self):
        result = self.client.get(
            "/knowledge/search", params={"query": "leaf irrigation"}
        ).json()
        self.assertEqual(result["count"], 0)

    def test_invalid_image(self):
        self.assertEqual(
            self.client.post(
                "/vision/analyze",
                files={"file": ("bad.png", b"not an image", "image/png")},
            ).status_code,
            422,
        )

    def test_wrong_mime(self):
        self.assertEqual(
            self.client.post(
                "/vision/analyze", files={"file": ("bad.txt", b"text", "text/plain")}
            ).status_code,
            415,
        )

    def test_external_requires_saved_permission(self):
        response = self.client.post(
            "/agents/fetch", json={"features": FEATURES, "authorize_external": True}
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "external_services_disabled")

    def test_external_requires_per_request_permission(self):
        self.client.put("/privacy/settings", json={"external_services_enabled": True})
        response = self.client.post("/agents/fetch", json={"features": FEATURES})
        self.assertEqual(response.status_code, 403)

    def test_private_fields_blocked(self):
        from backend.privacy import authorize_external_payload, PrivacyViolation

        self.client.put("/privacy/settings", json={"external_services_enabled": True})
        with self.assertRaises(PrivacyViolation):
            authorize_external_payload(
                provider="fetch",
                payload={
                    "task": "investigate_visible_discoloration",
                    "features": FEATURES,
                    "raw_image": "secret",
                },
                explicit_authorization=True,
            )

    def test_preferences_persist(self):
        self.client.put(
            "/privacy/settings",
            json={
                "external_services_enabled": True,
                "collaborative_training_enabled": True,
            },
        )
        settings = self.client.get("/privacy/settings").json()
        self.assertTrue(settings["external_services_enabled"])
        self.assertTrue(settings["collaborative_training_enabled"])
        self.assertFalse(settings["observation_sync_enabled"])

    def test_sync_denied_by_default(self):
        response = self.client.post(
            "/observations/sync?authorize_sync=true",
            files={"file": ("leaf.png", self.image(), "image/png")},
        )
        self.assertEqual(response.status_code, 403)

    def test_sync_needs_both_permissions(self):
        self.client.put("/privacy/settings", json={"observation_sync_enabled": True})
        files = lambda: {"file": ("leaf.png", self.image(), "image/png")}
        self.assertEqual(
            self.client.post("/observations/sync", files=files()).status_code, 403
        )
        result = self.client.post(
            "/observations/sync?authorize_sync=true", files=files()
        )
        self.assertEqual(result.status_code, 200, result.text)
        self.assertFalse(result.json()["stored_on_server"])

    def test_hosted_access_token(self):
        with patch.dict(os.environ, {"VIGILO_API_TOKEN": "test-only-token"}):
            self.assertEqual(self.client.get("/health").status_code, 200)
            self.assertEqual(self.client.get("/privacy/settings").status_code, 401)
            self.assertEqual(
                self.client.get(
                    "/privacy/settings",
                    headers={"Authorization": "Bearer test-only-token"},
                ).status_code,
                200,
            )

    def test_remote_access_denied_without_token(self):
        with TestClient(app, client=("203.0.113.1", 1234)) as client:
            self.assertEqual(client.get("/privacy/settings").status_code, 403)

    def test_creao_missing_config_and_unknown_run(self):
        self.client.put("/privacy/settings", json={"external_services_enabled": True})
        with patch.dict(os.environ, {"creao_api_key": "", "creao_app_id": ""}):
            result = self.client.post(
                "/agents/analyze",
                json={
                    "features": FEATURES,
                    "provider": "creao",
                    "authorize_external": True,
                },
            )
            self.assertEqual(result.status_code, 503, result.text)
        self.assertEqual(self.client.get("/agents/creao/unknown-run").status_code, 404)

    def test_telemetry_no_silent_fallback(self):
        with patch.dict(os.environ, {"TIGER_DATABASE_URL": ""}):
            self.assertEqual(self.client.get("/telemetry/history").status_code, 503)
        self.assertTrue(
            self.client.get("/telemetry/history?source=demo").json()["synthetic"]
        )

    def test_federated_api(self):
        response = self.client.post(
            "/federated/demo",
            json={
                "consent": {
                    "greenhouse_a": True,
                    "greenhouse_b": True,
                    "greenhouse_c": True,
                },
                "rounds": 10,
                "local_epochs": 2,
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(response.json()["history"]), 10)

    def test_cors_preflight(self):
        response = self.client.options(
            "/privacy/settings",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization",
            },
        )
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
