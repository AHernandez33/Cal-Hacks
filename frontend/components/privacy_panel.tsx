"use client";
import { useEffect, useState } from "react";
import {
  setAccessToken,
  retentionKey,
  requestJSON,
  type PrivacySettings,
} from "../lib/api";
const labels: Record<keyof PrivacySettings, string> = {
  external_services_enabled: "Allow external agent services",
  collaborative_training_enabled:
    "Participate in future customer-data federated training",
  observation_sync_enabled:
    "Allow queued observations to be sent to this backend",
  local_retention_enabled: "Allow saving photos on this device",
};
export default function PrivacyPanel() {
  const [settings, setSettings] = useState<PrivacySettings | null>(null);
  const [token, setToken] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let active = true;
    let revision = 0;
    const refresh = () => {
      const requested = ++revision;
      requestJSON<PrivacySettings>("/privacy/settings").then(value => {
        if (active && requested === revision) { setSettings(value); setMessage("Preferences updated."); }
      }).catch(() => { if (active && requested === revision) setSettings(null); });
    };
    const accountChanged = () => { revision += 1; setSettings(null); setMessage(""); };
    window.addEventListener("vigilo-privacy-change", refresh);
    window.addEventListener("vigilo-account-change", accountChanged);
    return () => {
      active = false;
      window.removeEventListener("vigilo-privacy-change", refresh);
      window.removeEventListener("vigilo-account-change", accountChanged);
    };
  }, []);
  async function connect() {
    setBusy(true);
    setMessage("");
    try {
      if (token.trim()) setAccessToken(token.trim());
      const value = await requestJSON<PrivacySettings>("/privacy/settings");
      setSettings(value);
      localStorage.setItem(
        retentionKey(),
        String(value.local_retention_enabled),
      );
      setToken("");
      setMessage("Connected. Preferences loaded.");
    } catch (e) {
      setSettings(null);
      setMessage(String(e));
    } finally {
      setBusy(false);
    }
  }
  async function update(key: keyof PrivacySettings, value: boolean) {
    const before = settings;
    if (before) setSettings({ ...before, [key]: value });
    setBusy(true);
    try {
      const result = await requestJSON<PrivacySettings>("/privacy/settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ [key]: value }),
      });
      setSettings(result);
      localStorage.setItem(
        retentionKey(),
        String(result.local_retention_enabled),
      );
      setMessage("Preference saved.");
      window.dispatchEvent(new Event("vigilo-privacy-change"));
    } catch (e) {
      setSettings(before);
      setMessage(String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel">
      <p className="eyebrow">Control center</p>
      <h2>Your data. Your choices.</h2>
      <p className="muted">
        Signed-in workspaces keep separate sharing preferences. Without a
        workspace, local development uses shared demo settings.
      </p>
      <p className="muted">
        <a href="/login">Sign in with a private workspace key</a> — no name or
        email required.
      </p>
      <details>
        <summary>Deployment administrator access (optional)</summary>
        <p className="muted">
          This is a server-owner setup password, not a customer login. Local
          development does not need it. Never share it with customers.
        </p>
        <label className="field">
          Deployment access token
          <input
            type="password"
            autoComplete="off"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Leave empty for local development"
          />
        </label>
      </details>
      <div className="actions">
        <button disabled={busy} onClick={() => void connect()}>
          Connect / refresh
        </button>
        <button
          className="secondary"
          onClick={() => {
            setAccessToken("");
            setSettings(null);
            setMessage("Session token cleared.");
          }}
        >
          Disconnect
        </button>
      </div>
      {settings && (
        <div className="checklist">
          {(Object.keys(labels) as (keyof PrivacySettings)[]).map((key) => (
            <label key={key}>
              <input
                type="checkbox"
                disabled={busy}
                checked={settings[key]}
                onChange={(e) => void update(key, e.target.checked)}
              />
              {labels[key]}
            </label>
          ))}
        </div>
      )}
      <p className="muted">
        Each external request and sync also requires explicit consent. Turning
        retention off prevents new saves; delete existing local photos in Field
        Mode. Synthetic training opt-ins are separate from customer-data
        permission.
      </p>
      <p role="status">{message}</p>
    </section>
  );
}
