export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
export type LeafFeatures = {
  yellow_fraction: number;
  brown_fraction: number;
  mean_hue: number;
  texture_variance: number;
  edge_density: number;
};
export type VisionResponse = {
  features: LeafFeatures;
  anomaly_score: number;
  leaf_coverage_fraction: number;
  heatmap_data_url: string;
  warnings: string[];
  disclaimer: string;
};
export type PrivacySettings = {
  collaborative_training_enabled: boolean;
  external_services_enabled: boolean;
  observation_sync_enabled: boolean;
  local_retention_enabled: boolean;
};
export function getAccessToken() {
  return typeof window === "undefined"
    ? ""
    : sessionStorage.getItem("vigilo-access-token") || "";
}
export function setAccessToken(token: string) {
  if (token) sessionStorage.setItem("vigilo-access-token", token);
  else sessionStorage.removeItem("vigilo-access-token");
}
export async function requestJSON<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const headers = new Headers(init?.headers);
  const token = getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
  const text = await response.text();
  let body: unknown;
  try {
    body = text ? JSON.parse(text) : null;
  } catch {
    body = text;
  }
  if (!response.ok) {
    const detail =
      body && typeof body === "object" && "detail" in body
        ? (body as { detail: unknown }).detail
        : body;
    throw new Error(
      `${response.status}: ${typeof detail === "string" ? detail : JSON.stringify(detail)}`,
    );
  }
  return body as T;
}
export async function analyzeImage(image: Blob): Promise<VisionResponse> {
  const form = new FormData();
  form.append(
    "file",
    image,
    image.type === "image/png" ? "leaf.png" : "leaf.jpg",
  );
  return requestJSON<VisionResponse>("/vision/analyze", {
    method: "POST",
    body: form,
  });
}
export async function fetchInvestigation(
  features: LeafFeatures,
  anomalyScore: number,
  cropCategory: string,
  authorizeExternal = false,
) {
  return requestJSON<Record<string, unknown>>("/agents/fetch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      features,
      anomaly_score: anomalyScore,
      crop_category: cropCategory,
      authorize_external: authorizeExternal,
    }),
  });
}
