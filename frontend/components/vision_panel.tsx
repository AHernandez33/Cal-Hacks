"use client";
import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import { analyzeImage, type VisionResponse } from "../lib/api";

type Props = { onAnalyzed?: (data: VisionResponse) => void };
export default function VisionPanel({ onAnalyzed }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [cameraOn, setCameraOn] = useState(false);
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
    try {
      if (!navigator.mediaDevices?.getUserMedia)
        throw new Error(
          "Camera requires localhost or HTTPS and browser camera permissions.",
        );
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setCameraOn(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Camera unavailable");
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
      <div className="actions">
        <button type="button" onClick={cameraOn ? stopCamera : startCamera}>
          {cameraOn ? "Stop camera" : "Start camera"}
        </button>
        <button type="button" disabled={!cameraOn || busy} onClick={capture}>
          {busy ? "Analyzing…" : "Capture & analyze"}
        </button>
        <label className="file-label">
          Upload leaf photo{" "}
          <input
            aria-label="Upload leaf photo"
            type="file"
            accept="image/*"
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
          <pre className="code-result">
            {JSON.stringify(
              Object.fromEntries(
                Object.entries(result).filter(
                  ([key]) => key !== "heatmap_data_url",
                ),
              ),
              null,
              2,
            )}
          </pre>
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
