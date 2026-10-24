"""Run the local receiver with the same .env used by Uvicorn."""

from pathlib import Path
import sys
from dotenv import load_dotenv

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
load_dotenv(root / ".env")
from backend.fetch_agent import create_agent  # noqa: E402

if __name__ == "__main__":
    create_agent().run()
