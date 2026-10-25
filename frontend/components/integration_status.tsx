"use client";
import { useState } from "react";
import { requestJSON } from "../lib/api";
type Status = {
  fetch: { ready: boolean; message: string; messaging_verified: boolean };
  creao: { configured: boolean; message: string; agents: {role: string; name: string; configured: boolean}[] };
  tiger_data: { configured: boolean; message: string };
};
export default function IntegrationStatus() {
  const [status, setStatus] = useState<Status | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function check() {
    setBusy(true);
    setError("");
    try {
      setStatus(await requestJSON<Status>("/integrations/status"));
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel support">
      <p className="eyebrow">Connection checks</p>
      <h2>Know what is connected</h2>
      <p className="muted">
        Checking configuration does not prove a successful agent run or database
        query. Credentials are never displayed.
      </p>
      <button
        className="secondary"
        disabled={busy}
        onClick={() => void check()}
      >
        {busy ? "Checking…" : "Check integration status"}
      </button>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {status && (
        <div className="integration-grid">
          <article>
            <h3>Fetch.ai</h3>
            <p>
              {status.fetch.ready
                ? "Receiver responds · messaging still needs verification"
                : "Needs attention"}
            </p>
            <p className="muted">{status.fetch.message}</p>
          </article>
          <article>
            <h3>CREAO</h3>
            <p>
              {status.creao.configured
                ? "Configuration present · not verified"
                : "Not configured"}
            </p>
            <p className="muted">{status.creao.message}</p>
            <ul>{status.creao.agents.map(agent => <li key={agent.role}>
              {agent.name}: {agent.configured ? "configured" : "missing credentials"}
            </li>)}</ul>
          </article>
        </div>
      )}
    </section>
  );
}
