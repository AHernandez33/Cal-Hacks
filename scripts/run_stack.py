"""One terminal for the API, local Fetch receiver, and Next.js development server."""

from pathlib import Path
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from dotenv import load_dotenv

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
                        env=os.environ.copy(),
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
        while True:
            for name, child in children:
                if child.poll() is not None:
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
