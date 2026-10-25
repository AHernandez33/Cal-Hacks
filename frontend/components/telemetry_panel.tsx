"use client";
import { useState } from "react";
import { requestJSON } from "../lib/api";
type Measurement = {
  timestamp: string;
  soil_moisture: number | null;
  temperature_c: number | null;
  humidity_pct: number | null;
  leaf_anomaly_score?: number | null;
};
type History = {
  source: string;
  synthetic: boolean;
  measurements: Measurement[];
};
const metrics = [
  { key: "soil_moisture", label: "Soil moisture", scale: 100, unit: "%" },
  { key: "temperature_c", label: "Temperature", scale: 1, unit: "°C" },
  { key: "humidity_pct", label: "Humidity", scale: 1, unit: "%" },
  { key: "leaf_anomaly_score", label: "Leaf anomaly", scale: 1, unit: "" },
] as const;

function Trend({ rows, field }: { rows: Measurement[]; field: typeof metrics[number] }) {
  const points = rows.map((row, index) => {
    const raw = row[field.key];
    return typeof raw === "number" && Number.isFinite(raw)
      ? { index, value: raw * field.scale } : null;
  }).filter((x): x is { index: number; value: number } => x !== null);
  if (!points.length) return <p className="muted">No measurements available for this chart.</p>;
  const low = Math.min(...points.map((x) => x.value));
  const high = Math.max(...points.map((x) => x.value));
  const coords = points.map(({ index, value }) =>
    `${15 + (index / Math.max(rows.length - 1, 1)) * 670},${170 - ((value - low) / (high - low || 1)) * 145}`
  ).join(" ");
  return (
    <div>
      <p className="muted">{field.label}: {low.toFixed(2)}–{high.toFixed(2)} {field.unit}</p>
      <svg viewBox="0 0 700 190" role="img"
        aria-label={`${field.label} trend for ${points.length} observations`}
        style={{ width: "100%", maxHeight: 240 }}>
        <line x1="15" y1="170" x2="685" y2="170" stroke="#507563" />
        <polyline points={coords} fill="none" stroke="#00ddb8"
          strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
}
export default function TelemetryPanel() {
  const [data, setData] = useState<History | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState<typeof metrics[number]["key"]>("soil_moisture");
  async function load(source: "live" | "demo") {
    setBusy(true); setError(""); setData(null);
    try {
      setData(await requestJSON<History>(`/telemetry/history?source=${source}`));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally { setBusy(false); }
  }
  const metric = metrics.find((m) => m.key === selected) ?? metrics[0];
  return (
    <section className="panel">
      <p className="eyebrow">Environment history</p>
      <h2>Greenhouse telemetry</h2>
      <p className="muted">
        Tiger Cloud currently displays only labeled synthetic greenhouse_01
        observations. Private production data requires per-customer authorization.
      </p>
      <div className="actions">
        <button disabled={busy} onClick={() => void load("live")}>
          {busy ? "Loading..." : "Load Tiger Cloud records"}
        </button>
        <button disabled={busy} className="secondary" onClick={() => void load("demo")}>
          View local synthetic demo
        </button>
      </div>
      {error && <p role="alert" className="error">{error}</p>}
      {data && (
        <>
          <p><strong>{data.synthetic ? "SYNTHETIC DATA — " : ""}</strong>{data.source}</p>
          {data.measurements.length === 0 ? <p>No historical records found.</p> : (
            <>
              <div className="actions">
                <label htmlFor="telemetry-metric">Chart metric</label>
                <select id="telemetry-metric" value={selected}
                  onChange={(e) => setSelected(e.target.value as typeof selected)}>
                  {metrics.map((m) => <option key={m.key} value={m.key}>{m.label}</option>)}
                </select>
              </div>
              <Trend rows={data.measurements} field={metric} />
            </>
          )}
          <div className="table-scroll">
            <table>
              <thead><tr>
                <th>Time</th><th>Soil moisture</th><th>°C</th><th>Humidity</th><th>Leaf anomaly</th>
              </tr></thead>
              <tbody>{data.measurements.map((row, index) => (
                <tr key={`${row.timestamp}-${index}`}>
                  <td>{new Date(row.timestamp).toLocaleString()}</td>
                  <td>{row.soil_moisture == null ? "—" : `${(row.soil_moisture * 100).toFixed(1)}%`}</td>
                  <td>{row.temperature_c ?? "—"}</td>
                  <td>{row.humidity_pct == null ? "—" : `${row.humidity_pct}%`}</td>
                  <td>{row.leaf_anomaly_score ?? "—"}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}
