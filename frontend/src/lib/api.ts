import type {
  DashboardSnapshot, DatasetSummaryResponse, EvaluationsResponse,
  ModelInfoResponse, PredictionsResponse,
} from "@/types/api";

const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

async function readApi<T>(endpoint: string, signal?: AbortSignal): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/api/${endpoint}`, { signal, cache: "no-store" });
  } catch (error) {
    if (signal?.aborted) throw error;
    throw new Error("Backend tidak dapat dihubungi. Periksa server dan alamat API.");
  }
  if (!response.ok) throw new Error(`API ${endpoint} gagal dimuat (HTTP ${response.status}).`);
  return response.json() as Promise<T>;
}

export type DashboardLoad =
  | { status: "ready"; snapshot: DashboardSnapshot }
  | { status: "preparing"; message: string }
  | { status: "failed"; message: string };

export async function loadDashboard(signal?: AbortSignal): Promise<DashboardLoad> {
  const summary = await readApi<DatasetSummaryResponse>("dataset-summary", signal);
  if (summary.status === "failed") return { status: "failed", message: summary.error.message };
  if (summary.status === "preparing") return { status: "preparing", message: "Backend sedang menyiapkan hasil analisis." };

  const [predictions, modelInfo, evaluations] = await Promise.all([
    readApi<PredictionsResponse>("predictions", signal),
    readApi<ModelInfoResponse>("model-info", signal),
    readApi<EvaluationsResponse>("evaluations", signal),
  ]);
  const responses = [predictions, modelInfo, evaluations];
  const mismatch = responses.some(response =>
    response.dataset_version !== summary.dataset_version || response.model_version !== summary.model_version,
  );
  if (mismatch || predictions.status === "preparing" || modelInfo.status === "preparing" || evaluations.status === "preparing") {
    return { status: "preparing", message: "Versi analisis sedang berubah. Menunggu hasil yang konsisten." };
  }
  if (predictions.status === "failed") return { status: "failed", message: predictions.error.message };
  if (modelInfo.status === "failed") return { status: "failed", message: modelInfo.error.message };
  return { status: "ready", snapshot: { summary, predictions, modelInfo, evaluations } };
}
