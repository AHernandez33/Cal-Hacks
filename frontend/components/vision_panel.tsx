"use client";
import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import { analyzeImage, type VisionResponse } from "../lib/api";

type Props = { onAnalyzed?: (data: VisionResponse) => void };
export default function VisionPanel({ onAnalyzed }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [cameraOn, setCameraOn] = useState(false);
  const [starting, setStarting] = useState(false);
  const [facing, setFacing] = useState("environment");
  const [device, setDevice] = useState("");
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<VisionResponse | null>(null);
  function stopCamera() {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraOn(false);
  }
  useEffect(
    () => () => {
      streamRef.current?.getTracks().forEach((t) => t.stop());
    },
    [],
  );
  async function startCamera() {
    setError("");
    setStarting(true);
    try {
      if (!navigator.mediaDevices?.getUserMedia)
        throw new Error(
          "Camera requires localhost or HTTPS and browser camera permissions.",
        );
      const stream = await navigator.mediaDevices.getUserMedia({
        video: device
          ? { deviceId: { exact: device } }
          : { facingMode: { ideal: facing } },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setCameraOn(true);
      setDevices(
        (await navigator.mediaDevices.enumerateDevices()).filter(
          (d) => d.kind === "videoinput",
        ),
      );
    } catch (e) {
      stopCamera();
      setError(e instanceof Error ? e.message : "Camera unavailable");
    } finally {
      setStarting(false);
    }
  }
  async function submit(blob: Blob) {
    setBusy(true);
    setError("");
    try {
      const data = await analyzeImage(blob);
      setResult(data);
      onAnalyzed?.(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Image analysis failed");
    } finally {
      setBusy(false);
    }
  }
  async function capture() {
    const video = videoRef.current;
    if (!video || !video.videoWidth) {
      setError("Camera is not ready");
      return;
    }
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0);
    canvas.toBlob(
      (blob) => {
        if (blob) void submit(blob);
        else setError("Could not capture image");
      },
      "image/jpeg",
      0.85,
    );
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
          disabled={starting}
          onClick={cameraOn ? stopCamera : startCamera}
        >
          {starting
            ? "Opening camera…"
            : cameraOn
              ? "Stop camera"
              : "Start camera"}
        </button>
        <button type="button" disabled={!cameraOn || busy} onClick={capture}>
          {busy ? "Analyzing…" : "Capture & analyze"}
        </button>
        <label className="file-label">
          Upload leaf photo{" "}
          <input
            aria-label="Upload leaf photo"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            capture="environment"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) void submit(file);
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
        style={{ display: cameraOn ? "block" : "none" }}
      />
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
