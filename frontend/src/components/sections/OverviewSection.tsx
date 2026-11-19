import type { DatasetSummaryResponse } from "@/types/api";
import StatCard from "@/components/StatCard";

interface OverviewSectionProps {
  summary: DatasetSummaryResponse;
}

export default function OverviewSection({ summary }: OverviewSectionProps) {
  const { data } = summary;
  const churnRatePct = (data.actual_churn.rate * 100).toFixed(1);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-lg font-semibold text-slate-800 mb-1">Overview</h2>
        <p className="text-sm text-slate-500">
          Ringkasan statistik dataset churn pelanggan.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Baris"
          value={data.processed_rows}
          subtitle="Pelanggan diproses"
          accent="default"
        />
        <StatCard
          label="Churn Rate"
          value={`${churnRatePct}%`}
          subtitle="Dari total pelanggan"
          accent="red"
        />
        <StatCard
          label="Churn (Yes)"
          value={data.actual_churn.yes_count}
          subtitle="Pelanggan churn"
          accent="red"
        />
        <StatCard
          label="Churn (No)"
          value={data.actual_churn.no_count}
          subtitle="Pelanggan tidak churn"
          accent="green"
        />
      </div>
    </div>
  );
}
