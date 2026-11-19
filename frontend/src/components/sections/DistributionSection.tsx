import type { DatasetSummaryData } from "@/types/api";
import BarChart from "@/components/BarChart";

interface DistributionSectionProps {
  data: DatasetSummaryData;
}

export default function DistributionSection({
  data,
}: DistributionSectionProps) {
  const { distributions } = data;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-lg font-semibold text-slate-800 mb-1">
          Distribusi Data
        </h2>
        <p className="text-sm text-slate-500">
          Distribusi pelanggan berdasarkan kontrak, masa berlangganan, dan biaya
          bulanan.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <BarChart
          title="Distribusi Kontrak"
          data={distributions.contract}
          color="indigo"
        />
        <BarChart
          title="Distribusi Masa Berlangganan"
          data={distributions.tenure}
          color="blue"
        />
        <BarChart
          title="Distribusi Biaya Bulanan"
          data={distributions.monthly_charges}
          color="violet"
        />
      </div>
    </div>
  );
}
