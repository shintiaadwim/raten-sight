// ─── Distribution ───────────────────────────────────────────────────────────

export interface DistributionEntry {
  label: string;
  count: number;
}

export interface Distributions {
  contract: DistributionEntry[];
  tenure: DistributionEntry[];
  monthly_charges: DistributionEntry[];
}

// ─── Actual Churn ────────────────────────────────────────────────────────────

export interface ActualChurn {
  yes_count: number;
  no_count: number;
  rate: number;
}

// ─── Dataset Summary ─────────────────────────────────────────────────────────

export interface DatasetSummaryData {
  processed_rows: number;
  actual_churn: ActualChurn;
  distributions: Distributions;
}

export interface DatasetSummaryResponse {
  is_demo: boolean;
  status: "ready" | "preparing" | "failed";
  dataset_name: string;
  dataset_version: string;
  model_version: string;
  data: DatasetSummaryData;
  error: string | null;
}

// ─── Predictions ─────────────────────────────────────────────────────────────

export interface Prediction {
  customer_id: string;
  churn_probability: number;
  churn_prediction: "Yes" | "No";
  segment_id: number;
  segment_name: string;
  predicted_monthly_charges: number;
  recommendation: string;
}

export interface PredictionsData {
  processed_rows: number;
  warnings: string[];
  predictions: Prediction[];
}

export interface PredictionsResponse {
  is_demo: boolean;
  status: "ready" | "preparing" | "failed";
  data: PredictionsData;
}

// ─── Model Info ──────────────────────────────────────────────────────────────

export interface ClassificationModel {
  algorithm: string;
  features: string[];
  positive_class: string;
  threshold: number;
}

export interface ClusterSegment {
  segment_id: number;
  segment_name: string;
  customer_count: number;
  average_tenure_months: number;
}

export interface ClusteringModel {
  algorithm: string;
  features: string[];
  segments: ClusterSegment[];
}

export interface RegressionModel {
  algorithm: string;
  features: string[];
  target: string;
  unit: string;
}

export interface ModelInfoData {
  classification: ClassificationModel;
  clustering: ClusteringModel;
  regression: RegressionModel;
}

export interface ModelInfoResponse {
  status: "ready" | "preparing" | "failed";
  data: ModelInfoData;
}

// ─── Health ──────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string;
}
