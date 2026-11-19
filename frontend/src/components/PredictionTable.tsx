import type { Prediction } from "@/types/api";

interface PredictionTableProps {
  predictions: Prediction[];
}

function ChurnBadge({ probability }: { probability: number }) {
  const isHigh = probability > 0.5;
  return (
    <span
      className={`inline-block px-2.5 py-1 rounded-full text-xs font-bold ${
        isHigh
          ? "bg-red-100 text-red-700 border border-red-200"
          : "bg-green-100 text-green-700 border border-green-200"
      }`}
    >
      {(probability * 100).toFixed(1)}%
    </span>
  );
}

export default function PredictionTable({ predictions }: PredictionTableProps) {
  if (predictions.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8 text-center text-slate-400 text-sm">
        Tidak ada data prediksi.
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                Customer ID
              </th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                Churn Prob
              </th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                Prediksi
              </th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                Segmen
              </th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                Tagihan Prediksi
              </th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                Rekomendasi
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {predictions.map((p) => (
              <tr
                key={p.customer_id}
                className="hover:bg-slate-50 transition-colors"
              >
                <td className="px-4 py-3 font-mono text-slate-800 font-medium">
                  {p.customer_id}
                </td>
                <td className="px-4 py-3">
                  <ChurnBadge probability={p.churn_probability} />
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`font-semibold ${
                      p.churn_prediction === "Yes"
                        ? "text-red-600"
                        : "text-green-600"
                    }`}
                  >
                    {p.churn_prediction}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-600">{p.segment_name}</td>
                <td className="px-4 py-3 text-slate-700 font-medium">
                  {p.predicted_monthly_charges.toFixed(2)}
                </td>
                <td className="px-4 py-3 text-slate-500 max-w-xs">
                  {p.recommendation}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
