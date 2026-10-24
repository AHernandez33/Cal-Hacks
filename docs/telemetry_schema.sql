-- Run as the database owner, then give the application's DB role SELECT only.
CREATE TABLE IF NOT EXISTS greenhouse_telemetry (
    timestamp TIMESTAMPTZ PRIMARY KEY,
    soil_moisture DOUBLE PRECISION NOT NULL CHECK (soil_moisture BETWEEN 0 AND 1),
    temperature_c DOUBLE PRECISION NOT NULL,
    humidity_pct DOUBLE PRECISION NOT NULL CHECK (humidity_pct BETWEEN 0 AND 100)
);
-- Populate with actual observations. Never label generated samples as live readings.
