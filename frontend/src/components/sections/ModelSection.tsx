import type { ModelInfoData } from "@/types/api";
import ModelInfoCard from "@/components/ModelInfoCard";

interface ModelSectionProps {
  data: ModelInfoData;
}

export default function ModelSection({ data }: ModelSectionProps) {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-lg font-semibold text-slate-800 mb-1">
          Informasi Model
        </h2>
        <p className="text-sm text-slate-500">
          Detail algoritma dan konfigurasi model machine learning yang digunakan.
        </p>
      </div>
      <ModelInfoCard data={data} />
    </div>
  );
}
