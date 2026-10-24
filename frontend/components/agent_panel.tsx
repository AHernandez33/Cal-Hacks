"use client";
import { useState } from "react";
import { fetchInvestigation, type LeafFeatures, type VisionResponse } from "../lib/api";

const KEYS = ["yellow_fraction", "brown_fraction", "mean_hue", "texture_variance", "edge_density"] as const;
type Props = { vision: VisionResponse | null };
export default function AgentPanel({ vision }: Props) {
  const [crop, setCrop] = useState("Tomato");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [response, setResponse] = useState<Record<string, unknown> | null>(null);
  const features = Object.fromEntries(KEYS.map(key => [key, vision?.[key]]));
  const ready = KEYS.every(key => typeof vision?.[key] === "number" && Number.isFinite(vision[key]));
  async function investigate() {
    if(!vision || !ready) return;
    setBusy(true); setError(""); setResponse(null);
    try {
      const data = await fetchInvestigation(features as LeafFeatures, typeof vision.anomaly_score === "number" ? vision.anomaly_score : 0, crop);
      setResponse(data);
    } catch(e) { setError(e instanceof Error ? e.message : "Investigation failed"); }
    finally { setBusy(false); }
  }
  return <section className="panel"><h2>Fetch.ai evidence investigation</h2>
    <p className="muted">Analyze an image first. Only the five numeric observations, anomaly score, and crop category are sent through this endpoint; no raw image is sent by this panel.</p>
    <label className="field">Crop category <input value={crop} onChange={e=>setCrop(e.target.value)} maxLength={60} /></label>
    <button type="button" disabled={!ready || busy} onClick={investigate}>{busy ? "Investigating…" : "Request Fetch.ai evidence"}</button>
    {!ready && <p className="muted">Waiting for five numeric leaf features from OpenCV.</p>}
    {error && <p role="alert" className="error">{error}</p>}
    {response && <pre className="code-result">{JSON.stringify(response,null,2)}</pre>}
    <p className="muted">CREAO is intentionally not invoked until its API authentication and privacy policy checks are verified.</p>
  </section>;
}
