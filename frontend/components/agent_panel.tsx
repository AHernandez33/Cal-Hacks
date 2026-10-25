"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import {
  requestJSON,
  fetchInvestigation,
  type VisionResponse,
} from "../lib/api";
const roles = ["coordinator", "crop_investigator", "leaf_analyst", "reference_retriever", "response_advisor", "trend_analyst", "privacy_reviewer", "telemetry_analyst", "visitor_guide"] as const;
type HostedRun = { role: string; status: string; run_id?: string; result?: unknown; error?: string; notice?: string };
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
  const [role, setRole] = useState("coordinator");
  const [runs, setRuns] = useState<HostedRun[]>([]);
  const [pollUntil, setPollUntil] = useState(0);
  async function checkRuns() {
    await Promise.all(runs.filter(r => r.run_id && !["completed", "failed", "cancelled"].includes(r.status)).map(async r => {
      try {
        const update = await requestJSON<HostedRun>(`/agents/creao/${encodeURIComponent(r.run_id!)}`);
        setRuns(previous => previous.map(item => item.run_id === r.run_id ? {...item, ...update, error: update.error} : item));
      } catch (e) {
        setRuns(previous => previous.map(item => item.run_id === r.run_id ? {...item, error: String(e)} : item));
      }
    }));
  }
  useEffect(() => {
    if (!pollUntil || Date.now() >= pollUntil || !runs.some(r => r.run_id && !["completed", "failed", "cancelled"].includes(r.status))) return;
    let cancelled = false;
    const timer = setTimeout(async () => {
      const pending = runs.filter(r => r.run_id && !["completed", "failed", "cancelled"].includes(r.status));
      const updates = await Promise.all(pending.map(async r => {
        try { return {...r, ...await requestJSON<HostedRun>(`/agents/creao/${encodeURIComponent(r.run_id!)}`), error: undefined}; }
        catch(e) { return {...r, error: String(e)}; }
      }));
      if (!cancelled) setRuns(previous => previous.map(r => updates.find(u => u.run_id === r.run_id) || r));
    }, 3000);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [runs, pollUntil]);
  const ready = !!vision?.features;
  const external = provider !== "local";
  async function investigate() {
    if (!vision) return;
    setBusy(true);
    setError("");
    setReport(null);
    try {
      if (provider === "creao") {
        const selected = role === "all" ? roles : [role];
        setRuns(selected.map(role => ({role, status: "submitting"})));
        await Promise.all(selected.map(async selectedRole => {
          let run: HostedRun;
          try {
            run = await requestJSON<HostedRun>("/agents/analyze", {
              method: "POST", headers: {"Content-Type": "application/json"},
              body: JSON.stringify({features: vision.features, anomaly_score: vision.anomaly_score, crop_category: crop, provider: "creao", creao_role: selectedRole, authorize_external: consent}),
            });
          } catch(e) { run = {role: selectedRole, status: "failed", error: String(e)}; }
          setRuns(previous => previous.map(item => item.role === selectedRole ? {...run, role: selectedRole} : item));
        }));
        setPollUntil(Date.now() + 120000);
        return;
      }
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
          <option value="creao">CREAO specialist agents</option>
        </select>
      </label>
      {provider === "creao" && <label className="field">CREAO agent
        <select value={role} onChange={e => setRole(e.target.value)}>
          {roles.map(r => <option key={r} value={r}>{r.replaceAll("_", " ")}</option>)}
          <option value="all">Run all 9 CREAO agents</option>
        </select>
        <span className="muted">Independent hosted runs. Specialists report missing inputs; no live sensor history or visitor data is supplied.</span>
      </label>}
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
      {runs.length > 0 && <div aria-live="polite">
        {runs.map(r => <article key={r.role}>
          <h3>{r.role.replaceAll("_", " ")}</h3><p>{r.status}</p>
          {r.error && <p className="error">{r.error}</p>}
          {r.notice && <p>{r.notice}</p>}
          {r.result != null && <pre className="code-result">{typeof r.result === "string" ? r.result : JSON.stringify(r.result, null, 2)}</pre>}
        </article>)}
        <button className="secondary" disabled={busy} onClick={() => void checkRuns()}>Check existing hosted runs</button>
        <p className="muted">Automatic checks stop after two minutes. Manual checks never submit a new run.</p>
      </div>}
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
