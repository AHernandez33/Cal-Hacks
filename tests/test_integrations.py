"""Real local receiver connectivity and honest corpus/integration state."""

import asyncio
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.integrations import fetch_endpoint, fetch_status
from backend.RAG.ingest import ingest_documents


class Receiver(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(405)
        self.end_headers()

    def log_message(self, *args):
        pass


class IntegrationTests(unittest.TestCase):
    def test_probe_distinguishes_connectivity_from_message_success(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Receiver)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch.dict(
                os.environ,
                {
                    "FETCH_AGENT_ENDPOINT": f"http://127.0.0.1:{server.server_port}/submit",
                    "FETCH_PYTHON": "",
                },
            ):
                status = asyncio.run(fetch_status())
                self.assertTrue(status["ready"])
                self.assertFalse(status["messaging_verified"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_missing_interpreter_has_actionable_status(self):
        with patch.dict(os.environ, {"FETCH_PYTHON": "/nonexistent/vigilo-python"}):
            status = asyncio.run(fetch_status())
            self.assertFalse(status["ready"])
            self.assertEqual(status["code"], "interpreter_missing")

    def test_remote_plain_http_is_not_allowed(self):
        with patch.dict(
            os.environ, {"FETCH_AGENT_ENDPOINT": "http://example.com/submit"}
        ):
            with self.assertRaises(ValueError):
                fetch_endpoint()

    def test_credentials_in_fetch_url_are_rejected(self):
        with patch.dict(
            os.environ,
            {"FETCH_AGENT_ENDPOINT": "https://user:password@example.com/submit"},
        ):
            with self.assertRaises(ValueError):
                fetch_endpoint()

    def test_library_status_does_not_count_placeholder(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(
                os.environ,
                {
                    "SQLITE_DB_PATH": str(Path(directory) / "test.db"),
                    "VIGILO_API_TOKEN": "",
                },
            ):
                ingest_documents()
                with TestClient(app) as client:
                    result = client.get("/knowledge/status").json()
                    self.assertTrue(result["indexed"])
                    self.assertEqual(result["passages"], 0)
                    self.assertEqual(result["sources"], [])
                    self.assertFalse(result["llm_used"])


if __name__ == "__main__":
    unittest.main()
