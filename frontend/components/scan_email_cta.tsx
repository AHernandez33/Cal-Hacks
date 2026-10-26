"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { requestJSON, type VisionResponse } from "../lib/api";

type Started = { request_id: string; message: string };
type Finished = { sent: boolean; message: string };

export default function ScanEmailCTA({ result }: { result: VisionResponse }) {
  const [availability, setAvailability] = useState<{
    available: boolean;
    message: string;
  } | null>(null);
  const [connectionError, setConnectionError] = useState("");
  async function checkAvailability() {
    try {
      setAvailability(
        await requestJSON<{ available: boolean; message: string }>(
          "/reports/verify/status",
        ),
      );
      setConnectionError("");
    } catch (error) {
      setConnectionError(String(error));
    }
  }
  useEffect(() => {
    let active = true;
    requestJSON<{ available: boolean; message: string }>(
      "/reports/verify/status",
    )
      .then((value) => {
        if (active) setAvailability(value);
      })
      .catch((error) => {
        if (active) setConnectionError(String(error));
      });
    return () => {
      active = false;
    };
  }, []);
  function download() {
    const text = [
      "VigiloForge crop observations",
      "Heuristic measurements, not a disease diagnosis.",
      `Yellow area: ${(result.features.yellow_fraction * 100).toFixed(1)}%`,
      `Brown area: ${(result.features.brown_fraction * 100).toFixed(1)}%`,
      `Visible discoloration: ${(result.anomaly_score * 100).toFixed(1)}/100`,
      `Leaf coverage: ${(result.leaf_coverage_fraction * 100).toFixed(1)}%`,
      "No image, email address, or workspace key is included.",
    ].join("\n");
    const url = URL.createObjectURL(
      new Blob([text], { type: "text/plain;charset=utf-8" }),
    );
    const link = document.createElement("a");
    link.href = url;
    link.download = "vigiloforge-report.txt";
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
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
          email,
          consent_to_email: consent,
          yellow_fraction: result.features.yellow_fraction,
          brown_fraction: result.features.brown_fraction,
          anomaly_score: result.anomaly_score,
          leaf_coverage_fraction: result.leaf_coverage_fraction,
        }),
      });
      setRequestId(data.request_id);
      setMessage(data.message);
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Could not request verification.",
      );
    } finally {
      setBusy(false);
    }
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
      setMessage(
        error instanceof Error ? error.message : "Could not verify code.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="scan-cta" aria-label="Email crop results">
      <p className="eyebrow">Crop scan complete</p>
      <h3>Keep your crop observations</h3>
      <p>
        Download the numerical report directly to your device. No account or
        email address is needed.
      </p>
      <button type="button" onClick={download}>
        Download report
      </button>
      {!availability?.available && (
        <div>
          <p className="muted" role="status">
            {availability?.message || "Checking email availability…"}
          </p>
          {connectionError && <p className="error">{connectionError}</p>}
          <button
            className="secondary"
            type="button"
            onClick={() => void checkAvailability()}
          >
            Recheck email availability
          </button>
        </div>
      )}
      {availability?.available && (
        <>
          <p>
            Verify that the inbox is yours, then receive your numerical
            observations. No workspace key or credit card is required for this
            report.
          </p>
          {!requestId ? (
            <form onSubmit={(e) => void start(e)}>
              <label className="field">
                Email address
                <input
                  type="email"
                  autoComplete="email"
                  required
                  maxLength={254}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                />
              </label>
              <label className="consent">
                <input
                  type="checkbox"
                  checked={consent}
                  onChange={(e) => setConsent(e.target.checked)}
                />
                I agree to receive a verification code and this one crop report
                by email. No photo is sent.
              </label>
              <button type="submit" disabled={busy || !consent}>
                {busy ? "Sending code…" : "Verify email & get my results"}
              </button>
            </form>
          ) : !sent ? (
            <form onSubmit={(e) => void confirm(e)}>
              <p>
                A six-digit verification code was requested for{" "}
                <strong>{email}</strong>. It expires after 10 minutes.
              </p>
              <label className="field">
                Verification code
                <input
                  required
                  inputMode="numeric"
                  pattern="[0-9]{6}"
                  maxLength={6}
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="123456"
                />
              </label>
              <div className="actions">
                <button type="submit" disabled={busy || code.length !== 6}>
                  {busy ? "Verifying…" : "Send my report"}
                </button>
                <button
                  type="button"
                  className="secondary"
                  onClick={() => {
                    setRequestId("");
                    setCode("");
                    setMessage("");
                  }}
                >
                  Start over
                </button>
              </div>
            </form>
          ) : (
            <p>
              Report submitted to your email provider. Check your inbox and spam
              folder.
            </p>
          )}
          <p role="status" className="muted">
            {message}
          </p>
          <p className="muted">
            This does not yet create a verified Free account or unlock 10 daily
            scans. Email sending requires configured SMTP on the backend.
          </p>
        </>
      )}
      <Link href="/plans">Explore plans</Link>
    </section>
  );
}
