import type {
  DatasetSummaryResponse,
  PredictionsResponse,
  ModelInfoResponse,
  HealthResponse,
} from "@/types/api";

const API_BASE = "http://localhost:8000";

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<HealthResponse>;
}

export async function fetchDatasetSummary(): Promise<DatasetSummaryResponse> {
  const res = await fetch(`${API_BASE}/api/dataset-summary`);
  if (!res.ok) {
    throw new Error(
      `Failed to fetch dataset summary: ${res.status} ${res.statusText}`
    );
  }
  return res.json() as Promise<DatasetSummaryResponse>;
}

export async function fetchPredictions(): Promise<PredictionsResponse> {
  const res = await fetch(`${API_BASE}/api/predictions`);
  if (!res.ok) {
    throw new Error(
      `Failed to fetch predictions: ${res.status} ${res.statusText}`
    );
  }
  return res.json() as Promise<PredictionsResponse>;
}

export async function fetchModelInfo(): Promise<ModelInfoResponse> {
  const res = await fetch(`${API_BASE}/api/model-info`);
  if (!res.ok) {
    throw new Error(
      `Failed to fetch model info: ${res.status} ${res.statusText}`
    );
  }
  return res.json() as Promise<ModelInfoResponse>;
}
