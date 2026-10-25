"""Initialize the RAG index using the same configuration as the running API."""

from pathlib import Path
import sys
from dotenv import load_dotenv

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
load_dotenv(root / ".env")
from backend.RAG.ingest import main

if __name__ == "__main__":
    main()
