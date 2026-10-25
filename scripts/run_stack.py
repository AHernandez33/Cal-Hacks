"""One terminal for the API, local Fetch receiver, and Next.js development server."""

from pathlib import Path
import os
import shutil
import signal
import secrets
import socket
import subprocess
import sys
import time
from dotenv import load_dotenv, set_key

root = Path(__file__).resolve().parent.parent
load_dotenv(root / ".env")


def port_in_use(port):
    with socket.socket() as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def main():
    for port in (8000, 8001, 3000):
        if port_in_use(port):
            raise SystemExit(
                f"Port {port} is already in use. Stop the old API/agent/frontend with Ctrl+C, then retry. This script will not stop another application."
            )
    if not shutil.which("npm"):
        raise SystemExit("Install Node.js 22 or newer, then reopen the terminal.")
    if not (root / "frontend/node_modules/next").exists():
        raise SystemExit(
            "Frontend dependencies are missing. Run npm ci in frontend first."
        )
    frontend = (
        ["cmd.exe", "/d", "/s", "/c", "npm run dev -- --hostname 127.0.0.1"]
        if os.name == "nt"
        else ["npm", "run", "dev", "--", "--hostname", "127.0.0.1"]
    )
    if not os.getenv("VIGILO_REPORT_SECRET", "").strip():
        secret = secrets.token_urlsafe(48)
        set_key(str(root / ".env"), "VIGILO_REPORT_SECRET", secret)
        os.environ["VIGILO_REPORT_SECRET"] = secret
        print("Created a private report secret in .env; existing secrets are preserved.", flush=True)
    child_env = os.environ.copy()
    # This launcher always serves the local API, regardless of a deployment URL in .env.local.
    child_env["NEXT_PUBLIC_API_URL"] = "http://127.0.0.1:8000"
    origins = [v.strip() for v in child_env.get("FRONTEND_ORIGIN", "").split(",") if v.strip()]
    child_env["FRONTEND_ORIGIN"] = ",".join(dict.fromkeys(origins + ["http://127.0.0.1:3000", "http://localhost:3000"]))
    commands = [
        (
            "API",
            [
                sys.executable,
                "-m",
                "uvicorn",
                "backend.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
            ],
            root,
        ),
        ("Fetch receiver", [sys.executable, "scripts/run_fetch.py"], root),
        ("Frontend", frontend, root / "frontend"),
    ]
    children = []
    try:
        for name, command, directory in commands:
            children.append(
                (
                    name,
                    subprocess.Popen(
                        command,
                        cwd=directory,
                        env=child_env,
                        start_new_session=os.name != "nt",
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                        if os.name == "nt"
                        else 0,
                    ),
                )
            )
        print(
            "\nVigiloForge starts at http://127.0.0.1:3000 — keep this terminal open.",
            flush=True,
        )
        print(
            "Use /login for private workspaces, /federated for learning models, /research for SQLite retrieval, and /field for mobile observations.",
            flush=True,
        )
        print(
            "Fetch may need time to finish SDK startup. Use Check integration status on the dashboard; then send a consented request. Ctrl+C stops this stack.",
            flush=True,
        )
        reported = set()
        while True:
            for name, child in children:
                if child.poll() is not None:
                    if name == "Fetch receiver":
                        if name not in reported:
                            print("Fetch receiver stopped. The API and website remain available; use local investigations and check integration status before retrying Fetch.", flush=True)
                            reported.add(name)
                        continue
                    raise RuntimeError(
                        f"{name} stopped with exit code {child.returncode}. Read its error above."
                    )
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Stopping this stack…", flush=True)
    finally:
        for _, child in reversed(children):
            if child.poll() is None:
                if os.name == "nt":
                    subprocess.run(
                        ["taskkill", "/PID", str(child.pid), "/T", "/F"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
            if os.name != "nt":
                try:
                    os.killpg(child.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
        for _, child in children:
            try:
                child.wait(timeout=8)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == "__main__":
    main()
