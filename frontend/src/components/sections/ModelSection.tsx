import type { ModelInfoResponse } from "@/types/api";
import ModelInfoCard from "@/components/ModelInfoCard";

interface ModelSectionProps {
  modelInfo: ModelInfoResponse;
}

export default function ModelSection({ modelInfo }: ModelSectionProps) {
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
      <ModelInfoCard data={modelInfo.data} />
    </div>
  );
}
