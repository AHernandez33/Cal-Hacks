"use client";
import { useState } from "react";
import { requestJSON } from "../lib/api";
type History = {
  source: string;
  synthetic: boolean;
  measurements: {
    timestamp: string;
    soil_moisture: number;
    temperature_c: number;
    humidity_pct: number;
  }[];
};
export default function TelemetryPanel() {
  const [data, setData] = useState<History | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function load(source: string) {
    setBusy(true);
    setError("");
    setData(null);
    try {
      setData(
        await requestJSON<History>(`/telemetry/history?source=${source}`),
      );
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel">
      <p className="eyebrow">Environment history</p>
      <h2>Greenhouse telemetry</h2>
      <p className="muted">
        Live history requires a configured Tiger Data database. Workspaces share
        this installation’s telemetry feed; use non-private demonstration
        readings. Synthetic data is requested separately.
      </p>
      <div className="actions">
        <button disabled={busy} onClick={() => void load("live")}>
          Load database history
        </button>
        <button
          disabled={busy}
          className="secondary"
          onClick={() => void load("demo")}
        >
          View synthetic demo
        </button>
      </div>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {data && (
        <>
          <p>
            {data.synthetic ? "SYNTHETIC DEMONSTRATION — " : ""}
            {data.source}
          </p>
          {data.measurements.length === 0 && (
            <p>No historical records found.</p>
          )}
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Soil moisture</th>
                  <th>°C</th>
                  <th>Humidity</th>
                </tr>
              </thead>
              <tbody>
                {data.measurements.map((row) => (
                  <tr key={row.timestamp}>
                    <td>{new Date(row.timestamp).toLocaleString()}</td>
                    <td>{(row.soil_moisture * 100).toFixed(1)}%</td>
                    <td>{row.temperature_c}</td>
                    <td>{row.humidity_pct}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}
