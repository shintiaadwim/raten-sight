export interface ApiError {
  code: string;
  message: string;
  row?: number;
  field?: string;
}

interface ResponseMetadata {
  is_demo: boolean;
  dataset_version: string | null;
  model_version: string | null;
}

export type ApiResponse<T> = ResponseMetadata & (
  | { status: "ready"; data: T; error: null }
  | { status: "preparing"; data: null; error: null }
  | { status: "failed"; data: null; error: ApiError }
);

export interface DistributionEntry {
  label: string;
  count: number;
}

export interface DatasetSummaryData {
  processed_rows: number;
  actual_churn: { yes_count: number; no_count: number; rate: number } | null;
  distributions: {
    contract: DistributionEntry[];
    tenure: DistributionEntry[];
    monthly_charges: DistributionEntry[];
  };
}

export type DatasetSummaryResponse = ApiResponse<DatasetSummaryData> & { dataset_name: string };

export interface Prediction {
  customer_id: string;
  churn_probability: number | null;
  churn_prediction: "Yes" | "No" | null;
  segment_id: number | null;
  segment_name: string | null;
  predicted_monthly_charges: number | null;
  recommendation: string | null;
}

export interface PredictionsData {
  processed_rows: number;
  warnings: string[];
  predictions: Prediction[];
}

export type PredictionsResponse = ApiResponse<PredictionsData>;

export interface ClusterSegment {
  segment_id: number;
  segment_name: string;
  customer_count: number;
  average_tenure_months: number | null;
  profile?: string | null;
  is_noise?: boolean;
}

export interface ModelInfoData {
  classification: { algorithm: string; features: string[]; positive_class: string | number | boolean; threshold: number };
  clustering: { algorithm: string; features: string[]; segments: ClusterSegment[] };
  regression: { algorithm: string; features: string[]; target: string; unit: string };
}

export type ModelInfoResponse = ApiResponse<ModelInfoData>;
export type ExperimentRow = Record<string, string | number | boolean | null>;

export interface EvaluationsData {
  dataset_version: string;
  model_version: string;
  currency_unit: string;
  classification: {
    cv_candidates: ExperimentRow[];
    test_evaluation: {
      selected_model: string;
      evaluation_source: string;
      test_size: number;
      threshold: number;
      f1: number;
      recall: number;
      precision: number;
      roc_auc: number;
      accuracy: number;
      confusion_matrix: { tn: number; fp: number; fn: number; tp: number };
    };
  };
  clustering: {
    candidates: ExperimentRow[];
    elbow_curve: { k: number; inertia: number }[];
    segment_profiles: {
      segment_id: number;
      segment_name: string;
      customer_count: number;
      tenure_mean: number;
      monthly_charges_mean: number;
      historical_churn_rate_pct: number;
    }[];
  };
  regression: {
    cv_candidates: ExperimentRow[];
    test_evaluation: {
      selected_model: string;
      evaluation_source: string;
      test_size: number;
      mae_usd: number;
      rmse_usd: number;
      r2: number;
      actual_vs_predicted_and_residuals_sample: {
        customer_id: string;
        actual_monthly_charges: number;
        predicted_monthly_charges: number;
        residual: number;
      }[];
    };
  };
}

export type EvaluationsResponse = ApiResponse<EvaluationsData>;

export interface DashboardSnapshot {
  summary: DatasetSummaryResponse & { status: "ready" };
  predictions: PredictionsResponse & { status: "ready" };
  modelInfo: ModelInfoResponse & { status: "ready" };
  evaluations: EvaluationsResponse;
}
