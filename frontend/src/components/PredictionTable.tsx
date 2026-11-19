"use client";

import { useState } from "react";
import type { Prediction } from "@/types/api";

export default function PredictionTable({ predictions, unit }: { predictions: Prediction[]; unit: string }) {
  const [page, setPage] = useState(0);
  const pageSize = 25;
  const pageCount = Math.ceil(predictions.length / pageSize);
  if (!predictions.length) return <p className="panel">Belum ada hasil prediksi pelanggan.</p>;

  return (
    <section className="panel space-y-4">
      <div className="overflow-x-auto" tabIndex={0} aria-label="Tabel prediksi pelanggan">
        <table className="data-table w-full text-sm">
          <caption className="sr-only">Hasil model dan simulasi rekomendasi per pelanggan</caption>
          <thead><tr>
            {["ID pelanggan", "Probabilitas churn", "Prediksi churn", "Segmen", `Estimasi tagihan (${unit})`, "Simulasi rekomendasi"].map(label => (
              <th scope="col" key={label}>{label}</th>
            ))}
          </tr></thead>
          <tbody>{predictions.slice(page * pageSize, (page + 1) * pageSize).map(row => (
            <tr key={row.customer_id}>
              <td className="font-mono">{row.customer_id}</td>
              <td>{row.churn_probability === null ? "—" : `${(row.churn_probability * 100).toFixed(1)}%`}</td>
              <td className={row.churn_prediction === "Yes" ? "font-semibold text-red-700" : "text-slate-700"}>{row.churn_prediction ?? "—"}</td>
              <td>{row.segment_name ?? "Belum tersedia"}</td>
              <td>{row.predicted_monthly_charges === null ? "—" : row.predicted_monthly_charges.toFixed(2)}</td>
              <td className="min-w-64 max-w-md">{row.recommendation ?? "Data untuk rekomendasi belum lengkap."}</td>
            </tr>
          ))}</tbody>
        </table>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
        <p>{page * pageSize + 1}–{Math.min((page + 1) * pageSize, predictions.length)} dari {predictions.length} pelanggan</p>
        <div className="flex items-center gap-3">
          <button className="button-secondary" disabled={page === 0} onClick={() => setPage(value => value - 1)}>Sebelumnya</button>
          <span aria-live="polite">Halaman {page + 1} / {pageCount}</span>
          <button className="button-secondary" disabled={page + 1 >= pageCount} onClick={() => setPage(value => value + 1)}>Selanjutnya</button>
        </div>
      </div>
    </section>
  );
}
