export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export type LeafFeatures = {
  yellow_fraction: number;
  brown_fraction: number;
  mean_hue: number;
  texture_variance: number;
  edge_density: number;
};

export type VisionResponse = Record<string, unknown>;

export async function requestJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { cache: "no-store", ...init });
  const text = await response.text();
  let body: unknown;
  try { body = text ? JSON.parse(text) : null; } catch { body = text; }
  if (!response.ok) {
    const detail = body && typeof body === "object" && "detail" in body ? String((body as { detail: unknown }).detail) : String(body || response.statusText);
    throw new Error(`${response.status}: ${detail}`);
  }
  return body as T;
}

export async function analyzeImage(image: Blob): Promise<VisionResponse> {
  const form = new FormData();
  form.append("file", image, "leaf.jpg");
  return requestJSON<VisionResponse>("/vision/analyze", { method: "POST", body: form });
}

export async function fetchInvestigation(features: LeafFeatures, anomalyScore: number, cropCategory: string) {
  return requestJSON<Record<string, unknown>>("/agents/fetch", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ features, anomaly_score: anomalyScore, crop_category: cropCategory }),
  });
}
