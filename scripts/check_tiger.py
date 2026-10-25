"""Read-only verification; prints only a record count or a sanitized failure."""

from pathlib import Path
import sys
from dotenv import load_dotenv

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
load_dotenv(root / ".env")
from backend.tigerdata import history, TelemetryUnavailable

if __name__ == "__main__":
    try:
        result = history(1)
        print(
            f"Tiger Data query succeeded. Records returned: {len(result['measurements'])} (0 means connected but empty)."
        )
    except TelemetryUnavailable as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
