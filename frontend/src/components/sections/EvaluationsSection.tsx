import type { EvaluationsResponse, ExperimentRow } from "@/types/api";
import PlotChart from "@/components/PlotChart";

interface Column { key: string; label: string; std?: string }
const numberFormat = new Intl.NumberFormat("id-ID", { maximumFractionDigits: 4 });

function metric(value: string | number | boolean | null | undefined) {
  return typeof value === "number" ? numberFormat.format(value) : value == null ? "—" : String(value);
}

function Comparison({ title, rows, columns }: { title: string; rows: ExperimentRow[]; columns: Column[] }) {
  return <div className="overflow-x-auto" tabIndex={0} aria-label={title}>
    <table className="data-table w-full text-sm">
      <caption className="mb-3 text-left font-semibold">{title}</caption>
      <thead><tr><th scope="col">Kandidat</th>{columns.map(column => <th scope="col" key={column.key}>{column.label}</th>)}</tr></thead>
      <tbody>{rows.map((row, index) => <tr key={index} className={row.Selected ? "bg-indigo-50" : ""}>
        <th scope="row" className="min-w-60">
          <span>{String(row.Kandidat)}</span>
          {row.Selected && <span className="ml-2 rounded bg-indigo-100 px-2 py-1 text-xs text-indigo-800">Terpilih</span>}
          <details className="mt-2 font-normal text-slate-600">
            <summary className="cursor-pointer">Konfigurasi dan catatan</summary>
            <p className="mt-2">{String(row.Parameter ?? "—")}</p>
            <p className="mt-1">{String(row.Alasan_Pemilihan_Catatan ?? "")}</p>
          </details>
        </th>
        {columns.map(column => <td key={column.key} className="whitespace-nowrap">
          {metric(row[column.key])}{column.std && row[column.std] != null ? ` ± ${metric(row[column.std])}` : ""}
        </td>)}
      </tr>)}</tbody>
    </table>
    {!rows.length && <p className="py-3 text-slate-600">Tabel eksperimen belum tersedia.</p>}
  </div>;
}

