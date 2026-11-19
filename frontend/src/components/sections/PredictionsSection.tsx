import type { ModelInfoData, PredictionsData } from "@/types/api";
import PredictionTable from "@/components/PredictionTable";
import BarChart from "@/components/BarChart";

export default function PredictionsSection({ data, models }: { data: PredictionsData; models: ModelInfoData }) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Prediksi & Segmen</h2>
        <p className="mt-1 text-slate-600">
          Hasil model untuk {data.processed_rows.toLocaleString("id-ID")} pelanggan.
          Threshold churn {models.classification.threshold}. Estimasi memakai {models.regression.unit}.
        </p>
      </div>
      <BarChart title="Jumlah pelanggan per segmen" data={models.clustering.segments.map(segment => ({
        label: segment.segment_name, count: segment.customer_count,
      }))} />
      {data.warnings.length > 0 && <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        {data.warnings.map(warning => <p key={warning}>{warning}</p>)}
      </div>}
      <PredictionTable predictions={data.predictions} unit={models.regression.unit} />
    </div>
  );
}
