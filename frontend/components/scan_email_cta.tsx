"use client";
import { useState } from "react";
import Link from "next/link";
import { requestJSON, type VisionResponse } from "../lib/api";

type Started = { request_id: string; message: string };
type Finished = { sent: boolean; message: string };

export default function ScanEmailCTA({ result }: { result: VisionResponse }) {
  const [email, setEmail] = useState("");
  const [consent, setConsent] = useState(false);
  const [code, setCode] = useState("");
  const [requestId, setRequestId] = useState("");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const [message, setMessage] = useState("");

  async function start(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!consent) return;
    setBusy(true);
    setMessage("");
    try {
      const data = await requestJSON<Started>("/reports/verify/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email, consent_to_email: consent,
          yellow_fraction: result.features.yellow_fraction,
          brown_fraction: result.features.brown_fraction,
          anomaly_score: result.anomaly_score,
          leaf_coverage_fraction: result.leaf_coverage_fraction,
        }),
      });
      setRequestId(data.request_id);
      setMessage(data.message);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not request verification.");
    } finally { setBusy(false); }
  }

  async function confirm(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!requestId) return;
    setBusy(true);
    setMessage("");
    try {
      const data = await requestJSON<Finished>("/reports/verify/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ request_id: requestId, code: code.trim() }),
      });
      setSent(data.sent);
      setMessage(data.message);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not verify code.");
    } finally { setBusy(false); }
  }

  return (
    <section className="scan-cta" aria-label="Email crop results">
      <p className="eyebrow">Crop scan complete</p>
      <h3>Email your detailed results</h3>
      <p>Verify that the inbox is yours, then receive your numerical observations. No workspace key or credit card is required for this report.</p>
      {!requestId ? (
        <form onSubmit={e => void start(e)}>
          <label className="field">Email address
            <input type="email" autoComplete="email" required maxLength={254}
              value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" />
          </label>
          <label className="consent">
            <input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)} />
            I agree to receive a verification code and this one crop report by email. No photo is sent.
          </label>
          <button type="submit" disabled={busy || !consent}>{busy ? "Sending code…" : "Verify email & get my results"}</button>
        </form>
      ) : !sent ? (
        <form onSubmit={e => void confirm(e)}>
          <p>A six-digit verification code was requested for <strong>{email}</strong>. It expires after 10 minutes.</p>
          <label className="field">Verification code
            <input required inputMode="numeric" pattern="[0-9]{6}" maxLength={6}
              value={code} onChange={e => setCode(e.target.value)} placeholder="123456" />
          </label>
          <div className="actions">
            <button type="submit" disabled={busy || code.length !== 6}>{busy ? "Verifying…" : "Send my report"}</button>
            <button type="button" className="secondary" onClick={() => {setRequestId("");setCode("");setMessage("");}}>Start over</button>
          </div>
        </form>
      ) : (
        <p>Report submitted to your email provider. Check your inbox and spam folder.</p>
      )}
      <p role="status" className="muted">{message}</p>
      <p className="muted">This does not yet create a verified Free account or unlock 10 daily scans. Email sending requires configured SMTP on the backend.</p>
      <Link href="/plans">Explore Free, Gold & Platinum</Link>
    </section>
  );
}
