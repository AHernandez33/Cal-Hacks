"use client";
import { useState } from "react";
import { requestJSON } from "../lib/api";

type Metrics = { validation_loss: number; accuracy: number; precision: number; recall: number; f1: number };
type Round = Metrics & { round: number; training_loss: number };
type DemoResult = {
  dataset: string; simulation: string; participating_clients: string[]; excluded_clients: string[];
  history: Round[]; federated_final: Round; local_only_baseline: Metrics; privacy: string;
};
const CLIENTS = ["greenhouse_a", "greenhouse_b", "greenhouse_c"] as const;
const percent = (n: number) => `${(n * 100).toFixed(2)}%`;
export default function FederatedPanel() {
  const [consent, setConsent] = useState<Record<string, boolean>>({});
  const [result, setResult] = useState<DemoResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function runDemo() {
    setBusy(true); setError(""); setResult(null);
    try {
      const data = await requestJSON<DemoResult>("/federated/demo", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ consent, rounds: 10, local_epochs: 2 }),
      });
      setResult(data);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Request failed"); }
    finally { setBusy(false); }
  }
  return <section className="panel">
    <h2>Federated learning</h2>
    <p className="muted">Synthetic, single-computer demo. Each client must opt in separately for this run; these controls do not alter persistent privacy settings.</p>
    <div className="checklist">{CLIENTS.map(name => <label key={name}><input type="checkbox" checked={consent[name] === true}
      onChange={e => setConsent(before => ({ ...before, [name]: e.target.checked }))}/> {name.replaceAll("_", " ")}</label>)}</div>
    <button type="button" onClick={runDemo} disabled={busy || !CLIENTS.some(name => consent[name])}>{busy ? "Training…" : "Run 10 federated rounds"}</button>
    {error && <p role="alert" className="error">{error}</p>}
    {result && <div>
      <p><strong>{result.dataset}</strong> — {result.simulation}</p>
      <p>Participating: {result.participating_clients.join(", ") || "None"}</p>
      <p>Excluded: {result.excluded_clients.join(", ") || "None"}</p>
      <div className="table-scroll"><table><thead><tr><th>Model</th><th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1</th><th>Val loss</th></tr></thead><tbody>
        {[{ name: "Federated", m: result.federated_final }, { name: "Local only", m: result.local_only_baseline }].map(({name,m}) =>
        <tr key={name}><td>{name}</td><td>{percent(m.accuracy)}</td><td>{percent(m.precision)}</td><td>{percent(m.recall)}</td><td>{percent(m.f1)}</td><td>{m.validation_loss.toFixed(4)}</td></tr>)}</tbody></table></div>
      <h3>Training history</h3><ol className="history">{result.history.map(r => <li key={r.round}>Round {r.round}: training {r.training_loss.toFixed(4)} · validation {r.validation_loss.toFixed(4)} · F1 {percent(r.f1)}</li>)}</ol>
      <p className="muted">{result.privacy}</p>
    </div>}
  </section>;
}
