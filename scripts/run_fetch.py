"""Run the local receiver with the same .env used by Uvicorn."""

from pathlib import Path
import sys
from dotenv import load_dotenv

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
load_dotenv(root / ".env")


if __name__ == "__main__":
    import socket
    with socket.socket() as probe:
        probe.settimeout(0.3)
        occupied = probe.connect_ex(("127.0.0.1", 8001)) == 0
    if occupied:
        raise SystemExit("Fetch port 8001 is already occupied. Keep the existing receiver, or stop it before starting a replacement. No second agent was started.")
    from backend.fetch_agent import create_agent
    create_agent().run()
