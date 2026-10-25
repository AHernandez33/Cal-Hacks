"use client";
import { useEffect, useState, useSyncExternalStore } from "react";
type InstallPrompt = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: string }>;
};
const subscribeOnline = (callback: () => void) => {
  window.addEventListener("online", callback);
  window.addEventListener("offline", callback);
  return () => {
    window.removeEventListener("online", callback);
    window.removeEventListener("offline", callback);
  };
};
export default function MobileStatus() {
  const online = useSyncExternalStore(
    subscribeOnline,
    () => navigator.onLine,
    () => true,
  );
  const [install, setInstall] = useState<InstallPrompt | null>(null);
  const [message, setMessage] = useState("");
  useEffect(() => {
    const listener = (event: Event) => {
      event.preventDefault();
      setInstall(event as InstallPrompt);
    };
    window.addEventListener("beforeinstallprompt", listener);
    return () => window.removeEventListener("beforeinstallprompt", listener);
  }, []);
  async function add() {
    if (!install) return;
    await install.prompt();
    const result = await install.userChoice;
    setMessage(
      result.outcome === "accepted"
        ? "Installation accepted."
        : "Installation dismissed.",
    );
    setInstall(null);
  }
  return (
    <aside className="mobile-status">
      <p>
        <span className="status-dot" aria-hidden="true" />{" "}
        {online ? "Device reports online" : "Device reports offline"}
      </p>
      <p className="muted">
        A connection indicator does not prove the backend is reachable. Photos
        stay in this browser until you explicitly synchronize.
      </p>
      {install && (
        <button className="secondary" onClick={() => void add()}>
          Install Field Mode
        </button>
      )}
      <details>
        <summary>Use on your phone</summary>
        <ol>
          <li>
            Open the deployed HTTPS website. A phone cannot use your laptop’s
            localhost address.
          </li>
          <li>
            Sign in with your private workspace key, then enable local photo
            retention in Privacy.
          </li>
          <li>
            Visit Field Mode online once before relying on offline access.
          </li>
          <li>
            Use your browser’s Install app option. On iPhone, use Safari → Share
            → Add to Home Screen.
          </li>
          <li>
            Choose a photo or use the rear camera. Queue observations and
            synchronize after reconnecting.
          </li>
        </ol>
        <p className="muted">
          Cloud agents and server-side OpenCV do not run offline. Installation
          prompts depend on the browser and may not appear.
        </p>
      </details>
      <p role="status">{message}</p>
    </aside>
  );
}