export default function EvaluationsSection({ response }: { response: EvaluationsResponse }) {
  if (response.status !== "ready") return <p className="panel" role="status">
    {response.status === "failed" ? response.error.message : "Evaluasi sedang disiapkan."}
  </p>;
  const { classification, clustering, regression } = response.data;
  const test = classification.test_evaluation;
  const reg = regression.test_evaluation;
  const matrix = test.confusion_matrix;
  return <div className="space-y-6">
    <div>
      <h2 className="text-xl font-semibold">Evaluasi Model</h2>
      <p className="mt-1 text-sm text-slate-600">Sumber eksperimen {response.data.dataset_version} · Rilis {response.data.model_version}</p>
    </div>
    <section className="panel space-y-5">
      <h3 className="text-lg font-semibold">Klasifikasi churn</h3>
      <Comparison title="Cross-validation data latih · rerata ± simpangan baku" rows={classification.cv_candidates} columns={[
        { key: "F1_Mean", label: "F1 churn", std: "F1_Std" },
        { key: "Recall_Mean", label: "Recall", std: "Recall_Std" },
        { key: "Precision_Mean", label: "Precision", std: "Precision_Std" },
        { key: "ROC_AUC_Mean", label: "ROC-AUC", std: "ROC_AUC_Std" },
      ]} />
      <h4 className="font-semibold">Data uji · {test.selected_model}</h4>
      <p className="text-sm text-slate-600">{test.evaluation_source} · Threshold {test.threshold}</p>
      <dl className="grid grid-cols-2 gap-4 sm:grid-cols-4">{[
        ["F1 churn", test.f1], ["Recall", test.recall], ["Precision", test.precision], ["ROC-AUC", test.roc_auc],
      ].map(([label, value]) => <div key={label}><dt className="text-sm text-slate-600">{label}</dt><dd className="text-xl font-bold">{metric(value)}</dd></div>)}</dl>
      <div className="overflow-x-auto">
        <table className="data-table text-sm">
          <caption className="mb-2 text-left font-semibold">Confusion matrix pada data uji</caption>
          <thead><tr><th scope="col">Aktual / Prediksi</th><th scope="col">No</th><th scope="col">Yes</th></tr></thead>
          <tbody>
            <tr><th scope="row">No</th><td>TN {matrix.tn}</td><td>FP {matrix.fp}</td></tr>
            <tr><th scope="row">Yes</th><td>FN {matrix.fn}</td><td>TP {matrix.tp}</td></tr>
          </tbody>
        </table>
      </div>
    </section>
    <section className="panel space-y-5">
      <h3 className="text-lg font-semibold">Clustering pelanggan</h3>
      <p className="text-sm text-slate-600">Metrik internal dataset. Skor DBSCAN dihitung pada pelanggan yang mendapat klaster; cakupan dan noise dicantumkan.</p>
      <Comparison title="Perbandingan konfigurasi clustering" rows={clustering.candidates} columns={[
        { key: "Jumlah_Klaster", label: "Klaster" }, { key: "Silhouette", label: "Silhouette" },
        { key: "Davies_Bouldin", label: "Davies–Bouldin" }, { key: "Calinski_Harabasz", label: "Calinski–Harabasz" },
        { key: "Coverage_Pct (%)", label: "Cakupan (%)" }, { key: "Noise_Count", label: "Noise" },
      ]} />
      <PlotChart title="Elbow K-Means" points={clustering.elbow_curve.map(point => ({ x: point.k, y: point.inertia }))}
        xLabel="Jumlah klaster (k)" yLabel="Inertia" connect />
      <div className="overflow-x-auto"><table className="data-table w-full text-sm">
        <caption className="mb-2 text-left font-semibold">Profil segmen terpilih pada dataset</caption>
        <thead><tr>{["Segmen", "Pelanggan", "Tenure (bulan)", `Tagihan (${response.data.currency_unit})`, "Churn historis (%)"].map(label => <th scope="col" key={label}>{label}</th>)}</tr></thead>
        <tbody>{clustering.segment_profiles.map(profile => <tr key={profile.segment_id}>
          <th scope="row">{profile.segment_name}</th><td>{profile.customer_count}</td>
          <td>{metric(profile.tenure_mean)}</td><td>{metric(profile.monthly_charges_mean)}</td><td>{metric(profile.historical_churn_rate_pct)}</td>
        </tr>)}</tbody>
      </table></div>
    </section>
    <section className="panel space-y-5">
      <h3 className="text-lg font-semibold">Regresi tagihan bulanan</h3>
      <Comparison title="Cross-validation data latih · rerata ± simpangan baku" rows={regression.cv_candidates} columns={[
        { key: "MAE_Mean (USD)", label: "MAE (USD)", std: "MAE_Std (USD)" },
        { key: "RMSE_Mean (USD)", label: "RMSE (USD)", std: "RMSE_Std (USD)" },
        { key: "R2_Mean", label: "R²", std: "R2_Std" },
      ]} />
      <h4 className="font-semibold">Data uji · {reg.selected_model}</h4>
      <p className="text-sm text-slate-600">{reg.evaluation_source}</p>
      <dl className="grid grid-cols-3 gap-4">{[
        ["MAE (USD)", reg.mae_usd], ["RMSE (USD)", reg.rmse_usd], ["R²", reg.r2],
      ].map(([label, value]) => <div key={label}><dt className="text-sm text-slate-600">{label}</dt><dd className="text-xl font-bold">{metric(value)}</dd></div>)}</dl>
      <div className="grid gap-4 lg:grid-cols-2">
        <PlotChart title="Aktual versus prediksi · sampel data uji"
          points={reg.actual_vs_predicted_and_residuals_sample.map(point => ({ x: point.actual_monthly_charges, y: point.predicted_monthly_charges }))}
          xLabel="Aktual (USD)" yLabel="Prediksi (USD)" />
        <PlotChart title="Residual · sampel data uji"
          points={reg.actual_vs_predicted_and_residuals_sample.map(point => ({ x: point.predicted_monthly_charges, y: point.residual }))}
          xLabel="Prediksi (USD)" yLabel="Aktual − prediksi (USD)" zeroLine />
      </div>
    </section>
  </div>;
}
