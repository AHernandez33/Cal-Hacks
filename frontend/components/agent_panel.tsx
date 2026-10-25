"use client";
import Link from "next/link";
import AgentReport from "./agent_report";
import { useEffect, useRef, useState } from "react";
import {
  requestJSON,
  fetchInvestigation,
  type VisionResponse,
  type PrivacySettings,
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
  const [servicesEnabled, setServicesEnabled] = useState<boolean | null>(null);
  const [permissionBusy, setPermissionBusy] = useState(false);
  const [permissionError, setPermissionError] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [report, setReport] = useState<Report | null>(null);
  const [role, setRole] = useState("coordinator");
  const [runs, setRuns] = useState<HostedRun[]>([]);
  const [pollUntil, setPollUntil] = useState(0);
  const generation = useRef(0);
  useEffect(() => {
    const clear = () => {
      generation.current += 1;
      setRuns([]);
      setReport(null);
      setError("");
      setConsent(false);
      setServicesEnabled(null);
      setPermissionError("");
      setPermissionBusy(false);
      setPollUntil(0);
      setBusy(false);
    };
    window.addEventListener("vigilo-account-change", clear);
    return () => {
      generation.current += 1;
      window.removeEventListener("vigilo-account-change", clear);
    };
  }, []);
  useEffect(() => {
    if (provider === "local") return;
    let active = true;
    let revision = 0;
    const load = () => {
      const current = generation.current;
      const requested = ++revision;
      requestJSON<PrivacySettings>("/privacy/settings").then(settings => {
        if (active && current === generation.current && requested === revision) { setServicesEnabled(settings.external_services_enabled); setPermissionError(""); }
      }).catch(e => {
        if (active && current === generation.current && requested === revision) { setServicesEnabled(null); setPermissionError(String(e)); }
      });
    };
    load();
    window.addEventListener("vigilo-privacy-change", load);
    window.addEventListener("vigilo-account-change", load);
    return () => {
      active = false;
      window.removeEventListener("vigilo-privacy-change", load);
      window.removeEventListener("vigilo-account-change", load);
    };
  }, [provider]);
  async function saveExternalPermission(enabled: boolean) {
    const current = generation.current;
    const before = servicesEnabled;
    setServicesEnabled(enabled);
    setPermissionBusy(true);
    setPermissionError("");
    try {
      const settings = await requestJSON<PrivacySettings>("/privacy/settings", {
        method: "PUT", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({external_services_enabled: enabled}),
      });
      if (current !== generation.current) return;
      setServicesEnabled(settings.external_services_enabled);
      setError("");
      window.dispatchEvent(new Event("vigilo-privacy-change"));
    } catch(e) {
      if (current === generation.current) { setServicesEnabled(before); setPermissionError(String(e)); }
    } finally {
      if (current === generation.current) setPermissionBusy(false);
    }
  }
  function agentError(value: unknown) {
    const message = String(value);
    return message.includes("external_services_disabled")
      ? "External services are off for this workspace. Enable them above and authorize the request before running agents."
      : message;
  }
  async function checkRuns() {
    const current = generation.current;
    await Promise.all(runs.filter(r => r.run_id && !["completed", "failed", "cancelled"].includes(r.status)).map(async r => {
      try {
        const update = await requestJSON<HostedRun>(`/agents/creao/${encodeURIComponent(r.run_id!)}`);
        if (generation.current === current) setRuns(previous => previous.map(item => item.run_id === r.run_id ? {...item, ...update} : item));
      } catch (e) {
        if (generation.current === current) setRuns(previous => previous.map(item => item.run_id === r.run_id ? {...item, error: agentError(e)} : item));
      }
    }));
  }
  useEffect(() => {
    if (!pollUntil || Date.now() >= pollUntil || !runs.some(r => r.run_id && !["completed", "failed", "cancelled"].includes(r.status))) return;
    let cancelled = false;
    const timer = setTimeout(async () => {
      const pending = runs.filter(r => r.run_id && !["completed", "failed", "cancelled"].includes(r.status));
      const updates = await Promise.all(pending.map(async r => {
        try { return {...r, ...await requestJSON<HostedRun>(`/agents/creao/${encodeURIComponent(r.run_id!)}`)}; }
        catch(e) { return {...r, error: agentError(e)}; }
      }));
      if (!cancelled) setRuns(previous => previous.map(r => updates.find(u => u.run_id === r.run_id) || r));
    }, 3000);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [runs, pollUntil]);
  const ready = !!vision?.features;
  const external = provider !== "local";
  async function investigate() {
    if (!vision) return;
    const current = ++generation.current;
    setBusy(true);
    setPollUntil(0);
    setRuns([]);
    setError("");
    setReport(null);
    try {
      if (external) {
        if (!consent) throw new Error("Authorize this request before running external agents.");
        const settings = await requestJSON<PrivacySettings>("/privacy/settings");
        if (generation.current !== current) return;
        setServicesEnabled(settings.external_services_enabled);
        if (!settings.external_services_enabled)
          throw new Error("External services are off for this workspace. Enable them above, then run your investigation again.");
      }
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
          } catch(e) { run = {role: selectedRole, status: "failed", error: agentError(e)}; }
          if (generation.current === current) setRuns(previous => previous.map(item => item.role === selectedRole ? {...run, role: selectedRole} : item));
        }));
        if (generation.current === current) setPollUntil(Date.now() + 120000);
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
      if (generation.current === current) setReport(result as Report);
    } catch (e) {
      if (generation.current === current) setError(agentError(e));
    } finally {
      if (generation.current === current) setBusy(false);
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
      setError(agentError(e));
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
          disabled={busy}
          aria-label="Provider"
          value={provider}
          onChange={(e) => {
            setProvider(e.target.value);
            setConsent(false);
            setServicesEnabled(null);
            setPermissionError("");
          }}
        >
          <option value="local">Local evidence workflow</option>
          <option value="fetch">Fetch.ai agent messaging</option>
          <option value="creao">CREAO specialist agents</option>
        </select>
      </label>
      {provider === "creao" && <label className="field">CREAO agent
        <select aria-label="CREAO agent" disabled={busy} value={role} onChange={e => setRole(e.target.value)}>
          {roles.map(r => <option key={r} value={r}>{r.replaceAll("_", " ")}</option>)}
          <option value="all">Run all 9 CREAO agents</option>
        </select>
        <span className="muted">Independent hosted runs. Specialists report missing inputs; no live sensor history or visitor data is supplied.</span>
      </label>}
      {external && <div>
        <label className="consent">
          <input type="checkbox" checked={servicesEnabled === true}
            disabled={busy || permissionBusy || servicesEnabled === null}
            onChange={event => void saveExternalPermission(event.target.checked)} />
          Allow external agent services for this workspace
        </label>
        <p className="muted" role="status">
          {permissionBusy ? "Saving permission…" : servicesEnabled === null
            ? "Checking this workspace’s saved permission…" : servicesEnabled
            ? "External services enabled. Authorize the request below to continue."
            : "External services are off. Enable the workspace permission above to run CREAO or Fetch agents."}
        </p>
        {permissionError && <p className="error" role="alert">{permissionError}</p>}
        <label className="consent">
          <input type="checkbox" checked={consent} disabled={busy || permissionBusy}
            onChange={event => setConsent(event.target.checked)} />
          I authorize this request to the selected agent service.
        </label>
      </div>}
      <button
        disabled={!ready || busy || permissionBusy || (external && (!consent || servicesEnabled !== true))}
        onClick={() => void investigate()}
      >
        {busy ? "Working…" : provider === "creao" && role === "all" ? "Run all 9 CREAO agents" : "Request investigation"}
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
          {r.result != null && <AgentReport value={r.result} />}
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
            <AgentReport value={report.result} />
          )}
        </div>
      )}
    </section>
  );
}
