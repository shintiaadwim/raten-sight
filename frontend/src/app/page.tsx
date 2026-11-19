"use client";

import { useEffect, useState } from "react";
import { loadDashboard, type DashboardLoad } from "@/lib/api";
import OverviewSection from "@/components/sections/OverviewSection";
import DistributionSection from "@/components/sections/DistributionSection";
import PredictionsSection from "@/components/sections/PredictionsSection";
import ModelSection from "@/components/sections/ModelSection";
import EvaluationsSection from "@/components/sections/EvaluationsSection";
import StatusBadge from "@/components/StatusBadge";

const tabs = [
  ["overview", "Beranda"],
  ["distribusi", "Eksplorasi"],
  ["prediksi", "Prediksi & Segmen"],
  ["evaluasi", "Evaluasi Model"],
] as const;
type Tab = typeof tabs[number][0];

export default function DashboardPage() {
  const [tab, setTab] = useState<Tab>("overview");
  const [result, setResult] = useState<DashboardLoad | { status: "loading" }>({ status: "loading" });
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    async function refresh() {
      let delay = 10000;
      try {
        const next = await loadDashboard(controller.signal);
        if (controller.signal.aborted) return;
        setResult(next);
        if (next.status === "preparing") delay = 2000;
      } catch (error) {
        if (controller.signal.aborted) return;
        setResult({ status: "failed", message: error instanceof Error ? error.message : "Dashboard gagal dimuat." });
      }
      if (!controller.signal.aborted) timer = setTimeout(refresh, delay);
    }
    void refresh();
    return () => { controller.abort(); clearTimeout(timer); };
  }, [revision]);

  const snapshot = result.status === "ready" ? result.snapshot : null;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-5 sm:px-6">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-indigo-700">RetenSight</h1>
            <p className="mt-1 text-sm text-slate-600">Analitik pelanggan telekomunikasi</p>
          </div>
          <div className="flex items-center gap-3">
            {result.status !== "loading" && <StatusBadge status={result.status} />}
            <button className="button-secondary" onClick={() => {
              setResult({ status: "loading" });
              setRevision(value => value + 1);
            }}>Muat ulang</button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
        <nav aria-label="Bagian dashboard" className="mb-6 flex gap-1 overflow-x-auto rounded-xl border border-slate-200 bg-white p-1">
          {tabs.map(([id, label]) => (
            <button key={id} aria-pressed={tab === id} onClick={() => setTab(id)}
              className={`min-w-max flex-1 rounded-lg px-4 py-3 text-sm font-semibold ${tab === id ? "bg-indigo-600 text-white" : "text-slate-600 hover:bg-slate-100"}`}>
              {label}
            </button>
          ))}
        </nav>

        {result.status === "loading" && <p className="panel" role="status">Memuat dashboard…</p>}
        {result.status === "preparing" && <p className="panel border-amber-200 bg-amber-50 text-amber-900" role="status">
          {result.message} Tampilan akan diperbarui otomatis.
        </p>}
        {result.status === "failed" && <div className="panel border-red-200 bg-red-50 text-red-800" role="alert">
          <h2 className="font-semibold">Hasil belum dapat ditampilkan</h2>
          <p className="mt-2">{result.message}</p>
          <p className="mt-2 text-sm">Periksa Backend, lalu gunakan Muat ulang.</p>
        </div>}

        {snapshot && <>
          <section className="panel mb-6 space-y-3">
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="font-semibold">{snapshot.summary.dataset_name}</h2>
              {snapshot.summary.is_demo && <span className="rounded bg-amber-100 px-2 py-1 text-sm text-amber-800">Data demo</span>}
            </div>
            <details className="text-sm text-slate-600">
              <summary className="cursor-pointer">Versi analisis</summary>
              <p className="mt-2 break-all">Dataset {snapshot.summary.dataset_version}</p>
              <p className="mt-1 break-all">Model {snapshot.summary.model_version}</p>
            </details>
          </section>
          {tab === "overview" && <>
            <OverviewSection data={snapshot.summary.data} />
            <div className="mt-6 flex flex-wrap gap-3">
              <button className="button-primary" onClick={() => setTab("distribusi")}>Lihat eksplorasi</button>
              <button className="button-secondary" onClick={() => setTab("prediksi")}>Lihat prediksi</button>
            </div>
          </>}
          {tab === "distribusi" && <DistributionSection data={snapshot.summary.data} />}
          {tab === "prediksi" && <>
            <PredictionsSection key={snapshot.summary.model_version + String(snapshot.summary.dataset_version)}
              data={snapshot.predictions.data} models={snapshot.modelInfo.data} />
            <details className="panel mt-6">
              <summary className="cursor-pointer font-semibold">Informasi model yang digunakan</summary>
              <div className="mt-4"><ModelSection data={snapshot.modelInfo.data} /></div>
            </details>
          </>}
          {tab === "evaluasi" && <EvaluationsSection response={snapshot.evaluations} />}
        </>}
      </main>
      <footer className="mx-auto max-w-7xl px-6 py-8 text-sm text-slate-500">IBM Telco Customer Churn · Analisis dataset historis</footer>
    </div>
  );
}
