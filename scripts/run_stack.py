"""One terminal for the API, local Fetch receiver, and Next.js development server."""

from pathlib import Path
import os
import argparse
import shutil
import signal
import socket
import subprocess
import sys
import time
import httpx
from dotenv import load_dotenv

root = Path(__file__).resolve().parent.parent
load_dotenv(root / ".env")


def port_in_use(port):
    with socket.socket() as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend-only", action="store_true", help="Supervise API and local Fetch receiver without Node/Next.js (for hosting).")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535 or args.port == 8001 or (not args.backend_only and args.port == 3000):
        parser.error("API port must be valid and distinct from the receiver/frontend ports.")
    for port in ((args.port, 8001) if args.backend_only else (args.port, 8001, 3000)):
        if port_in_use(port):
            raise SystemExit(
                f"Port {port} is already in use. Stop the old API/agent/frontend with Ctrl+C, then retry. This script will not stop another application."
            )
    if not args.backend_only and not shutil.which("npm"):
        raise SystemExit("Install Node.js 22 or newer, then reopen the terminal.")
    if not args.backend_only and not (root / "frontend/node_modules/next/dist/bin/next").is_file():
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
                args.host,
                "--port",
                str(args.port),
            ],
            root,
        ),
        ("Fetch receiver", [sys.executable, "scripts/run_fetch.py"], root),
    ]
    if not args.backend_only:
        commands.append(("Frontend", frontend, root / "frontend"))
    children = []
    def stop_stack(signum, frame):
        raise KeyboardInterrupt
    previous_term = signal.signal(signal.SIGTERM, stop_stack)
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
        print("Starting " + ", ".join(name for name, _, _ in commands) + "; waiting for readiness…", flush=True)
        pending = {
            "API": (f"http://127.0.0.1:{args.port}/health", "GET", {200}),
            "Fetch receiver": ("http://127.0.0.1:8001/submit", "HEAD", {200, 204, 400, 405}),
        }
        if not args.backend_only:
            pending["Frontend"] = ("http://127.0.0.1:3000/", "GET", {200})
        deadline = time.monotonic() + 60
        with httpx.Client(timeout=2, trust_env=False) as client:
            while pending:
                for name, child in children:
                    if child.poll() is not None:
                        raise RuntimeError(f"{name} stopped with exit code {child.returncode}. Read its error above.")
                for name, (url, method, accepted) in list(pending.items()):
                    try:
                        response = client.request(method, url)
                        if response.status_code in accepted:
                            if name == "API" and response.json().get("status") != "ok":
                                continue
                            del pending[name]
                    except (httpx.RequestError, ValueError):
                        pass
                if pending:
                    if time.monotonic() >= deadline:
                        raise RuntimeError("Startup timed out waiting for: " + ", ".join(pending) + ". Read the service errors above.")
                    time.sleep(0.5)
        print("Backend and Fetch receiver are ready." if args.backend_only else "VigiloForge is ready at http://127.0.0.1:3000 — keep this terminal open.", flush=True)
        print("Local scans need no email verification. For hosted agents, enable external services and authorize the request.", flush=True)
        print("Receiver readiness does not prove messaging; run scripts/check_fetch.py for a genuine local exchange. Ctrl+C stops this stack.", flush=True)
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
        signal.signal(signal.SIGTERM, previous_term)
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
