"""Read-only historical telemetry. Never falls back to synthetic data silently."""

import os


class TelemetryUnavailable(RuntimeError):
    pass


def history(limit: int = 24) -> dict:
    dsn = os.getenv("TIGER_DATABASE_URL", "").strip()
    if not dsn:
        raise TelemetryUnavailable(
            "Tiger Data is not configured. Set TIGER_DATABASE_URL on the backend."
        )
    try:
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(
            dsn, connect_timeout=5, sslmode="verify-full", row_factory=dict_row
        ) as conn:
            with conn.transaction():
                conn.execute("SET TRANSACTION READ ONLY")
                conn.execute("SET LOCAL statement_timeout = '5000ms'")
                rows = conn.execute(
                    "SELECT timestamp, soil_moisture, temperature_c, humidity_pct FROM greenhouse_telemetry ORDER BY timestamp DESC LIMIT %s",
                    (max(1, min(limit, 200)),),
                ).fetchall()
    except Exception as exc:
        raise TelemetryUnavailable(
            "Tiger Data query failed. Verify TLS trust, credentials, connectivity, and the documented schema."
        ) from exc
    return {
        "source": "Tiger Data historical records",
        "synthetic": False,
        "measurements": list(reversed(rows)),
        "units": {
            "soil_moisture": "fraction",
            "temperature_c": "°C",
            "humidity_pct": "%",
        },
    }
