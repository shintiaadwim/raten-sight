"use client";

import { useState, useEffect } from "react";
import type {
  DatasetSummaryResponse,
  PredictionsResponse,
  ModelInfoResponse,
} from "@/types/api";
import {
  fetchDatasetSummary,
  fetchPredictions,
  fetchModelInfo,
} from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";
import OverviewSection from "@/components/sections/OverviewSection";
import DistributionSection from "@/components/sections/DistributionSection";
import PredictionsSection from "@/components/sections/PredictionsSection";
import ModelSection from "@/components/sections/ModelSection";

type Tab = "overview" | "distribusi" | "prediksi" | "model";

const TABS: { id: Tab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "distribusi", label: "Distribusi" },
  { id: "prediksi", label: "Prediksi" },
  { id: "model", label: "Model Info" },
];

interface DashboardState {
  summary: DatasetSummaryResponse | null;
  predictions: PredictionsResponse | null;
  modelInfo: ModelInfoResponse | null;
  loading: boolean;
  error: string | null;
}

function LoadingSpinner({ message }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-4">
      <div className="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
      <p className="text-slate-500 text-sm">{message ?? "Memuat data..."}</p>
    </div>
  );
}

function ErrorCard({ message }: { message: string }) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-xl p-6 my-6">
      <div className="flex items-start gap-3">
        <span className="text-red-500 text-xl">⚠️</span>
        <div>
          <p className="text-red-800 font-semibold mb-1">Terjadi Kesalahan</p>
          <p className="text-red-600 text-sm">{message}</p>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [state, setState] = useState<DashboardState>({
    summary: null,
    predictions: null,
    modelInfo: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    async function loadData() {
      setState((prev) => ({ ...prev, loading: true, error: null }));
      try {
        const [summary, predictions, modelInfo] = await Promise.all([
          fetchDatasetSummary(),
          fetchPredictions(),
          fetchModelInfo(),
        ]);
        setState({
          summary,
          predictions,
          modelInfo,
          loading: false,
          error: null,
        });
      } catch (err) {
        setState((prev) => ({
          ...prev,
          loading: false,
          error:
            err instanceof Error
              ? err.message
              : "Gagal terhubung ke backend. Pastikan server berjalan di http://localhost:8000",
        }));
      }
    }

    void loadData();
  }, []);

  const { summary, predictions, modelInfo, loading, error } = state;
  const isDemo = summary?.is_demo;
  const status = summary?.status ?? modelInfo?.status ?? "preparing";

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">R</span>
              </div>
              <div>
                <h1 className="text-lg font-bold text-slate-900">RetenSight</h1>
                <p className="text-xs text-slate-400 leading-none">
                  Dashboard Analitik Churn Pelanggan
                </p>
              </div>
            </div>
            {!loading && !error && (
              <StatusBadge status={status} />
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Loading state */}
        {loading && <LoadingSpinner message="Memuat data dashboard..." />}

        {/* Error state */}
        {!loading && error && <ErrorCard message={error} />}

        {/* Content */}
        {!loading && !error && summary && predictions && modelInfo && (
          <>
            {/* Status Banner */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 mb-6">
              <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
                {isDemo && (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-amber-100 text-amber-700 border border-amber-200 rounded-full text-xs font-semibold">
                    🧪 Demo Mode
                  </span>
                )}
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400">Status:</span>
                  <StatusBadge status={summary.status} />
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400">Dataset:</span>
                  <span className="text-xs font-medium text-slate-700">
                    {summary.dataset_name}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400">Versi Dataset:</span>
                  <span className="text-xs font-mono text-slate-600">
                    {summary.dataset_version}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400">Versi Model:</span>
                  <span className="text-xs font-mono text-slate-600">
                    {summary.model_version}
                  </span>
                </div>
              </div>

              {/* Preparing state */}
              {summary.status === "preparing" && (
                <div className="mt-4 flex items-center gap-3 text-yellow-700">
                  <div className="w-5 h-5 border-2 border-yellow-400 border-t-yellow-700 rounded-full animate-spin flex-shrink-0" />
                  <span className="text-sm font-medium">Memproses data...</span>
                </div>
              )}

              {/* Failed state */}
              {summary.status === "failed" && summary.error && (
                <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
                  <p className="text-xs font-semibold text-red-700 mb-1">
                    Detail Error
                  </p>
                  <p className="text-xs text-red-600">{summary.error}</p>
                </div>
              )}
            </div>

            {/* Tabs Navigation */}
            <div className="flex gap-1 bg-white border border-slate-200 rounded-xl p-1 mb-6 shadow-sm overflow-x-auto">
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex-1 min-w-max px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    activeTab === tab.id
                      ? "bg-indigo-600 text-white shadow-sm"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div>
              {activeTab === "overview" && (
                <OverviewSection summary={summary} />
              )}
              {activeTab === "distribusi" && (
                <DistributionSection summary={summary} />
              )}
              {activeTab === "prediksi" && (
                <PredictionsSection predictions={predictions} />
              )}
              {activeTab === "model" && (
                <ModelSection modelInfo={modelInfo} />
              )}
            </div>
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-16 border-t border-slate-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-xs text-slate-400">
            RetenSight · IBM Telco Customer Churn Analytics Dashboard
          </p>
        </div>
      </footer>
    </div>
  );
}
