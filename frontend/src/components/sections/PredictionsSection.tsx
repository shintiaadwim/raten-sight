import type { PredictionsResponse } from "@/types/api";
import PredictionTable from "@/components/PredictionTable";

interface PredictionsSectionProps {
  predictions: PredictionsResponse;
}

export default function PredictionsSection({
  predictions,
}: PredictionsSectionProps) {
  const { data } = predictions;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-800 mb-1">
            Prediksi Churn Pelanggan
          </h2>
          <p className="text-sm text-slate-500">
            Hasil prediksi model untuk setiap pelanggan dalam dataset.
          </p>
        </div>
        <div className="text-right">
          <span className="text-2xl font-bold text-indigo-600">
            {data.processed_rows}
          </span>
          <p className="text-xs text-slate-400">baris diproses</p>
        </div>
      </div>

      {data.warnings.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-sm font-semibold text-yellow-800 mb-1">
            Peringatan
          </p>
          <ul className="list-disc list-inside text-sm text-yellow-700 space-y-1">
            {data.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      <PredictionTable predictions={data.predictions} />
    </div>
  );
}
