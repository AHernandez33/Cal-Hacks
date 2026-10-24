"use client";
import { useEffect, useState } from "react";
import {
  saveObservation,
  listObservations,
  deleteObservation,
  setQueued,
  type Observation,
} from "../lib/offline_storage";
import { synchronizeQueue } from "../lib/sync_queue";
import type { VisionResponse } from "../lib/api";
export default function OfflinePanel({
  onAnalyzed,
}: {
  onAnalyzed?: (value: VisionResponse) => void;
}) {
  const [items, setItems] = useState<Observation[]>([]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  async function refresh() {
    try {
      setItems(await listObservations());
    } catch (e) {
      setMessage(String(e));
    }
  }
  useEffect(() => {
    let active = true;
    listObservations()
      .then((values) => {
        if (active) setItems(values);
      })
      .catch((e) => {
        if (active) setMessage(String(e));
      });
    return () => {
      active = false;
    };
  }, []);
  async function save(file: File) {
    try {
      if (localStorage.getItem("vigilo-retention") !== "true")
        throw new Error(
          "Connect in Privacy settings and enable local photo retention before saving. That choice remains available offline.",
        );
      await saveObservation(file, file.name);
      setMessage("Saved on this device. Nothing uploaded.");
      await refresh();
    } catch (e) {
      setMessage(String(e));
    }
  }
  async function sync() {
    if (
      !window.confirm(
        "Send queued photos to your configured backend for analysis now? Photos are processed but not retained there. No agent request is made.",
      )
    )
      return;
    setBusy(true);
    try {
      const result = await synchronizeQueue(true, onAnalyzed);
      setMessage(`${result.completed} analyzed. ${result.errors.join(" ")}`);
      await refresh();
    } catch (e) {
      setMessage(String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel">
      <p className="eyebrow">Device storage</p>
      <h2>Mobile Field Mode</h2>
      <p className="muted">
        Save photos and manage the queue offline. Backend OpenCV and agent
        services require a connection. Sync sends photos for analysis; it does
        not create a server photo archive.
      </p>
      <label className="file-label">
        Save a photo locally
        <input
          type="file"
          accept="image/jpeg,image/png,image/webp"
          capture="environment"
          disabled={busy}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void save(file);
            e.currentTarget.value = "";
          }}
        />
      </label>
      <p>
        {items.length} saved · {items.filter((x) => x.queued).length} queued
      </p>
      <div className="history">
        {items.map((item) => (
          <article className="observation" key={item.id}>
            <strong>{item.name}</strong>
            <p className="muted">{new Date(item.createdAt).toLocaleString()}</p>
            <div className="actions">
              <button
                className="secondary"
                disabled={busy}
                onClick={() =>
                  void setQueued(item.id, !item.queued)
                    .then(refresh)
                    .catch((e) => setMessage(String(e)))
                }
              >
                {item.queued ? "Remove from queue" : "Queue analysis"}
              </button>
              <button
                className="secondary"
                disabled={busy}
                onClick={() => {
                  if (window.confirm("Delete this photo from this device?"))
                    void deleteObservation(item.id)
                      .then(refresh)
                      .catch((e) => setMessage(String(e)));
                }}
              >
                Delete
              </button>
            </div>
            {item.lastError && <p className="error">{item.lastError}</p>}
          </article>
        ))}
      </div>
      <button
        disabled={busy || !items.some((x) => x.queued)}
        onClick={() => void sync()}
      >
        {busy ? "Synchronizing…" : "Synchronize queued photos with consent"}
      </button>
      <p role="status">{message}</p>
    </section>
  );
}
