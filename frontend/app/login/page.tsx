"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import {
  requestJSON,
  setAccessToken,
  setWorkspaceSession,
  retentionKey,
  type PrivacySettings,
} from "../../lib/api";
type Session = { token: string; workspace_id: string; workspace_key?: string };
type Identity = { workspace_id: string; mode: string; plan: string };
export default function LoginPage() {
  const [key, setKey] = useState("");
  const [newKey, setNewKey] = useState("");
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  useEffect(() => {
    let active = true;
    requestJSON<Identity>("/auth/me")
      .then((value) => {
        if (active) setIdentity(value);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);
  async function accept(session: Session) {
    setWorkspaceSession(session.token, session.workspace_id);
    if (session.workspace_key) setNewKey(session.workspace_key);
    setKey("");
    setIdentity({
      workspace_id: session.workspace_id,
      mode: "workspace",
      plan: "free",
    });
    const preferences = await requestJSON<PrivacySettings>("/privacy/settings");
    localStorage.setItem(
      retentionKey(),
      String(preferences.local_retention_enabled),
    );
  }
  async function create() {
    setBusy(true);
    setMessage("");
    try {
      await accept(
        await requestJSON<Session>("/auth/workspaces", { method: "POST" }),
      );
      setMessage(
        "Workspace created. Save your private key before leaving this page.",
      );
    } catch (e) {
      setMessage(String(e));
    } finally {
      setBusy(false);
    }
  }
  async function login(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      await accept(
        await requestJSON<Session>("/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ workspace_key: key.trim() }),
        }),
      );
      setNewKey("");
      setMessage("Signed in. Open the dashboard to continue.");
    } catch (e) {
      setMessage(String(e));
    } finally {
      setBusy(false);
    }
  }
  async function logout() {
    setBusy(true);
    try {
      await requestJSON("/auth/logout", { method: "POST" });
      setAccessToken("");
      setIdentity(null);
      setNewKey("");
      setMessage("Signed out; this session has been revoked.");
    } catch (e) {
      setMessage(String(e));
    } finally {
      setBusy(false);
    }
  }
  async function remove() {
    if (
      !window.confirm(
        "Delete this workspace and its server-side preferences and sessions? Your saved browser photos are not deleted by this action.",
      )
    )
      return;
    setBusy(true);
    try {
      await requestJSON("/auth/workspace", { method: "DELETE" });
      setAccessToken("");
      setIdentity(null);
      setNewKey("");
      setMessage(
        "Workspace deleted. Delete local photos separately from Field Mode before sharing this browser profile.",
      );
    } catch (e) {
      setMessage(String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="container route-page">
      <p className="eyebrow">Private workspace</p>
      <h1>
        Your crops.
        <br />
        <span>Your space.</span>
      </h1>
      <p className="hero-copy">
        No name, email, or farm address required. Your randomly generated
        workspace key is your sign-in credential. Keep it private: anyone
        holding it can access this workspace.
      </p>
      <div className="grid">
        <section className="panel">
          <h2>Create a workspace</h2>
          <p>
            Separate sharing preferences and browser photo storage. Accounts and
            credential hashes are stored; this is data minimization, not
            complete anonymity.
          </p>
          <p className="muted">
            Workspace creation is available locally or to the deployment
            administrator. Remote pilot users receive a key privately from the
            administrator.
          </p>
          <button
            disabled={busy || identity?.mode === "workspace"}
            onClick={() => void create()}
          >
            Create private workspace
          </button>
          {newKey && (
            <div className="key-card">
              <h3>Save this key privately</h3>
              <code>{newKey}</code>
              <p className="muted">
                Shown only now. No email recovery is available. Do not put it in
                screenshots, GitHub, or chat.
              </p>
              <button
                className="secondary"
                onClick={() => {
                  navigator.clipboard
                    .writeText(newKey)
                    .then(() =>
                      setMessage(
                        "Key copied. Store it in your password manager.",
                      ),
                    )
                    .catch(() =>
                      setMessage("Select and copy the key manually."),
                    );
                }}
              >
                Copy workspace key
              </button>
            </div>
          )}
        </section>
        <section className="panel">
          <h2>Sign in</h2>
          <form onSubmit={(e) => void login(e)}>
            <label className="field">
              Workspace key
              <input
                type="password"
                autoComplete="off"
                required
                minLength={20}
                maxLength={150}
                value={key}
                onChange={(e) => setKey(e.target.value)}
              />
            </label>
            <button disabled={busy || !key.trim()}>Sign in with key</button>
          </form>
          {identity && (
            <>
              <p>
                Mode: {identity.mode} · Plan: {identity.plan}
              </p>
              {identity.mode === "workspace" && (
                <>
                  <p className="muted">
                    Workspace {identity.workspace_id.slice(0, 8)} · sessions
                    expire after 24 hours.
                  </p>
                  <div className="actions">
                    <Link className="button" href="/">
                      Open dashboard
                    </Link>
                    <button
                      className="secondary"
                      disabled={busy}
                      onClick={() => void logout()}
                    >
                      Sign out
                    </button>
                    <button
                      className="secondary"
                      disabled={busy}
                      onClick={() => void remove()}
                    >
                      Delete workspace
                    </button>
                  </div>
                </>
              )}
            </>
          )}
        </section>
      </div>
      <p role="status" className="status-message">
        {message}
      </p>
      <p className="muted">
        No tracking analytics or payment details are collected by this page.
        Server hosts can still process connection metadata. Signing out hides
        this workspace’s local photos in the app but does not encrypt or erase
        browser storage.
      </p>
    </main>
  );
}
