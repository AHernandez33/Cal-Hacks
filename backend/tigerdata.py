"""Read Tiger Cloud greenhouse telemetry without exposing private customer records.

The public dashboard currently displays only explicitly synthetic demo records.
Private production telemetry requires user-scoped ownership authorization.
"""

import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class TelemetryUnavailable(RuntimeError):
    """A cloud telemetry connection or query could not be completed."""


def _dsn() -> str:
    return (
        os.getenv("TIMESCALE_SERVICE_URL", "").strip()
        or os.getenv("TIGER_DATABASE_URL", "").strip()
    )


def history(limit: int = 24) -> dict:
    """Read *only synthetic* Tiger Cloud records for the fixed demo client.

    The endpoint currently has no client-level telemetry authorization.
    Never remove the synthetic/client filters to expose arbitrary real records.
    """
    dsn = _dsn()
    if not dsn:
        raise TelemetryUnavailable(
            "Tiger Cloud not configured. Set TIMESCALE_SERVICE_URL (or TIGER_DATABASE_URL)."
        )
    try:
        import psycopg
        from psycopg.rows import dict_row

        safe_limit = max(1, min(int(limit), 200))
        with psycopg.connect(dsn, connect_timeout=10, row_factory=dict_row) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SET TRANSACTION READ ONLY")
                cursor.execute("SET LOCAL statement_timeout = '5000ms'")
                cursor.execute(
                    """
                    SELECT time AS timestamp, soil_moisture, temperature_c,
                           humidity_pct, leaf_anomaly_score, demo_client_id,
                           is_synthetic
                    FROM greenhouse_telemetry
                    WHERE demo_client_id = %s AND is_synthetic IS TRUE
                    ORDER BY time DESC LIMIT %s
                    """,
                    ("greenhouse_01", safe_limit),
                )
                rows = cursor.fetchall()
    except Exception as exc:
        raise TelemetryUnavailable(
            "Tiger Cloud query failed. Verify environment configuration, network, and table schema."
        ) from exc

    measurements = []
    for row in reversed(rows):
        timestamp = row["timestamp"]
        if isinstance(timestamp, datetime):
            timestamp = timestamp.astimezone(timezone.utc).isoformat()
        measurements.append(
            {
                "timestamp": timestamp,
                "soil_moisture": row["soil_moisture"],
                "temperature_c": row["temperature_c"],
                "humidity_pct": row["humidity_pct"],
                "leaf_anomaly_score": row["leaf_anomaly_score"],
                "demo_client_id": row["demo_client_id"],
                "is_synthetic": True,
            }
        )

    return {
        "source": "Tiger Cloud — synthetic greenhouse_01 records",
        "synthetic": True,
        "measurements": measurements,
        "units": {
            "soil_moisture": "fraction",
            "temperature_c": "°C",
            "humidity_pct": "%",
            "leaf_anomaly_score": "score",
        },
    }
