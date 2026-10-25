"use client";
import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import { analyzeImage, type VisionResponse } from "../lib/api";

import { cameraError, captureCameraFrame, waitForCameraFrame } from "../lib/camera";

type Props = { onAnalyzed?: (data: VisionResponse) => void };
export default function VisionPanel({ onAnalyzed }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const openingRef = useRef<AbortController | null>(null);
  const generationRef = useRef(0);
  const workingRef = useRef(false);
  const snapshotRef = useRef("");
  const [snapshot, setSnapshot] = useState<{url: string; width: number; height: number} | null>(null);
  const [cameraOn, setCameraOn] = useState(false);
  const [frameReady, setFrameReady] = useState(false);
  const [starting, setStarting] = useState(false);
  const [facing, setFacing] = useState("environment");
  const [device, setDevice] = useState("");
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<VisionResponse | null>(null);
  function stopCamera() {
    generationRef.current += 1;
    openingRef.current?.abort();
    openingRef.current = null;
    streamRef.current?.getTracks().forEach(t => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraOn(false);
    setFrameReady(false);
    setStarting(false);
  }
  useEffect(() => () => {
    generationRef.current += 1;
    openingRef.current?.abort();
    streamRef.current?.getTracks().forEach(t => t.stop());
    if (snapshotRef.current) URL.revokeObjectURL(snapshotRef.current);
  }, []);
  async function startCamera() {
    stopCamera();
    const generation = generationRef.current;
    const controller = new AbortController();
    openingRef.current = controller;
    setError("");
    setStarting(true);
    try {
      if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia)
        throw new Error("Open this app on localhost or HTTPS to use the camera, then allow camera permission.");
      const stream = await navigator.mediaDevices.getUserMedia({
        video: device ? {deviceId: {exact: device}} : {facingMode: {ideal: facing}},
        audio: false,
      });
      // Permission prompts can resolve after cancellation or navigation.
      if (generation !== generationRef.current) {
        stream.getTracks().forEach(t => t.stop());
        return;
      }
      streamRef.current = stream;
      const video = videoRef.current;
      if (!video) throw new Error("Camera preview is unavailable. Reopen this page and try again.");
      video.srcObject = stream;
      video.muted = true;
      video.playsInline = true;
      setCameraOn(true);
      stream.getVideoTracks().forEach(track => track.addEventListener("ended", () => {
        if (generation === generationRef.current) {
          stopCamera();
          setError("The camera disconnected. Reconnect it and start the camera again.");
        }
      }, {once: true}));
      await Promise.all([video.play(), waitForCameraFrame(video, controller.signal)]);
      if (generation !== generationRef.current) return;
      setFrameReady(true);
      setStarting(false);
      // Some browsers restrict device enumeration even when video capture works.
      try {
        const available = await navigator.mediaDevices.enumerateDevices();
        if (generation === generationRef.current) setDevices(available.filter(d => d.kind === "videoinput"));
      } catch { /* Device names are optional; keep the working camera. */ }
    } catch (e) {
      if (generation === generationRef.current) {
        stopCamera();
        setError(cameraError(e));
      }
    } finally {
      if (generation === generationRef.current) setStarting(false);
    }
  }
  async function analyze(blob: Blob) {
    const data = await analyzeImage(blob);
    setResult(data);
    onAnalyzed?.(data);
  }
  async function withBusy(action: () => Promise<void>) {
    if (workingRef.current) return;
    workingRef.current = true;
    setBusy(true);
    setError("");
    try { await action(); }
    catch (e) { setError(e instanceof Error ? e.message : "Image analysis failed."); }
    finally { workingRef.current = false; setBusy(false); }
  }
  async function submit(blob: Blob) {
    await withBusy(() => analyze(blob));
  }
  async function capture() {
    await withBusy(async () => {
      const video = videoRef.current;
      if (!video) throw new Error("Start the camera and wait for its live preview first.");
      const {blob, width, height} = await captureCameraFrame(video);
      const url = URL.createObjectURL(blob);
      if (snapshotRef.current) URL.revokeObjectURL(snapshotRef.current);
      snapshotRef.current = url;
      setSnapshot({url, width, height});
      await analyze(blob);
    });
  }
  return (
    <section className="panel">
      <h2>Leaf imaging</h2>
      <p className="muted">
        NexiGo or any browser-accessible webcam. OpenCV reports heuristic
        observations, not a validated disease diagnosis.
      </p>
      <div className="camera-controls">
        <label className="field">
          Camera direction
          <select
            disabled={starting || busy}
            value={facing}
            onChange={(e) => {
              stopCamera();
              setDevice("");
              setFacing(e.target.value);
            }}
          >
            <option value="environment">Rear / leaf-facing camera</option>
            <option value="user">Front camera</option>
          </select>
        </label>
        {devices.length > 1 && (
          <label className="field">
            Camera device
            <select
              disabled={starting || busy}
              value={device}
              onChange={(e) => {
                stopCamera();
                setDevice(e.target.value);
              }}
            >
              <option value="">Use preferred direction</option>
              {devices.map((d, i) => (
                <option value={d.deviceId} key={d.deviceId}>
                  {d.label || `Camera ${i + 1}`}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>
      <div className="actions">
        <button
          type="button"
          disabled={busy}
          onClick={cameraOn || starting ? stopCamera : startCamera}
        >
          {starting
            ? "Cancel camera"
            : cameraOn
              ? "Stop camera"
              : "Start camera"}
        </button>
        <button type="button" disabled={!frameReady || busy || starting} onClick={capture}>
          {busy ? "Analyzing…" : "Capture & analyze"}
        </button>
        <label className="file-label">
          Upload leaf photo{" "}
          <input
            aria-label="Upload leaf photo"
            type="file"
            disabled={busy || starting}
            accept="image/jpeg,image/png,image/webp"
            capture="environment"
            onChange={(e) => {
              const file = e.target.files?.[0];
              const input = e.currentTarget;
              if (file) void submit(file).finally(() => { input.value = ""; });
            }}
          />
        </label>
      </div>
      <video
        ref={videoRef}
        autoPlay
        muted
        playsInline
        className="camera"
        aria-label="Live camera preview"
        style={{ display: cameraOn || starting ? "block" : "none" }}
      />
      {starting && <p role="status">Opening camera; waiting for a live picture…</p>}
      {frameReady && <p role="status">Camera ready. Position the leaf in the preview, then capture.</p>}
      {snapshot && <div>
        <h3>Captured photo</h3>
        <Image unoptimized src={snapshot.url} width={snapshot.width} height={snapshot.height}
          className="heatmap" alt="Latest captured camera photo" />
        <a href={snapshot.url} download="vigiloforge-capture.jpg">Download captured photo</a>
      </div>}
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {result && (
        <>
          <h3>Latest observations</h3>
          <div className="metric-cards observation-metrics">
            {[
              {
                name: "Yellow area",
                value: `${(result.features.yellow_fraction * 100).toFixed(1)}%`,
                meaning: "Fraction of the detected leaf classified as yellow.",
              },
              {
                name: "Brown area",
                value: `${(result.features.brown_fraction * 100).toFixed(1)}%`,
                meaning: "Fraction classified as brown.",
              },
              {
                name: "Visible discoloration",
                value: `${(result.anomaly_score * 100).toFixed(1)} / 100`,
                meaning: "A heuristic index, not a disease probability.",
              },
              {
                name: "Leaf coverage",
                value: `${(result.leaf_coverage_fraction * 100).toFixed(1)}%`,
                meaning: "How much of the frame was detected as leaf.",
              },
            ].map((item) => (
              <article key={item.name}>
                <span>{item.name}</span>
                <strong>{item.value}</strong>
                <small>{item.meaning}</small>
              </article>
            ))}
          </div>
          <h3>How to read the heatmap</h3>
          <p>
            Colored highlights mark areas the simple color rules classified as
            yellow or brown. Unhighlighted areas keep their original appearance.
            Lighting and background can change the result.
          </p>
          <p className="muted">
            This is not a temperature map, a disease diagnosis, or a confidence
            score. Use it to decide where to look more closely.
          </p>
          {result.warnings.map((warning) => (
            <p key={warning} className="warning">
              {warning}
            </p>
          ))}
          <details>
            <summary>All numerical observations</summary>
            <pre className="code-result">
              {JSON.stringify(
                { ...result, heatmap_data_url: undefined },
                null,
                2,
              )}
            </pre>
          </details>
          {typeof result.heatmap_data_url === "string" &&
            result.heatmap_data_url.startsWith("data:image/") && (
              <Image
                unoptimized
                width={768}
                height={768}
                className="heatmap"
                src={result.heatmap_data_url}
                alt="Heuristic image heatmap"
              />
            )}
        </>
      )}
    </section>
  );
}
