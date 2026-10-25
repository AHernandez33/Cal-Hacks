"use client";
import Link from "next/link";
import { useState } from "react";
import {
  requestJSON,
  fetchInvestigation,
  type VisionResponse,
} from "../lib/api";
type Report = {
  provider: string;
  status: string;
  run_id?: string;
  summary?: string;
  uncertainty?: string;
  next_observations?: string[];
  minimum_intervention?: string[];
  possible_explanations?: string[];
  citations?: { title: string; url: string; excerpt: string }[];
  stages?: { id: string; name: string; execution: string; status: string }[];
  result?: unknown;
};
export default function AgentPanel({
  vision,
}: {
  vision: VisionResponse | null;
}) {
  const [crop, setCrop] = useState("Tomato");
  const [provider, setProvider] = useState("local");
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [report, setReport] = useState<Report | null>(null);
  const ready = !!vision?.features;
  const external = provider !== "local";
  async function investigate() {
    if (!vision) return;
    setBusy(true);
    setError("");
    setReport(null);
    try {
      const result =
        provider === "fetch"
          ? await fetchInvestigation(
              vision.features,
              vision.anomaly_score,
              crop,
              consent,
            )
          : await requestJSON<Report>("/agents/analyze", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                features: vision.features,
                anomaly_score: vision.anomaly_score,
                crop_category: crop,
                provider,
                authorize_external: external && consent,
              }),
            });
      setReport(result as Report);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }
  async function poll() {
    if (!report?.run_id) return;
    setBusy(true);
    setError("");
    try {
      const result = await requestJSON<Report>(
        `/agents/creao/${encodeURIComponent(report.run_id)}`,
      );
      setReport({ ...report, ...result });
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel">
      <p className="eyebrow">Evidence workflow</p>
      <h2>Investigate with context</h2>
      <p>
        <Link href="/research">Explore the SQLite research library →</Link>
      </p>
      <p className="muted">
        Local mode uses rules and SQLite retrieval. External providers receive
        only five numbers, the anomaly score, crop category, and approved public
        passages.
      </p>
      <label className="field">
        Crop category
        <input
          value={crop}
          maxLength={40}
          onChange={(e) => setCrop(e.target.value)}
        />
      </label>
      <label className="field">
        Provider
        <select
          aria-label="Provider"
          value={provider}
          onChange={(e) => {
            setProvider(e.target.value);
            setConsent(false);
          }}
        >
          <option value="local">Local evidence workflow</option>
          <option value="fetch">Fetch.ai agent messaging</option>
          <option value="creao">Configured CREAO hosted agent</option>
        </select>
      </label>
      {external && (
        <label className="consent">
          <input
            type="checkbox"
            checked={consent}
            onChange={(e) => setConsent(e.target.checked)}
          />
          I authorize this request to the selected agent service. Saved
          external-service permission must also be enabled.
        </label>
      )}
      <button
        disabled={!ready || busy || (external && !consent)}
        onClick={() => void investigate()}
      >
        {busy ? "Working…" : "Request investigation"}
      </button>
      {!ready && <p className="muted">Analyze a leaf image first.</p>}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {report && (
        <div aria-live="polite">
          <p>
            <strong>{report.provider}</strong> · {report.status}
          </p>
          {report.summary && <p>{report.summary}</p>}
          {report.stages && (
            <ol>
              {report.stages.map((s) => (
                <li key={s.id}>
                  {s.name}: {s.status}{" "}
                  <span className="muted">({s.execution})</span>
                </li>
              ))}
            </ol>
          )}
          {report.citations && (
            <>
              <h3>Public evidence</h3>
              {report.citations.length === 0 ? (
                <p>
                  No vetted matching references are available. Add reviewed
                  public passages before relying on scientific evidence.
                </p>
              ) : (
                report.citations.map((c, i) => (
                  <article key={i}>
                    <a href={c.url} target="_blank" rel="noreferrer">
                      {c.title}
                    </a>
                    <p>{c.excerpt}</p>
                  </article>
                ))
              )}
            </>
          )}
          {report.possible_explanations?.map((x) => (
            <p key={x}>{x}</p>
          ))}
          {report.next_observations && (
            <>
              <h3>Next observations</h3>
              <ul>
                {report.next_observations.map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
            </>
          )}
          {report.minimum_intervention && (
            <>
              <h3>Minimum intervention</h3>
              <ul>
                {report.minimum_intervention.map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
            </>
          )}
          {report.uncertainty && <p className="muted">{report.uncertainty}</p>}
          {report.run_id && (
            <button
              className="secondary"
              disabled={busy}
              onClick={() => void poll()}
            >
              Check hosted run status
            </button>
          )}
          {report.result != null && (
            <pre className="code-result">
              {JSON.stringify(report.result, null, 2)}
            </pre>
          )}
        </div>
      )}
    </section>
  );
}
